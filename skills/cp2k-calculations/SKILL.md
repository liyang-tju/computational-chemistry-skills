---
name: cp2k-calculations
description: "Prepare CP2K Quickstep inputs for ENERGY_FORCE, GEO_OPT, CELL_OPT and NVT/NPT AIMD, including Poisson periodicity, OT/diagonalization SCF and EXT_RESTART continuations."
---
# CP2K 计算准备

准备可运行的 CP2K Quickstep 输入（单点 `ENERGY_FORCE`、优化 `GEO_OPT`/`CELL_OPT`、分子动力学 `MD`），确保基组/赝势文件、网格精度、周期性 Poisson 求解、SCF 策略与重启边界清晰一致。

## 开始前确认

- **任务类型**：`RUN_TYPE`（`ENERGY_FORCE` / `GEO_OPT` / `CELL_OPT` / `MD`）。
- **体系与电子态**：原子结构（XYZ/CIF）、晶胞参数 `ABC`/`ALPHA_BETA_GAMMA`、净电荷 `CHARGE`、自旋多重度 `MULTIPLICITY` 与是否开启非限制自旋 `UKS`。
- **边界条件**：三维周期体相/溶液（`PERIODIC XYZ`）、二维 slab（`PERIODIC XY` + Poisson 求解器）还是孤立分子（`PERIODIC NONE`）。
- **计算环境**：可用 CP2K 可执行文件（如 `cp2k.psmp` / `cp2k.ssmp`）、`CP2K_DATA_DIR` 或本地基组/赝势文件（如 `BASIS_MOLOPT`、`GTH_POTENTIALS`、`dftd3.dat`）的真实位置。

## 工作流程

### 1. 探测软件与数据文件

先只读确认目标 CP2K 版本及数据文件路径（由运行配置或当前环境 `CP2K_DATA_DIR` 获取，不向可分享技能写入特定主机路径）：

```bash
command -v cp2k.psmp cp2k.ssmp || true
cp2k.psmp --version | head -n 5
```

确保 `&DFT` 中引用的 `BASIS_SET_FILE_NAME`、`POTENTIAL_FILE_NAME`、`PARAMETER_FILE_NAME`（如 DFT-D3）在运行目录下真实可读。

### 2. 配置 `&DFT` 与 `&SUBSYS`

- **每个 `&KIND` 逐一核对**：确保结构中出现的每个元素或自定义原子种类都有对应的 `&KIND`，其 `BASIS_SET`（如 `DZVP-MOLOPT-SR-GTH`）和 `POTENTIAL`（如 `GTH-PBE-q6`）确实存在于所引用的数据文件中，价电子数与期望电荷一致。
- **网格与精度（`&MGRID` / `&QS`）**：明确 `CUTOFF`（如 400–600 Ry，取决于最硬赝势）、`REL_CUTOFF`（常取 50–60 Ry）和 `EPS_DEFAULT`（如 `1.0E-12`）。
- **周期性与 Poisson 求解器**：`&SUBSYS/&CELL` 与 `&DFT/&POISSON` 的 `PERIODIC` 必须一致，不能只改 `CELL` 尺寸而不改 Poisson 设置：
  - 三维体系：`PERIODIC XYZ`，默认周期 Poisson。
  - 二维 slab：`&CELL PERIODIC XY` + `&POISSON PERIODIC XY` + `POISSON_SOLVER ANALYTIC`（或 `MT` / `WAVELET`，注意 `WAVELET` 对居中和盒子尺寸有严格要求；非对称 slab 可评估 `SURFACE_DIPOLE_CORRECTION`）。
  - 孤立分子：`PERIODIC NONE` + `POISSON_SOLVER MT` 或 `WAVELET`。

### 3. 选择 SCF 求解策略（`&SCF`）

- **绝缘体/液相/带隙体系**：优先使用 **OT**（`&OT ON` + `MINIMIZER DIIS`/`CG` + `PRECONDITIONER FULL_SINGLE_INVERSE`）配合 `&OUTER_SCF`（`EPS_SCF 1.0E-6`），速度快且内存友好；OT **不能**与分数占据（`&SMEAR`）同时开启。
- **金属或小带隙体系**：关闭 OT，改用常规对角化 `&DIAGONALIZATION` + `&MIXING`（如 `BROYDEN_MIXING`）+ `&SMEAR`（`METHOD FERMI_DIRAC`，`ELECTRONIC_TEMP [K] 300`），并配合足够数量的 `ADDED_MOS`。

### 4. 配置 `&MOTION` 与重启（`&EXT_RESTART`）

- 在 `&MD` 中显式写明 `ENSEMBLE`、`STEPS`、`TIMESTEP [fs]`、`TEMPERATURE [K]` 及 `&THERMOSTAT`（如 `TYPE CSVR`, `TIMECON [fs] 50`）。
- 续算或温度/系综切换时，按 [动力学与重启](references/md-restart.md) 显式控制 `&EXT_RESTART` 中的 `RESTART_POS`、`RESTART_VEL`、`RESTART_CELL`、`RESTART_THERMOSTAT` 与 `RESTART_COUNTERS`，确保步数、时间起点与波函数初猜（`SCF_GUESS RESTART`）匹配。

### 5. 输出对齐与输入静态校验

- 统一配置 `&PRINT` 输出频率（`&TRAJECTORY`, `&VELOCITIES`, `&CELL`, `&RESTART`），确保轨迹、晶胞和能量都能通过 `Step`/`Time` 对齐。
- 提交或运行前用 CP2K 内置检查命令验证输入语法与依赖读取：

```bash
cp2k.psmp -c input.inp
```

## 按需参考

- `MD` 模板、OT/对角化示例、`&EXT_RESTART` 语义与步号时间对齐检查：阅读 [动力学与重启](references/md-restart.md)。

## 交付产物与验收

1. 独立运行目录内的 `input.inp`（及被 `@INCLUDE` 引用的子文件）、初始结构与作业脚本。
2. 静态语法检查 `cp2k.psmp -c input.inp` 无报错。
3. 运行后验收：日志出现正常结束标记（`PROGRAM ENDED AT`）、SCF 在 `MAX_SCF` 内收敛，且目标步数/优化判据达成。
