# PLUMED 与 OPES

## 1. 单位声明与 OPES 输入模板

```text
# 务必首行显式指定单位，与 ASE/VASP/LAMMPS metal 对齐
UNITS LENGTH=A ENERGY=eV TIME=ps

# 1-based 原子索引与 PBC 行为（NOPBC 仅在确认不会跨盒断裂时使用）
d: DISTANCE ATOMS=12,45
coord: COORDINATION GROUPA=12 GROUPB=45-60 R_0=1.35 NN=6 MM=12

opes: OPES_METAD ...
  ARG=d
  PACE=100
  BARRIER=0.50       # 单位 eV (相当于 ~48 kJ/mol)，按实际预期能垒调整
  TEMP=300
  FILE=KERNELS
  STATE_WFILE=STATE
  STATE_WSTRIDE=1000
...

# 限制壁（防止脱附跑飞；不同于 EXCLUDED_REGION）
uwall: UPPER_WALLS ARG=d AT=6.0 KAPPA=20.0 EXP=2

PRINT ARG=d,coord,opes.bias,uwall.bias STRIDE=10 FILE=COLVAR
```

- **`OPES_METAD` 常见语义陷阱**：
  - `BARRIER` 单位随 `UNITS ENERGY=...` 改变！若误把 kJ/mol 的数值 `50` 当成 eV 填入，会导致偏置强度荒谬放大近 100 倍。
  - `EXCLUDED_REGION` 只控制不往某个高能区沉积核，**不会把系统推回感兴趣区域**；需要防止构型飘远须使用 `UPPER_WALLS` / `LOWER_WALLS`。
  - 续算时需加 `RESTART=YES` 及 `STATE_RFILE=STATE`（并确认 `STATE` 与 MD 重启文件处于同一时间步）；若重启后切换了 CV 定义或温度，应明确开始全新偏置或查阅当前 PLUMED 版本的重读限制。

## 2. ASE `Plumed` 与自定义 `LOAD` 接口注意

- **ASE `Plumed` 多行块问题**：ASE 的 `ase.calculators.plumed.Plumed(atoms, input=lines, timestep=...)` 传入字符串列表时，某些版本会按行直接送入 PLUMED，不支持把多行 `...` 块拆开或含特定注释方式，或对不同版本有换行解析差异。在 ASE 环境下使用多行动作时，建议将每个动作整理为单行命令（去掉 `...` 续行符）并在测试目录实际初始化跑 2 步核对 `COLVAR`。
- **自定义库路径**：若 `plumed.dat` 中使用 `LOAD FILE=./CustomAction.cpp`，相对路径是相对于**实际启动 MD 进程的工作目录**，测试和生产脚本需保持一致。

## 3. `plumed driver` 快速校验命令

```bash
# 1. 检查当前 PLUMED 版本与内置/已加载动作
plumed info --version

# 2. 对现有轨迹或测试构型做干跑检查（查看 COLVAR 输出范围是否合理）
plumed driver --plumed plumed.dat --mf_extxyz test_init.extxyz --timestep 0.001 --length-units A
head -n 10 COLVAR
```

- 短程 MD 验收重点：`COLVAR` 第一帧数值与手工几何计算完全一致；偏置力施加后，前 10 步能量/温度/原子速度有限且无突然爆炸。
