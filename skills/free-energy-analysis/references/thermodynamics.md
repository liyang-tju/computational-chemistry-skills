# 参考态与比较

## 1. 计算氢电极（CHE）反应自由能图

对于每步基本反应，需先写平包含 $\text{H}^+ + e^-$ 转移化学计量的反应式，再计算自由能变化：

$$\Delta G(U_{\text{RHE}}) = \Delta E_{\text{DFT}} + \Delta E_{\text{solv}} + \Delta \text{ZPE} - T\Delta S + \Delta G_{U}$$

- **电势项 $\Delta G_U$ 符号必须由反应方向严格推导**，切勿对所有步骤套同一符号：
  - **质子耦合电子还原步骤**（消耗 $n$ 个 $\text{H}^+ + e^-$，例如 $\text{CO}_2^* + \text{H}^+ + e^- \to \text{COOH}^*$）：
    $$\Delta G_U = + n e U_{\text{RHE}}$$
    （因为外加正电势 $U > 0$ 会拉低电子能量，不利于电子参与还原，使还原步 $\Delta G$ 升高）。
  - **质子耦合电子氧化步骤**（释放 $n$ 个 $\text{H}^+ + e^-$，例如 $\text{H}_2\text{O} + * \to \text{OH}^* + \text{H}^+ + e^-$）：
    $$\Delta G_U = - n e U_{\text{RHE}}$$
    （外加正电势 $U > 0$ 有利于氧化脱电子，使氧化步 $\Delta G$ 降低）。
- **RHE vs SHE 与 pH**：
  $$U_{\text{RHE}} = U_{\text{SHE}} + \frac{k_B T \ln 10}{e}\,\text{pH} \quad (298.15\,\text{K}\text{ 时约 }+0.0592\,\text{V/pH})$$
  在 CHE 中直接用 $U_{\text{RHE}}$ 时，pH 项已与 $\mu(\text{H}^+)$ 中的 $-k_B T \ln 10 \cdot \text{pH}$ 精确抵消，切勿重复再加减一次 pH 项！
- **标准态与溶剂校正**：气相分子（如 $\text{H}_2$、$\text{CO}$、$\text{H}_2\text{O}$）明确气体压力参考态（如 $\text{H}_2\text{O}$ 常用 0.035 bar 对应 298 K 液相蒸气压）、是否加入孤立 DFT 能量经验修正（如 PBE 下 $\text{CO}_2$/$\text{CO}$ 校正）及使用的溶剂化模型。

## 2. 不同方法与温度对比规范

- **物理量命名隔离**：分别命名并保存电子势能 $\Delta E$、静态热修正自由能 $\Delta G_{\text{static}}$、恒电荷自由能 PMF 与恒电势巨势 $\Delta \Omega(U)$，不要偷换概念只改图纵轴标签。
- **双温度焓熵分解警醒**：用仅有的两个温度（如 300 K 与 330 K）拟合 $\Delta F(T) = \Delta H - T\Delta S$ 属于“两点确定一条直线”，自由度为 0，没有任何拟合残差可用于检验线性假设；在同时报告表观 $\Delta H_{\text{app}}$、$-T\Delta S_{\text{app}}$ 时，必须把各自两点的 PMF 统计不确定度直接传播过去并注明仅基于两个温度点。
- **比较真空优化、隐式溶剂与显式溶剂 MD**：三者差异不仅来自溶剂模型本身，还包含了构象采样与电极界面重构效应；在结论中保留各自来源类别。
