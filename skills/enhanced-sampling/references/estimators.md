# PMF 估算器、重加权与误差分析

相关开源工具：[choderalab/pymbar](https://github.com/choderalab/pymbar)（MBAR 与统计无效度 `statistical_inefficiency`）、[agrossfield/wham](https://github.com/agrossfield/wham)（Grossfield `wham` / `wham-2d`）、[plumed/plumed2](https://github.com/plumed/plumed2)（`sum_hills` 与 `REWEIGHT_BIAS`）、[zhangchenyu-USTC/i-pi_slow-growth](https://github.com/zhangchenyu-USTC/i-pi_slow-growth)。

## 1. 约束 MD（Blue Moon）与慢生长热力学积分（Slow-Growth TI）

### 完整自由能梯度公式（含度量修正）

在受约束条件下沿反应坐标 $\xi$ 积分（Blue Moon 系综）：

$$\frac{dA}{d\xi} = \frac{\left\langle Z^{-1/2}\left(-\lambda + k_B T\, G\right) \right\rangle_\xi}{\left\langle Z^{-1/2} \right\rangle_\xi}$$

其中 $\lambda$ 为约束拉格朗日乘子，$Z = \sum_i \frac{1}{m_i} \left(\frac{\partial\xi}{\partial \mathbf{r}_i}\right)^2$ 为约束矩阵，$G$ 为二阶几何度量修正项。若采用简化标度 $Z=1$（或忽略 $Z^{-1/2}$ 近似），**必须在输出报告中显式声明**，不得静默省略。对于两原子间距 $r_{AB}$，$\nabla\xi$ 为单位向量且模长恒定，$Z$ 为常数、简化近似恰好成立；但对**键角、二面角、配位数及复杂差值坐标 $S$**，$Z$ 随构型剧烈变化，绝不能丢弃 $Z^{-1/2}$ 与 $G$。

### VASP `REPORT` 与 CP2K 输出解析规范

- **VASP `REPORT`**：
  - `cc>` 行第 3 列（`parts[2]`）给出每步 CV 值 $\xi_t$，`b_m>` 行第 2 列（`parts[1]`）给出已包含度量权重/拉格朗日组合的梯度样本；使用前应确认具体 VASP 版本 `REPORT` 格式一致。
  - **多段续算去重坑**：Slow-growth 从 `CONTCAR` 重启续算时，下一段第 1 步常重复上一段末尾的 $\xi$。拼接后务必检测 `np.isclose(xi[i], xi[i - 1], atol=1e-5)` 并去重，再作梯形积分：
    $$\Delta A(\xi_k) = \sum_{i=1}^{k} \frac{1}{2}(\xi_i - \xi_{i-1})(g_i + g_{i-1})$$
  - **Constrained AIMD（固定窗口）**：每个 $\xi_k$ 独立平衡并剔除初始弛豫段后，先做均梯度自相关/分块误差检验，再按梯形或样条对 $\langle dA/d\xi \rangle_k$ 积分并传播误差（各独立窗口方差近似累加）。
  - **Slow-growth 滞后检验**：需验证积分曲线无明显速率依赖（如减半 `INCREM` 或对比正、反向拉动曲线，显著不重合时说明偏离准静态极限，应改用 Constrained AIMD 窗口或增加弛豫/取样）。
- **CP2K**：从 `.lagrange_mult` 提取各约束通道瞬时力后按窗口平均或梯形积分，注意 CP2K 内置原子单位制换算（Hartree / Bohr -> eV / Å）。

## 2. 伞形采样（Umbrella Sampling：WHAM 与 MBAR）

### 统一 $\frac{1}{2}\kappa$ 约定与工具选择

- VASP `SPRING_K`（`ICONST status=8`）与 PLUMED `RESTRAINT KAPPA` 均采用：
  $$V_i(\xi) = \frac{1}{2}\kappa_i(\xi - \xi_{0,i})^2$$
  （若外部工具如 Grossfield `wham` 或早期脚本期望 $V_i = \frac{1}{2}k(\xi-\xi_0)^2$，务必核对其定义是否含因子 $1/2$，以免弹性常数差 2 倍）。
- **工具选型**：
  - `agrossfield/wham`（1D/2D `wham` / `wham-2d`）：轻量、支持周期性边界与 bootstrap 误差；要求输入温度 $T$ 与一致的能量单位下的 $k$。
  - `pymbar`（`MBAR`）：无箱偏差（binless）估计，可直接构造各样本在所有窗口下的简化偏置能矩阵 $u_{kn} = V_k(\xi_n)/(k_B T)$，自然计算重加权自由能与方差协方差矩阵（参见 [choderalab/pymbar](https://github.com/choderalab/pymbar)）。

### 重叠诊断与球坐标 Jacobian 雅可比修正

1. **窗口重叠硬门槛**：合并所有窗口绘制边缘直方图分布，任何相邻窗口必须显著重叠；高能垒区若出现断档或采样空洞，**必须补窗或调整 `KAPPA`**，严禁用平滑/样条内插掩盖。
2. **三维径向距离的雅可比熵修正**：若 CV 为三维空间中两实体间的**径向距离 $r$**（如解离或吸附高度对球壳体积取平均，未在横向约束方向冻结自由度），三维相空间体元 $4\pi r^2 dr$ 会随 $r$ 引入平动体积熵贡献；需根据参考态定义决定是否加上雅可比修正：
   $$F_{\text{corr}}(r) = F_{\text{raw}}(r) + (d - 1)\, k_B T \ln\!\left(\frac{r}{r_{\text{ref}}}\right) \quad (\text{三维通常 } d=3 \Rightarrow +2 k_B T \ln r)$$
   （若吸附过程是在垂直表面法线 $z$ 方向一维投影而非球对称自由体积，则不加 $2k_B T \ln r$；必须清楚区分 `DISTANCE` 与 `ZDIST`/法向投影定义）。

## 3. Metadynamics / WT-Metadynamics / OPES 重加权

### 直接累加法 vs 均衡重加权

- **标准 Metadynamics（VASP `HILLSPOT` / 固定山丘）**：按时间先后累加山丘势再取负即可近似 $-V_{\text{bias}}(s)$。使用 VASP `HILLSPOT` 时，**前几行若来自初始 `PENALTYPOT` 放置的边界墙高斯，绘图时决定是否展示还是剔除人为墙势区**。注意标准固定高度 Metadynamics 若未停止在首次跨越后，长期继续投掷山丘会产生“过填（overfilling）”畸变。
- **PLUMED `sum_hills`（WT-Metadynamics 偏置累加）**：
  $$F(s) = -\frac{\gamma}{\gamma - 1} V_{\text{bias}}(s) \quad (\text{注意 } \gamma \to 1 \text{ 不可逆，}\gamma \to \infty \text{ 退化为标准 MetaD})$$
  命令行 `plumed sum_hills --hills HILLS --kt <kBT>`；若含边界墙或额外 CV 重投影（计算非偏置 CV 上的自由能），必须使用重加权而非仅 `sum_hills`。
- **Well-Tempered Metadynamics 时间依赖重加权（Tiwary–Parrinello $c(t)$）**：
  需在 `METAD` 中开启 `CALC_RCT`，再以每帧权重：
  $$w(t) \propto \exp\!\left(\frac{V(s(t), t) - c(t)}{k_B T}\right)$$
  进行直方图重加权（对应 `COLVAR` 中的 `metad.bias - metad.rct`）。
- **`OPES_METAD` 与 `OPES_METAD_EXPLORE` 准稳态重加权**：
  1. 当偏置趋近准稳态后，直接按瞬时偏置做伞形式重加权：
     $$w(t) \propto \exp\!\left(\frac{V_{\text{bias}}(s(t))}{k_B T}\right) \quad (V_{\text{bias}} = \text{opes.bias})$$
     也可使用 PLUMED `REWEIGHT_BIAS TEMP=<T>` + `HISTOGRAM`。
  2. **关键区分**：`OPES_METAD` 通常很快使 `opes.rct` 与 `opes.zed` 进入稳定平台，只需丢弃较短前段瞬态；**`OPES_METAD_EXPLORE` 直接追踪并更新目标分布，探索阶段偏置波动显著大于 `OPES_METAD`**，重加权前必须检查 `opes.rct`、`opes.zed` 与 `opes.neff`，**丢弃足够长的初始探索段**直至这些统计量平稳后，才统计各窗口/分段权重！

### $k_B T$ 单位硬校验与收敛核查

- **单位铁律**：
  - 当 PLUMED `UNITS ENERGY=eV` 时：$k_B = 8.617333262 \times 10^{-5}\ \text{eV/K}$（$300\ \text{K}$ 下 $k_B T \approx 0.025852\ \text{eV}$）。
  - 当 PLUMED 默认 `kJ/mol` 时：$R = 8.314462618 \times 10^{-3}\ \text{kJ/(mol}\cdot\text{K)}$（$300\ \text{K}$ 下 $RT \approx 2.4943\ \text{kJ/mol}$）。
  单位混用会直接导致指数权重 $\exp(V/k_B T)$ 溢出或严重压扁。
- **收敛三步校验**（仅有单条漂亮 PMF 曲线不够）：
  1. **Recrossing 往返次数**：CV 轨迹必须在反应物态、过渡区域与产物态之间发生**多次充分往返扩散**（单向跨越后不再返回无法保证相对能级收敛）。
  2. **分块时间漂移（Block PMF Drift）**：将去瞬态后的后半段采样拆成 2–4 个连续时间块分别重加权，检查能垒与反应自由能差 $\Delta F$ 是否随时间收敛且块间差异在允许误差内。
  3. **偏置饱和检查**：WT-Metadynamics 中沉积高度明显衰减且 $c(t)$ 单调平滑增长；OPES 中 `opes.rct` / `opes.zed` / `opes.nker` 趋于平稳。

## 4. 自相关时间与分块平均误差（Block Averaging）

时间序列采样（尤其是 AIMD 中的约束力 `b_m` 或近连续 `COLVAR`）高度时间相关，朴素标准误 $\sigma/\sqrt{N}$ 会严重低估不确定度。应结合有效样本数 $N_{\text{eff}} = N / g$（`pymbar.timeseries.statistical_inefficiency`）或分块平均增长曲线平台值报告标准误：

```python
import numpy as np


def block_error(x: np.ndarray, n_blocks: int = 5) -> float:
    """将一维平衡时间序列均分为 n_blocks 段，评估平均值的标准误。"""
    chunks = np.array_split(x, n_blocks)
    means = np.array([c.mean() for c in chunks if len(c) > 0])
    if len(means) < 2:
        return 0.0
    return float(means.std(ddof=1) / np.sqrt(len(means)))
```

对于长连续梯度轨迹（如单一约束 AIMD 窗口），可扫描多个块大小 $b \in [1, N/10]$，绘制 $\text{SEM}(b)$ 随块大小变化曲线（或拟合渐近饱和模型如 $A\arctan(Bb)$），确认误差棒已达平台再行引用；窗口间总积分误差可用各独立窗口标准误平方和开方（$\sqrt{\sum_k (w_k\,\text{SEM}_k)^2}$）或结合分块 `WHAM/MBAR` bootstrap 给出置信区间。
