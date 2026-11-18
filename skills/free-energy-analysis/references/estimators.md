# 重建方法与修正

## 1. 约束平均力（Constrained MD / Thermodynamic Integration）

- **符号与类型核对**：先在已知拉伸方向或简单双原子测试体系中确认输出的是 $-\frac{\partial F}{\partial \xi}$ 还是 $+\frac{\partial F}{\partial \xi}$（VASP `REPORT` 中的 `cc`/`b_m` 拉格朗日乘子与 Blue-Moon 修正输出约定因版本与 CV 类型而异，必须实测核实符号）。
- **Blue-Moon / 度量修正**：对一般非线性反应坐标 $\xi(\mathbf{r})$，严格自由能梯度为：
  $$\frac{\partial F}{\partial \xi} = \frac{\left\langle Z^{-1/2} \left( -\lambda + k_B T G \right) \right\rangle_{\xi}}{\left\langle Z^{-1/2} \right\rangle_{\xi}}$$
  其中 $Z = \sum_i m_i^{-1} (\nabla_i \xi)^2$；对于简单两原子距离（且使用对应质量加权约定下），$Z$ 为常数，可消去 $Z^{-1/2}$ 与 $G$，但对于键角、配位数、平面外距离或质心差等非线性 CV，不能漏掉度量修正。
- **积分**：按有序 CV 网格采用梯形/Simpson 数值积分：
  $$\Delta F(\xi_b) - \Delta F(\xi_a) = \int_{\xi_a}^{\xi_b} \left(\frac{\partial F}{\partial \xi}\right) d\xi$$
  缺失数据的中间区间应标记为不确定或补跑窗口，绝不能补成平均力为 0。

## 2. 伞形采样（Umbrella Sampling：WHAM 与 MBAR）

- **PLUMED `RESTRAINT` 偏置公式**：
  $$U_{\text{bias}, i}(s) = \frac{1}{2} \kappa_i (s - s_{0, i})^2$$
  若使用 Grossfield `wham` 等默认同样含 $\frac{1}{2}$ 的工具可直接使用 `kappa`；若某分析工具定义为 $K(s - s_0)^2$，传入前须换算为 $\kappa/2$。
- **使用 `pymbar` 估计 MBAR 与统计无效度**：
  ```python
  import numpy as np
  from pymbar import MBAR, timeseries

  # 1. 对每个窗口计算统计无效度 g，并按步长抽稀取准独立样本
  g_list = [timeseries.statistical_inefficiency(cv_win) for cv_win in cv_windows]
  sub_indices = [timeseries.subsample_correlated_data(cv_win, g=g) for cv_win, g in zip(cv_windows, g_list)]

  # 2. 构造 u_kn 矩阵 (shape: [K_windows, N_total_samples]), 单位 k_B T
  # u_kn[k, n] = beta * 0.5 * kappa_k * (s_n - s0_k)^2
  ```
- **状态整合与 Jacobian**：1D 距离 PMF $W(r)$ 与三维径向自由能或结合自由能之间通常相差径向熵项 $2 k_B T \ln r$（体积元 $4\pi r^2 dr$），应在定义中写明是否已扣除该项。

## 3. OPES / Metadynamics 重加权

- **OPES 重加权公式**（跳过初始偏置未稳态化的瞬态区间 $t < t_{\text{eq}}$）：
  $$w_i = \exp\!\left(\frac{V_{\text{bias}}(\mathbf{s}_i, t_i)}{k_B T}\right)$$
  （对于经典 Metadynamics / Well-Tempered Metadynamics，需在 `COLVAR` 中保留 $c(t)$ 修正项：$w_i = \exp(\beta [V(\mathbf{s}_i, t_i) - c(t_i)])$；对于 `OPES_METAD`，`opes.bias` 已按当前瞬时归一化 $Z(t)$ 构造，直接用于 $\exp(\beta \cdot \text{opes.bias})$ 重加权通常即可，仍应核对所用 PLUMED 版本及 `rct` 稳定性。）
- **能量单位换算**：在 `UNITS ENERGY=eV` 下，$k_B = 8.617333 \times 10^{-5}\,\text{eV/K}$（300 K 时 $k_B T \approx 0.02585\,\text{eV}$）；在 `kJ/mol` 下，$R T \approx 2.494\,\text{kJ/mol}$。
- **限制检查**：如果整段轨迹仅单向越过一次能垒或根本没有来回穿越（recrossing = 0），结果仅能作为“定性趋势/初猜”，不可当成收敛自由能。

## 4. 自相关与分块误差（Block Averaging）

```python
def block_error(series: np.ndarray, n_blocks: int = 5) -> float:
    """将时间序列等分为 n_blocks 块，计算块均值标准误。"""
    trimmed = series[: (len(series) // n_blocks) * n_blocks]
    blocks = trimmed.reshape(n_blocks, -1)
    block_means = blocks.mean(axis=1)
    return float(np.std(block_means, ddof=1) / np.sqrt(n_blocks))
```

- 建议分别扫描 `n_blocks = 4, 8, 16, 32` 观察误差是否趋于平台；若块数太少（`< 4`）或样本远短于相关时间，明确说明误差估计存在低估风险。
- 记住：**对 PMF 曲线做 Savitzky-Golay 或样条平滑只美化视觉，不增加任何真实统计信息**。
