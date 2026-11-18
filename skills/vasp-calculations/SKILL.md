---
name: vasp-calculations
description: "Prepare VASP geometry optimizations, single-point calculations and AIMD with explicit scientific parameters, POTCAR/KPOINTS checks and compatible restart inputs. Use for VASP input generation and sanity verification; installation and queue management belong to separate skills."
---
# VASP 计算准备

为单点计算、几何优化、AIMD 及约束动力学准备结构、输入文件与重启配置，确保 `POSCAR`、`POTCAR`、`INCAR`、`KPOINTS` 与当前 VASP 二进制版本及科学协议一致。

## 开始前确认

- **任务模式**：单点（`SP`）、离子弛豫（`GEO_OPT`）、晶胞弛豫（`CELL_OPT`）、`AIMD` 或约束动力学。
- **电子协议**：泛函（如 PBE/RPBE/HSE06）、色散修正（`IVDW`）、赝势变体（如 `PAW_PBE` 及其 `_pv`/`_sv`/`_h` 后缀）、`ENCUT`、`EDIFF`、`ISPIN`、`NELECT`（是否带电）。
- **体系与边界**：块体、分子还是表面 slab（真空方向、是否开启偶极修正 `LDIPOL`/`IDIPOL`、是否含隐式溶剂如 VASPsol）。
- **运行资源**：目标二进制（`vasp_std` / `vasp_gam` / `vasp_ncl`）、MPI ranks、GPU 数量与集群推荐并行参数（`KPAR`、`NCORE`）。

## 工作流程

### 1. 核对 `POSCAR` 与组装 `POTCAR`

- 检查 `POSCAR` 元素行、原子计数总和、坐标格式（`Direct` vs `Cartesian`）及 `Selective dynamics`（`T/F` 标记）。
- 若直接从 ASE 导出 `POSCAR`，确认相同元素未被拆成多段或重排，导致与预期 `POTCAR` 顺序错位。
- 按 `POSCAR` 第 6 行物种顺序拼接 `POTCAR`（仅在计算目录组装本地可用的赝势，严禁将版权赝势内容写入可分享技能仓库），并立即校验：

```bash
# 核对 POSCAR 物种顺序与 POTCAR TITEL 是否一一对应
sed -n '6,7p' POSCAR
grep -E "TITEL|ENMAX|ZVAL" POTCAR
```

### 2. 配置 `KPOINTS`

- 表面 slab 和孤立分子/团簇在非周期方向 k 点数必须为 `1`（例如 `Nx × Ny × 1` 或纯 Gamma `1 1 1`），优先采用 `Gamma`-centered 网格（六方/表面体系尤其避免用 `Monkhorst-Pack` 破坏对称性）。
- 仅当计算是 `1 1 1` 单点且无特殊相位需求时，才使用编译版 `vasp_gam`（`Gamma-only`）以加速。
- `KPOINTS` 写明网格来源或 k-spacing 定义（详见 [输入与运行适配](references/inputs-runtime.md)）。

### 3. 按模式编写 `INCAR`

将科学参数与并行控制参数分块写入 `INCAR`，不同任务模式的常用模板与关键区别见 [计算模式](references/modes.md)：

- **展宽（`ISMEAR` / `SIGMA`）**：
  - 金属块体/表面优化与能量：可用 `ISMEAR = 1` 或 `2`（`SIGMA = 0.1–0.2`），最后高精度单点/DOS 可切至 `ISMEAR = -5`（需 k 网格 $\ge 4$ 点且仅用于静态单点）。
  - 分子、半导体、绝缘体或气相参考物种：**必须用 `ISMEAR = 0`（Gaussian）** 且较小 `SIGMA = 0.02–0.05`，避免分数占据误差。
- **实空间投影（`LREAL`）**：小体系（< ~20 原子）与高精度能量对比用 `LREAL = .FALSE.`；大超胞界面或 AIMD 可用 `LREAL = Auto`（需在同一批对比计算中保持一致）。
- **净电荷与电化学**：设置 `NELECT` 时需由中性体系价电子总数 `sum(N_i * ZVAL_i)` 加减净电荷（多电子为正加、少电子为负减），并明确背景补偿电荷或隐式溶剂定义。

### 4. 设置并行与重启兼容

- **并行参数**：`KPAR` 必须能整除 MPI 总进程数及不可约 k 点数；CPU 运行常设 `NCORE`（如单节点核心数的因子），GPU（OpenACC）版本按当前集群已验证配方设置（通常不设或按 GPU 数调优）。
- **重启控制**：
  - 几何续算：复制完整 `CONTCAR` 为新目录的 `POSCAR`（先检查非空、原子数与 `Selective dynamics` 未丢）。
  - 电子续算：`ISTART = 1` 读 `WAVECAR`，`ICHARG = 1` 读 `CHGCAR`；仅当原子数、晶胞体积（截断能对应平面波基组）、k 点网格、旋量/共线（`ISPIN`/`LNONCOLLINEAR`）一致时才可复用，否则设为 `ISTART = 0` 重新初始化。

### 5. 静态检查与结果验收

提交前检查：
```bash
# 确认 4 个必需输入齐备且 POSCAR 原子总数与坐标行数匹配
ls -l INCAR POSCAR POTCAR KPOINTS
python3 -c '
from ase.io import read
a = read("POSCAR")
print("natoms:", len(a), "formula:", a.get_chemical_formula(), "pbc:", a.pbc)
'
```
运行后验收必须分别核对：
1. 正常结束标记：`grep -q "General timing" OUTCAR`；
2. 电子步是否真正收敛（不能只看任务退出码为 0）：检查每离子步电子迭代次数是否触及 `NELM` 上限；
3. 离子优化/MD 是否达到目标判据（自由原子最大力 vs `|EDIFFG|`，或实际完成的 `NSW` 步数）。

## 按需参考

- 单点、优化、AIMD 与约束动力学的参数模板及能量读取口径：阅读 [计算模式](references/modes.md)。
- `POTCAR`、k 点 spacing 约定、`GPU/MPI` 适配与重启边界：阅读 [输入与运行适配](references/inputs-runtime.md)。

## 交付产物与验收

- 独立计算目录内的 `POSCAR`、`INCAR`、`KPOINTS`、本地组装 `POTCAR`、作业脚本及 `protocol_notes.md`。
- 新协议或重启任务使用新目录，不直接覆盖原始运行输入和日志。
