---
name: lammps-md
description: "Prepare LAMMPS classical MD and electrode simulations, including data/topology checks, unit conversions, equilibration/production stages, independent replicas and restart continuations."
---
# LAMMPS 模拟准备

准备拓扑、单位制、边界条件和阶段协议一致的 LAMMPS 经典分子动力学输入，支持多独立重复（replicas）、二进制重启以及恒电势/固定电荷电极模拟。

## 开始前确认

- **单位与原子风格**：`units`（`real` / `metal` / `lj`）与 `atom_style`（`full` / `charge` / `atomic`）。
- **拓扑与势函数**：`data` 或 `restart` 文件路径、元素到 `atom type` 的显式映射、所需 `pair_style` / `bond_style` / `angle_style` / `kspace_style` 与 `special_bonds`（如 AMBER / CHARMM / OPLS）。
- **模拟阶段**：最小化（`minimize`）、升温/NPT 密度平衡、NVT 预平衡、生产采样与 `dump` 输出项。
- **电极设置**（如适用）：固定电荷（fixed-charge）、固定总电荷还是恒电势（如 `ELECTRODE` 包的 `fix electrode/conp`），以及电压设定与参考方式。
- **软件构建**：当前可用的 LAMMPS 可执行文件及其已编译的 package/style（CPU / GPU / Kokkos）。

## 工作流程

### 1. 检查 LAMMPS 编译能力与拓扑映射

先只读核对二进制实际支持哪些包与加速后端，不要假设所有风格默认可用：

```bash
lmp -h | grep -A 30 "Installed packages"
```

核对 `data` 文件头部与 `Masses` 段，建立 `type_id -> element -> role` 映射（例如 `type 1 = Pt`, `type 2 = Ow`, `type 3 = Hw`），确认 `data` 文件中实际含有的 `bonds`/`angles`/`dihedrals`/`impropers` 与输入脚本声明的势函数风格一致。

### 2. 核对单位制、力场组合与长程静电

- **严防单位混用**：导入参数时按当前 `units` 转换时间步、能量、电荷和弹簧常数（详见 [MD 协议](references/protocols.md) 单位对照表）。例如 `1.0 fs` 在 `units real` 中写作 `timestep 1.0`，在 `units metal` 中必须写作 `timestep 0.001`。
- **混合势与 1–4 规则**：使用 `pair_style hybrid` 或 `hybrid/overlay` 时，必须逐对检查交叉项 `pair_coeff i j` 是否全部显式给出或正确使用混合规则（`geometric` vs `arithmetic`）；按力场家族设置 `special_bonds`（如 `amber`、`charmm` 或 `lj/coul 0.0 0.0 0.5`）。
- **二维界面静电**：含真空或双电层界面时，采用 `boundary p p f` 配合 `kspace_style pppm 1.0e-4` 与 `kspace_modify slab 3.0`（或与电极求解器兼容的 `pppm/electrode`），不要用三维周期长程静电直接算无保护间隔的非对称界面。

### 3. 设计最小化、平衡与生产阶段

- **刚性水与约束**：刚性水模型（如 SPC/E、TIP3P）应使用 `fix shake`（仅用于支持 `rattle/shake` 的时间积分器，且需放在 `minimize` 之后、动力学之前；若必须最小化刚性水，先使用软弹簧或独立解除约束）。
- **受控比较与独立重复**：
  - 比较不同条件时保留相同的初始拓扑来源、势函数和截断参数，仅改变声明变量。
  - 生成多条独立 `replica` 时，显式记录各自的 `velocity all create <T> <seed>` 随机种子或互不重叠的独立初态来源，不要将同一条轨迹相邻帧当成独立重复。

### 4. 配置电极与恒电势协议（若适用）

- 明确区分三类常见模型，不可混为一谈：
  1. **固定原子电荷**：电极原子保持静态偏电荷（常为 0）。
  2. **零总电荷导体（Q=0）**：电荷可极化分布，总电极净电荷约束为 0。
  3. **恒定外加电势 / 电势差**：使用 `ELECTRODE` 包（如 `fix electrode/conp`、`fix electrode/thermo`）固定电极电势或两极电势差，需确认当前二进制已启用 `ELECTRODE` 及对应 `kspace_style`（如 `pppm/electrode`）。

### 5. 准备重启（Restart）、完成验收与输出验证

- **科学完成与数值健康验收**：确认 `log.lammps` 末尾出现 `Total wall time`、最后输出 `Step` 达到目标步数且无 `ERROR` / `Lost atoms`；联合检查整段温度、势能/总能及关键键长，若崩溃前已出现原子飞散或数值畸变，须回退到崩溃前的健康二进制 `restart` 续算，不强行接续失真末帧。
- **区分 `read_restart` 与 `read_data`**：需要完整保留速度和部分 `fix` 内部状态时用二进制 `restart`；跨大版本或更换非兼容 `fix` 时改用 `write_data`/`read_data` 并明确标为重新初始化动力学状态。
- **`read_restart` 重声明与续算步数**：重读后须重新声明所有非持久化的 `fix`、`pair_style`（视风格而定）和 `dump`，在独立新目录续算并用 `run <S_target> upto` 避免手算剩余步数出错。
- **0 步静态试跑**：先执行 `0` 步试运行检查语法、初始力/能量是否有限以及 `kspace`/GPU 路径是否真正启用：

```bash
lmp -in input.lammps -log check.log   # 临时测试脚本中设 run 0
```

## 按需参考

- `real`/`metal` 单位换算、标准输入骨架、电极求解器兼容表与恢复检查：阅读 [MD 协议](references/protocols.md)。

## 交付产物与验收

1. `input.lammps`（及分阶段脚本 `01_min.lmp` / `02_eq.lmp` / `03_prod.lmp`）、`data` 文件与类型映射 `type_map.json`。
2. `replicas.csv`（记录每个重复的 `replica_id`、初态来源、随机种子与目标时长）。
3. 验收标准：试跑无 `ERROR`/缺失系数，温度/总能/体相密度在平衡阶段稳定在目标窗口，且 `dump` 文件包含预期的 `id type x y z`（或未包裹坐标 `xu yu zu`）字段。
