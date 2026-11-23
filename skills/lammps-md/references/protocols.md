# MD 协议

## 1. `real` 与 `metal` 单位制对照

从文献、VASP/ASE 或机器学习势迁移参数到 LAMMPS 时，务必逐项核对以下单位：

| 物理量 | `units real`（常见古典力场） | `units metal`（常见 EAM / MLP） |
|---|---|---|
| 长度 | Å | Å |
| 时间 | fs（常用 `timestep 1.0`） | ps（`1 fs` 需写 `timestep 0.001`） |
| 能量 | kcal/mol | eV（$1\,\text{eV} = 23.0605\,\text{kcal/mol}$） |
| 质量 | g/mol | g/mol |
| 压力 | atm | bar（$1\,\text{atm} = 1.01325\,\text{bar}$） |
| 电荷 | $e$ | $e$ |
| 热浴阻尼 `Tdamp` | 常见 `100.0`（100 fs） | 常见 `0.1`（0.1 ps） |

> **谐振势系数陷阱**：AMBER/CHARMM/OPLS 参数表通常定义 $E = \frac{1}{2}k(r - r_0)^2$，而 LAMMPS `bond_style harmonic` / `angle_style harmonic` 定义为 $E = K(r - r_0)^2$（**不含 $1/2$**），导入时应取 $K = k/2$。

## 2. 界面/电解液模拟输入骨架（`units real`）

```lammps
units           real
atom_style      full
boundary        p p f

pair_style      lj/cut/coul/long 12.0 12.0
pair_modify     mix arithmetic tail no
kspace_style    pppm 1.0e-4
kspace_modify   slab 3.0

bond_style      harmonic
angle_style     harmonic
special_bonds   amber

read_data       system.data

# 分组定义（根据当前 data 文件 type_id 填写）
group           slab type 1
group           water type 2 3

# 1. 固定基底并最小化液相
fix             freeze slab setforce 0.0 0.0 0.0
minimize        1.0e-4 1.0e-6 1000 10000
reset_timestep  0

# 2. 刚性水约束（在 minimize 之后开启）与 NVT 平衡
fix             water_shake water shake 1.0e-4 20 0 b 1 a 1
velocity        water create 300.0 48271 dist gaussian
fix             thermo_nvt water nvt temp 300.0 300.0 100.0

thermo          500
thermo_style    custom step temp pe ke etotal press vol
dump            traj all custom 1000 eq.lammpstrj id type element xu yu zu
dump_modify     traj element Pt O H sort id

timestep        1.0
run             100000
write_restart   eq.restart
```

- **元素符号输出**：`dump_modify ... element ...` 的列表顺序必须严格对应 `type 1, 2, 3...`，否则下游 ASE/OVITO 读取时会把元素认错。

## 3. 恒电势电极（ELECTRODE）检查要点

- 使用 `fix electrode/conp`（常电势）或 `fix electrode/thermo` 时：
  1. `kspace_style` 必须使用电极包配套求解器（如 `pppm/electrode` 或 `ewald/electrode`），否则运行会直接报错。
  2. 明确电极组（`group elec1`, `group elec2`）与电势差还是单电极绝对电势参数，记录单位（在 `units real` 中电极电势单位通常为 Volt，具体以当前 LAMMPS 版本 `fix electrode/conp` 文档为准）。
  3. 仅编译了 `GPU` 或 `KOKKOS` 包不代表 `electrode` 求解器有 GPU 内核；在计算节点运行小步长测试后，查看日志确认实际运行的加速路径和性能，不要盲目加卡。

## 4. 平衡检验与体相密度统计

- **NPT 平衡与真空界面的区分**：三维体相溶液可用 `fix npt` 调节密度；含真空层的二维 slab 不可直接开启 z 方向压控，应通过固定液膜厚度或先做三维 NPT 溶液盒预平衡再拼装表面，并在生产阶段统计**远离双电层界面的体相窗口**平均密度来核对水模型密度，切勿把界面吸附第一峰当成体相密度。
- **Restart 续算与硬件确定性检查**：
  - 正常完成以 `log.lammps` 出现 `Total wall time` 且达到目标 `Step`、无 `ERROR`/`Lost atoms` 为准；新目录续算使用 `read_restart` 配合 `run <S_target> upto` 并重新定义 `fix shake`、`fix nvt`/`npt`、`fix setforce`、`fix electrode/*` 及 `dump`。
  - 若使用 `write_restart` 续算，确认日志文件开头打印的 `Step` 延续前段末步；若使用 `write_data`，注意其不保存 `fix` 历史状态，但会保存速度和 `Image flags`（除非显式清空）。
  - 仅改变 MPI ranks 或 GPU 数时，浮点求和顺序差异会导致单条 MD 轨迹在数十至数百步后分叉，属正常数值行为，但稳态热力学均值应一致。
