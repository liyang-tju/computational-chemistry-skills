# 热力学与 CHE 协议

## 1. 静态吸附态频率计算与热力学校正

### VASP 局域频率（`IBRION = 5`）要点
- **只动吸附质（可选含顶层活性金属）**：直接沿用收敛优化目录的 `CONTCAR`、`KPOINTS`、`POTCAR`，在独立 `freq/` 子目录设置：
  ```ini
  IBRION = 5
  POTIM  = 0.015
  NFREE  = 2
  EDIFF  = 1E-7
  ISTART = 0
  ICHARG = 2
  ```
  注意关闭 `NPAR`/`NSIM` 冲突限制并保持原基底 `Selective dynamics` `F` 标记冻结底部原子，避免整块金属晶格全部算入有限差分振动。
- **提取工具区别（极其关键）**：
  - **表面吸附分子**：不能用理想气体平动/转动公式！使用 `VASPKIT` 任务 **`501`**（或 ASE `HarmonicThermo`），只对全部 $3N_{\text{free}}$ 个振动模式求和。
  - **气相参考分子（$\text{H}_2$、$\text{CO}$、$\text{CO}_2$、$\text{H}_2\text{O}$）**：使用 `VASPKIT` 任务 **`502`**（或 ASE `IdealGasThermo`），正确计入平动、转动（区分线性 vs 非线性分子及对称数 $\sigma$）和指定分压 $p$ 下的体积熵项 $-k_B T \ln(p/p_0)$。
- **低频截断一致性**：受阻平动/转动产生的低频实模（如 $< 50\,\text{cm}^{-1}$）在谐振近似下会导致 $S_{\text{vib}}$ 急剧发散；若对 $< 50\,\text{cm}^{-1}$ 频率统一抬升至 $50\,\text{cm}^{-1}$（或统一忽略极小虚频），必须对同一反应网络的所有吸附物种采用完全一致的截断阈值。

## 2. 计算氢电极（CHE）反应自由能公式

首先写出每步包含 $\text{H}^+ + e^-$ 转移的配平化学方程式：

$$\Delta G(U_{\text{RHE}}) = \Delta E_{\text{DFT}} + \Delta E_{\text{solv}} + \Delta \text{ZPE} - T\Delta S + \Delta G_U$$

其中质子-电子对化学势在 $U_{\text{RHE}} = 0\,\text{V}$ 下以气相氢为参考：
$$\mu(\text{H}^+ + e^-) = \frac{1}{2} G(\text{H}_2, g, 298.15\,\text{K}, 1\,\text{bar})$$

### 电势项 $\Delta G_U$ 符号（严禁死背固定正负号）
- **质子耦合电子还原步骤**（消耗 $n$ 个 $\text{H}^+ + e^-$，例如 $\text{CO}_2^* + \text{H}^+ + e^- \to \text{COOH}^*$）：
  $$\Delta G_U = + n e U_{\text{RHE}}$$
  （外加更正的电势 $U > 0$ 拉低电子化学势，不利于电子参与还原，使还原步 $\Delta G$ 升高；外加负偏压 $U < 0$ 推动还原进行。）
- **质子耦合电子氧化步骤**（释放 $n$ 个 $\text{H}^+ + e^-$，例如 $\text{H}_2\text{O} + * \to \text{OH}^* + \text{H}^+ + e^-$）：
  $$\Delta G_U = - n e U_{\text{RHE}}$$
  （外加正电势 $U > 0$ 有利于体系失电子，使氧化步 $\Delta G$ 降低。）

### RHE vs SHE 与 pH 处理
$$U_{\text{RHE}} = U_{\text{SHE}} + \frac{k_B T \ln 10}{e}\,\text{pH} \quad (298.15\,\text{K}\text{ 时约 }+0.0592\,\text{V/pH})$$
- 使用 $U_{\text{RHE}}$ 表达 CHE 反应台阶图时，pH 效应已与 $\mu(\text{H}^+) = \mu_0(\text{H}^+) - k_B T \ln 10 \cdot \text{pH}$ 精确抵消，**切勿重复再加减一次 pH 项**。
- 仅在固定 $U_{\text{SHE}}$ 标尺并同时引入显式/恒电势双电层响应时，才按 $U_{\text{RHE}}$ 换算显式拆出 pH 与表面电荷两重贡献。

## 3. 常见气相参考态与对比边界

- **标准压力与液相水参考**：气相分子常见分压设置例如 $\text{H}_2$ 取 `1 bar`、$\text{H}_2\text{O}$ 取 `0.035 bar`（298.15 K 下液态水蒸气压，使气相水自由能等于液相水）。报告中必须明确列出每个气相分子的压力与温度。
- **泛函经验校正**：若文献协议对特定气相分子（如 PBE/RPBE 下 $\text{CO}_2$、$\text{CO}$ 或 $\text{H}_2$ 的气相过结合/误差）加入经验能量修正，必须在 `che_summary.json` 中单独列明校正值与出处，绝不能无声合并进原始 DFT 能量中。
- **对比边界**：比较静态真空 CHE、隐式溶剂 CHE 与动态显式溶剂 PMF 时，三者分别对应“无溶剂弛豫”、“连续介质响应”和“有限温度构象系综平均”，不可只因最终单位都是 `eV` 就混入同一曲线而不标明模型层级。
