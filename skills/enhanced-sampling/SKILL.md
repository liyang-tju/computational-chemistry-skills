---
name: enhanced-sampling
description: "End-to-end enhanced sampling and free energy workflow: design CVs and run inputs (VASP ICONST/Blue Moon/slow-growth/harmonic umbrella/MDALGO metadynamics, and PLUMED RESTRAINT/METAD/WT-Metadynamics/OPES_METAD/OPES_METAD_EXPLORE with ASE/CP2K/LAMMPS/i-PI), verify derivatives and bias convergence, and reconstruct PMFs with Blue Moon metric correction, WHAM, MBAR (pymbar), or c(t)/opes.bias reweighting and block error bars."
---
# 增强采样与自由能分析

覆盖增强采样的完整生命周期：**CV 设计与物理选型 $\rightarrow$ VASP / PLUMED / ASE / MD 输入构建与离线校验 $\rightarrow$ 采样充分性/滞后诊断 $\rightarrow$ PMF（自由能面）重建与误差分析**。（静态零点能/熵与计算氢电极台阶图属于 `$che-calculation`。）

## 开始前确认

1. **物理坐标与维度**：反应物/产物基态构型、原子编号约定（VASP `ICONST` 与 PLUMED 均为 **1-based**；ASE 为 **0-based**）、周期边界跨界情况，以及拟用 CV 是否足以区分中间态与副反应。
2. **方法与模拟引擎**：目标方法（Slow-growth / Blue Moon Constrained AIMD / Umbrella Sampling / Metadynamics / WT-Metadynamics / `OPES_METAD` / `OPES_METAD_EXPLORE`）与引擎（原生 VASP、CP2K、LAMMPS、ASE + MLP 或 i-PI）。
3. **可用输出与统计量**：待分析时核对输入文件格式（VASP `REPORT` / `HILLSPOT`、CP2K `.lagrange_mult`、PLUMED `COLVAR` / `HILLS` / `KERNELS` / `OPES_STATE`）、温度 $T$ 与目标能量单位（`eV` vs `kJ/mol`）。

## 方法选型矩阵

| 方法 | VASP 原生 | PLUMED | 适用场景 | 核心配置关键词 | 自由能重建 |
|---|---|---|---|---|---|
| **Slow-growth AIMD** | 是 (`-Dtbdyn`) | via i-PI / SMD | 已知 1D 路径快速扫描（需警惕滞后） | `ICONST status=0`, `LBLUEOUT`, `INCREM` | `REPORT` 梯度梯形积分（含去重） |
| **Constrained AIMD (Blue Moon)** | 是 (`-Dtbdyn`) | via CP2K / i-PI | 沿已知 1D CV 的高精度 AIMD 能垒 | `ICONST status=0`, `LBLUEOUT=.TRUE.` | 度量修正 $Z^{-1/2}(-\lambda+k_BTG)$ 积分 |
| **Umbrella Sampling** | 是 (`status=8`) | `RESTRAINT` | 高能垒/明确反应坐标、并行分段取样 | `SPRING_K`/`SPRING_R0`; `AT`/`KAPPA` | WHAM / `pymbar` MBAR + 重叠检查 |
| **标准 Metadynamics** | 是 (`MDALGO=11/21`) | `METAD` | VASP 原生 AIMD 探索（无 WT 衰减） | `status=5`, `HILLS_BIN/H/W`, `PENALTYPOT` | `HILLSPOT` 叠加（警惕过填） |
| **WT-Metadynamics** | 否（需外部接口） | `METAD` + `BIASFACTOR` | 经典 MD / MLIP / CP2K / ASE，带高度衰减 | `BIASFACTOR`, `GRID_*`, `CALC_RCT` | `sum_hills` 或 `metad.rct` $c(t)$ 重加权 |
| **`OPES_METAD`** | 否（需外部接口） | `OPES_METAD` | 能垒大致已知、CV 较好时快速收敛 PMF | `BARRIER`, `PACE`, `TEMP`, `STATE_*` | 抛弃前段瞬态后用 `opes.bias` 重加权 |
| **`OPES_METAD_EXPLORE`** | 否（需外部接口） | `OPES_METAD_EXPLORE` | 未知能垒、探索多通道/新 CV | `BARRIER`/`BIASFACTOR`, `EXCLUDED_REGION` | 抛弃更长初始探索段后用 `opes.bias` 重加权 |

## 工作流程

### 1. CV 设计与导数/极限核验
- 键长/键角/二面角及差值（如质子转移 `R1 - R2`）优先选用平滑、无奇点、与目标自由能过程正交度低的坐标；复杂断键重排或配位数切换 CV 按需参阅 [reactive-cv.md](references/reactive-cv.md)。
- 对复杂反应 CV 在部署长轨迹前执行静态结构校验与有限差分导数/作用力验证。

