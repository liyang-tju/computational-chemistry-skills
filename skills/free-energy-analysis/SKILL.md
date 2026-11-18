---
name: free-energy-analysis
description: "Reconstruct PMFs and free energy profiles from constrained MD (Blue Moon), umbrella sampling (WHAM/MBAR) or OPES/Metadynamics, evaluate autocorrelation/block uncertainties and build CHE reaction diagrams."
---
# 自由能分析

识别采样类型与热力学定义后，使用匹配的统计力学估计器重建自由能面（PMF）、估计自相关修正误差或构建计算氢电极（CHE）反应能量图。若任务仅是直接比较已计算好的 PMF 文件，则直接复用已有 PMF 定义而不重跑上游重建。

## 开始前确认

- **采样类型与数据**：
  - 约束动力学 / 慢增长（VASP `REPORT` / CP2K `.lagrange_mult`）；
  - 伞形采样（各窗口 `COLVAR`、中心 $\xi_0$、弹簧常数 $k$ 及其是否有 $1/2$ 系数、温度）；
  - OPES / Metadynamics（`COLVAR` 含 `opes.bias`/`metad.bias`、`STATE`/`KERNELS`、`rct`）；
  - 或已算好的单点/自由能表构建 CHE 图。
- **物理与参考约定**：温度 $T$、pH / 电势标尺（SHE vs RHE）、CV 坐标定义、比较区间与零点参考态（反应物盆地、体相自由态还是干净表面）。

## 工作流程

### 1. 核对时间序列、单位与采样窗口

- 清理断续段并对齐时间轴；按能量、CV 及偏置时间序列截去初始平衡段（equilibration discard）。
- 检查各窗口/全轨迹是否存在**非预期旁路反应**或脱附，若部分窗口采样偏离反应通道，明确标识限制而非强行插值掩盖。

### 2. 先做覆盖与重叠诊断，再出曲线

| 方法 | 重建前必查诊断 |
|---|---|
| **约束平均力（TI / Blue Moon）** | 每窗口约束力 $\langle \lambda \rangle$ 时间稳定性、窗口间距无大缺口、符号（$\partial F/\partial\xi$ vs $-\partial F/\partial\xi$）与度量修正 |
| **伞形采样（WHAM / MBAR）** | 相邻窗口直方图**重叠度**（建议相邻重叠 $\ge 5\%\text{–}10\%$）、窗口连通性、各窗口有效样本数 $N_{\text{eff}}$ |
| **OPES / Metadynamics** | 偏置准静态化时刻（如 OPES `zed` / `rct` 稳定期）、双向往返次数（recrossings）、偏置与能量单位统一（$k_B T$） |

### 3. 执行匹配的自由能重建

按 [重建方法与修正](references/estimators.md) 执行对应积分或重加权，务必明确：
- 弹簧势公式是否含 $1/2$（PLUMED `RESTRAINT KAPPA` 定义为 $\frac{1}{2}\kappa(s - s_0)^2$，而部分程序不带 $1/2$）；
- 距离类 CV 是否涉及径向熵/雅可比修正（如二维/三维距离自由能 $w(r) = \text{PMF}_{\text{1D}}(r) + (d-1)k_B T \ln r$）；
- 不同条件对比时使用**统一的参考盆地积分或固定参考点**对齐，不要各自把最低点归零后还直接断言绝对态自由能差。

### 4. 计算自相关修正误差

相邻 MD 帧高度时间相关，**绝对不能把总帧数当独立样本数**来算 $\sigma/\sqrt{N}$：
- 使用统计无效度 $g = 1 + 2\tau_{\text{int}}$（如 `pymbar.timeseries.statistical_inefficiency`）或**分块平均（Block Averaging）**检查块误差随块长收敛平台；
- 有独立重复（replicas）时，同时给出重复间标准差/标准误；报告时清楚注明误差定义（SD / SE / 95% CI / replica spread）。

### 5. 构建热力学 / CHE 图与交付

若涉及电化学反应自由能图或温度依赖焓熵分解，遵循 [参考态与比较](references/thermodynamics.md) 明确 $eU$ 符号、RHE/SHE 换算与标准态修正，然后输出数据表后再转入 `$scientific-figures` 绘图。

## 按需参考

- Blue Moon 积分、PLUMED/MBAR 重加权公式、OPES 归一化与自相关误差代码：阅读 [重建方法与修正](references/estimators.md)。
- CHE 电化学台阶图公式、RHE/SHE 标尺与双温度焓熵分解陷阱：阅读 [参考态与比较](references/thermodynamics.md)。

## 交付产物与验收

1. **`pmf.csv`**（或 **`che_profile.csv`**）：包含坐标网格、自由能均值、误差列、样本数 $N_{\text{eff}}$ 与参考零点说明。
2. **`diagnostics.csv`**：分窗口均值、重叠指标、自相关时间 $\tau_{\text{int}}$ 与分块误差收敛表。
3. **`reconstruct.py`**：完整可复现重建脚本及方法/限制说明。
