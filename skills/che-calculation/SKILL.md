---
name: che-calculation
description: "Calculate static DFT vibrational thermochemistry (ZPE, entropy, VASPKIT/ASE) and Computational Hydrogen Electrode (CHE) reaction free energy diagrams, RHE/SHE shifts, limiting potentials and gas-phase reference corrections. Dynamic enhanced sampling and PMF reconstruction belong to enhanced-sampling."
---
# 计算氢电极计算（静态热力学）

基于静态 DFT（或隐式/恒电势单点与局域频率）计算结果，提取零点能（ZPE）与熵热力学校正，配平质子耦合电子转移（PCET）反应路径并构建计算氢电极（CHE）自由能台阶图与限制电位分析。**动态增强采样与 PMF 重建属于 `$enhanced-sampling`**；电极电势下的电子库变换 $\Omega(U)$ 详见 `$constant-potential-calculations`。

## 开始前确认

- **反应机理与物种表**：反应各基元步骤（IS / 中间体 / TS / FS）、化学计量配平（每步转移 $\text{H}^+ + e^-$ 个数 $n$）及反应方向（还原 vs 氧化）。
- **热力学环境与标尺**：温度 $T$、电势标尺（`V vs RHE` 还是 `V vs SHE` + `pH`）、气相分子参考压力（例如 $\text{H}_2\text{O}$ 在 298.15 K 常取液相蒸气压 `0.035 bar`）。
- **热校与溶剂口径**：表面吸附态采用**仅放开吸附质**（或包含表层）的局域频率（VASP `IBRION = 5`）还是刚性近似；是否包含隐式溶剂化修正 $\Delta E_{\text{solv}}$、恒电势 $\Omega(U)$ 或经验气相修正（如 PBE 下 $\text{CO}_2$/$\text{CO}$ 校正）。

## 工作流程

### 1. 准备并核查静态频率计算（ZPE 与 $TS$）

- **不改变基底冻结约束**：计算表面吸附态振动频率时，从已严格收敛的优化结构（`CONTCAR`）出发，在独立 `freq/` 目录保持与父优化一致的 `KPOINTS`、`POTCAR`、泛函与 `ENCUT`，设置 `IBRION = 5`、`POTIM = 0.015`、`NFREE = 2`、`EDIFF = 1E-7`（从头收敛波函数 `ISTART = 0`），并固定基底只放开吸附质自由度（见 [热力学与 CHE 协议](references/thermochemistry-and-che.md)）。
- **虚频审查**：
  - 极小点（IS / 中间体 / FS）**不应出现显著虚频**；若出现微小低频虚频（常见如吸附质平动/转动受阻模式 $< 50\,\text{cm}^{-1}$），须按统一规则（如以 `50 cm⁻¹` 截断或替代）一致处理所有物种并记录在案，不可选择性删改。
  - 过渡态（TS）必须有且仅有 **1 个** 沿反应坐标的显著虚频，该虚频模不计入振动熵与 ZPE。

### 2. 提取热力学自由能校正（防止重复加减）

使用 `VASPKIT`（吸附态 `501` 仅含振动项；气相分子 `502` 含平/转/振与压力项）或 `ASE`（`HarmonicThermo` / `IdealGasThermo`）计算 $G_{\text{corr}}(T) = \text{ZPE} + \int C_p\,\mathrm{d}T - T S$：
- 明确区分总校正量 $G_{\text{corr}}(T)$ 与单独的 $\text{ZPE}$、$-TS$ 项，**严禁在 `E + G_corr` 上再重复加一次 ZPE**；
- 气相参考分子（$\text{H}_2$、$\text{CO}$、$\text{CO}_2$、$\text{H}_2\text{O}$）务必检查旋转对称数（`symmetrynumber`）、电子自旋简并度及参考压力。

### 3. 配平 CHE 化学计量并严格确定 $eU$ 符号

按照 $\text{H}^+ + e^- \rightleftharpoons \frac{1}{2}\text{H}_2(g)$ 构建每步自由能变（详见 [热力学与 CHE 协议](references/thermochemistry-and-che.md)）：
$$\Delta G(U_{\text{RHE}}) = \Delta E_{\text{DFT}} + \Delta E_{\text{solv}} + \Delta \text{ZPE} - T\Delta S + \Delta G_U$$
- **电势项符号必须逐支路核对**：
  - 还原消耗 $n(\text{H}^+ + e^-)$：$\Delta G_U = + n e U_{\text{RHE}}$（负电势 $U < 0$ 使还原步更放热）；
  - 氧化释放 $n(\text{H}^+ + e^-)$：$\Delta G_U = - n e U_{\text{RHE}}$（正电势 $U > 0$ 使氧化步更放热）。
- **RHE vs SHE 与 pH**：直接以 $U_{\text{RHE}}$ 作自变量时，pH 项已被包含并抵消，**切勿额外再加减 $-k_B T \ln 10 \cdot \text{pH}$**。

### 4. 隔离静态 CHE 与恒电势巨势口径

- 标准静态 CHE 默认只沿电势轴作线性移动 $n e U$（忽略双电层电容随吸附构型变化）；
- 若结合 `$constant-potential-calculations` 得到的巨势 $\Omega(U)$（含电容耦合与工作函数变化），不得与未变换的固定电荷能量混写，也不得对同一电子转移步骤既用 $\Omega(U)$ 扣过化学势又额外硬套静态经验项。

### 5. 输出台阶图数据表与电催化指标

输出完整中间态与反应路径数据表，计算并标明：
- 各步在 $U = 0\,\text{V}_{\text{RHE}}$ 及目标工作电势下的 $\Delta G$；
- 反应电位决定步骤（PDS）与热力学限制电位 $U_L = -\Delta G_{\max} / (n e)$（按还原/氧化方向写明定义与符号）。

## 按需参考

- VASP 吸附态频率设置、VASPKIT/ASE 热校陷阱、CHE 符号推导与标准态参数：阅读 [热力学与 CHE 协议](references/thermochemistry-and-che.md)。

## 交付产物与验收

1. **`species_thermochemistry.csv`**：每个物种（含气相参考）的 $E_{\text{DFT}}$、$E_{\text{solv}}$、$\text{ZPE}$、$-TS$、$G_{\text{corr}}(T)$、虚频个数及参考压力。
2. **`che_profile.csv`**：各基元步骤化学计量、$\Delta G(0\,\text{V})$、$\Delta G(U)$、累积反应自由能台阶与 PDS / $U_L$ 汇总。
3. **`che_summary.json` / 脚本**：记录温度、pH、RHE/SHE 标尺、低频截断阈值、气相经验校正值及协议说明。