### 2. 引擎输入配置与单位核对
- **原生 VASP**：按 [vasp-sampling.md](references/vasp-sampling.md) 配置 `INCAR`、`ICONST`（区分 `status=0/4/5/7/8`）、`LBLUEOUT`、`INCREM`、`SPRING_K`/`SPRING_R0` 或 `MDALGO=11/21` + `HILLS_*` + `PENALTYPOT`。注意原生 VASP **不支持 WT-Metadynamics 与 OPES**。
- **PLUMED / ASE / CP2K / LAMMPS**：按 [plumed-sampling.md](references/plumed-sampling.md) 配置 `UNITS LENGTH=A TIME=fs ENERGY=eV`（或对应力场单位）、`RESTRAINT`、`METAD`（必设 `GRID_*` 与 `CALC_RCT`）或 `OPES_METAD` / `OPES_METAD_EXPLORE`（严格校验 `BARRIER` 能量单位、`EXCLUDED_REGION` 与 `STATE_WFILE`/`STATE_RFILE`）。
- 投产前在本地或头节点用单帧 `plumed driver` 验证语法、核模块与首帧 CV 值；多段重启时强制对齐 `COLVAR`/`KERNELS`/`OPES_STATE` 或 `HILLSPOT -> PENALTYPOT` 状态。

### 3. 采样诊断与稳态筛选
- **Slow-growth**：对比正/反向拉动或更小 `INCREM` 验证滞后，合并续算时剔除边界重复帧。
- **Umbrella / Constrained AIMD**：按窗口检查时间序列平衡并截除初段弛豫；Umbrella 必须确认相邻窗口直方图明显重叠。
- **WT-Metadynamics / OPES**：在 `COLVAR` 中核对**反应物–过渡区–产物多次往返穿越（recrossing）**，检查 `metad.rct` 增长率或 `opes.rct` / `opes.zed` / `opes.neff` 平台期以划定稳态起点。

### 4. PMF 重建与误差分析
- 严格遵循 [estimators.md](references/estimators.md) 执行公式一致的数据重建：
  - Blue Moon / Slow-growth：梯度提取、度量修正及梯形积分（显式声明任何简化近似）。
  - Umbrella：WHAM 或无箱 MBAR（`pymbar`），三维径向距离 CV 需审视是否加 $(d-1)k_B T \ln r$ 雅可比修正。
  - WT-Metad / OPES：以与 `UNITS` 一致的 $k_B T$ 执行 $c(t)$ 或 `opes.bias` 指数重加权，**必须验证分块时间漂移（block drift）**并给出分块误差 / bootstrap / `statistical_inefficiency` 置信区间。

## 按需参考文档与开源工具

- **VASP 原生设定**：[VASP 增强采样配置（ICONST / Blue Moon / Umbrella / Metadynamics）](references/vasp-sampling.md)
- **PLUMED / ASE / OPES 设定**：[PLUMED 采样配置（Umbrella / WT-Metad / OPES / OPES Explore）](references/plumed-sampling.md)
- **反应性 CV 设计**：[反应性 CV、Voronoi/Grotthuss 追踪与导数测试](references/reactive-cv.md)
- **PMF 重建与统计**：[自由能估算器、重加权与分块误差分析](references/estimators.md)

复用关键开源项目：

| 工具 / 方法 | GitHub 仓库 |
|---|---|
| PLUMED 2（Metadynamics / WT-Metad / Umbrella / OPES / `driver`） | [plumed/plumed2](https://github.com/plumed/plumed2) |
| PyMBAR（MBAR 重加权与 `statistical_inefficiency`） | [choderalab/pymbar](https://github.com/choderalab/pymbar) |
| Grossfield WHAM（1D/2D Umbrella `wham`） | [agrossfield/wham](https://github.com/agrossfield/wham) |
| i-PI 与 VASP Slow-growth 扩展 | [i-pi/i-pi](https://github.com/i-pi/i-pi) · [zhangchenyu-USTC/i-pi_slow-growth](https://github.com/zhangchenyu-USTC/i-pi_slow-growth) |

## 交付产物与验收

- **输入与校对阶段**：可运行的参数文件（`INCAR` 片段/`ICONST`/`PENALTYPOT` 或 `plumed.dat` + 驱动器配置），并通过单帧 `driver`/首步 CV 数值及单位一致性核对。
- **后处理与报告阶段**：可重复的 Python 重建与诊断脚本、标注采样诊断（recrossing、窗口重叠或滞后对比）与统计误差棒的 PMF 图表及表格，并在输出中明确所采用的约定（如 $\frac{1}{2}\kappa$、雅可比修正、丢弃的瞬态长度与是否省略度量项 $Z$）。
