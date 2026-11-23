# 电荷扫描、隐式恒电势与 CPTI

## 1. 固定电荷 `NELECT` 扫描与二次拟合（Grand Potential Parabola）

适用于任何带 `LSOL = .TRUE.` 的 VASPsol（[henniggroup/VASPsol](https://github.com/henniggroup/VASPsol)，`ISOL = 1`）或非线性 VASPsol++（[VASPsol/VASPsol](https://github.com/VASPsol/VASPsol)，`ISOL = 2`, `C_MOLAR = 1.0`, `R_ION = 4.0`, `TAU = 0`）构建，不依赖特定恒电势补丁。

### 操作流程
1. 从 `POTCAR` 逐元素读取 `ZVAL`，结合 `POSCAR` 计算中性体系价电子总数 $N_0$。
2. 选取对称多组偏置电子数 $\Delta N_e$（常见 5–9 点，如 `-1.0, -0.5, 0.0, +0.5, +1.0` 或覆盖目标电势区间），设置 `NELECT = N_0 + delta_N`（**禁止同时设置 `EFERMI_ref` 或 `LDIPOL`**）。文件夹命名建议用 `dm` / `dp` 或 `n` / `p` 明确区分“增减电子”与“物理电荷正负”，避免符号误读。
3. 收集全部电子 SCF 与离子优化收敛的状态，提取：
   - 体系能量 $E(\Delta N_e)$（同一系列统一 `TOTEN` 或 `energy without entropy` / `sigma->0` 口径）；
   - 费米能级 $E_F$ 与 `OUTCAR`/日志中的 `FERMI_SHIFT`；
   - 化学势 $\mu_e = E_F + \text{FERMI\_SHIFT}$；
   - 电极电势：$U_{\text{SHE}} = E_{F,\text{ref}}^{\text{SHE}} - \mu_e$，或 $U_{\text{vs PZC}} = E_F(\Delta N_e = 0) - E_F(\Delta N_e)$（注意：$U_{\text{vs PZC}}$ 需每个几何或同一参照各自先算中性零电荷态）。
4. 勒让德变换并二次拟合：
   $$\Omega(\Delta N_e) = E(\Delta N_e) - \Delta N_e \cdot \mu_e$$
   - 既可直接拟合 $\Omega(U) = a_\Omega U^2 + b_\Omega U + c_\Omega$，也可先拟合 $E(\Delta N_e) = a_E \Delta N_e^2 + b_E \Delta N_e + c_E$，再由 $\mu_e = \partial E/\partial \Delta N_e = 2 a_E \Delta N_e + b_E$ 解析映射得到连续曲线 $\Omega(U)$ 与微分电容 $C = 1 / (2 a_E)$（单位 `e/V`，除以界面面积换算 $\mu\text{F/cm}^2$）。
   - **必做体检**：物理上要求 $a_E > 0$（正电容）、$a_\Omega < 0$（向下开口抛物线）且拟合 $R^2$ 高（若散点明显偏离二次曲线，排查吸附态重构、溶剂脱附或部分点 SCF 未收敛）。

### ASE `FCP` 自动化选项
若通过 `ase.calculators.FCPelectrochem.FCP`（[hellozhaoming/FCP-vasp-ase](https://github.com/hellozhaoming/FCP-vasp-ase)）自动调节 `NELECT`，需显式传入 `innercalc`（含 `lsol=True`）、目标电势 `U`、`work_ref`（正值 SHE 绝对功函数，如 `4.6`）、`NELECT0` 与初猜 `NELECT`。

## 2. VASPsol++ 原生恒电势（`EFERMI_ref`）

基于 [VASPsol/VASPsol](https://github.com/VASPsol/VASPsol) 在 SCF 内自动调整屏蔽电荷使费米能逼近目标值，可直接用于单点、结构弛豫及 CI-NEB / Dimer 过渡态搜索：

```ini
LSOL = .TRUE.
ISOL = 2
C_MOLAR = 1.0
R_ION = 4.0
TAU = 0
EFERMI_ref = -4.66    # 对应 U_SHE = 0 V；目标 U_SHE = -1.5 V 时设为 -3.16
EFERMI_tol = 0.01     # 显式指定费米能收敛容差 (eV)
LDIPOL = .FALSE.      # 严禁开启偶极修正；同时不固定 NELECT
```

- **能量防重复扣除**：当 `EFERMI_ref < 0` 时，VASPsol++ 源码在能量修正中**已经包含** `-q_sol * EFERMI_ref`（即已经处于巨势口径），后处理对比反应能垒或 $\Delta G(U)$ 时直接相减即可，绝不可再次减去 $\Delta N_e \cdot E_{F,\text{ref}}$。
- **CI-NEB / Dimer 要点**：优化 TS 时建议先用普通或中性路径跑出初猜路径/过渡态并收敛虚频，再切换为恒电势 `EFERMI_ref` + `ICHAIN = 2`（Dimer，附 `MODECAR`）或 CI-NEB；注意 Dimer 计算需移除 `NPAR`/`NSIM`/`IMAGES`/`SPRING`/`LCLIMB` 等无关冲突参数。
- **部分芯密度（`DENCOR`）形状力缺失核验**：
  - VASPsol++ 原始实现基于“赝势部分芯密度不与空腔边界重叠”的假设，在原子力计算中省略了部分芯密度对空腔/介电/离子响应势的显式导数项 $\mathbf{F}_I^{\text{shape}} = -\int v_{\text{shape}}(\mathbf{r}) \nabla_{\mathbf{R}_I} n_{c,I}\,d^3r$。
  - **如何判断是否显著**：对新元素、新赝势或高精度力依赖任务（优化、TS、AIMD），抽取典型代表结构对表层/吸附原子做中心有限差分验证（保持晶胞、FFT 网格与输入完全一致，比较多个小位移如 $h = 0.002\text{–}0.005\,\text{\AA}$）：
    $$F_{I\alpha}^{\text{FD}} = -\frac{\Omega(\mathbf{R} + h\mathbf{e}_{I\alpha}, \mu) - \Omega(\mathbf{R} - h\mathbf{e}_{I\alpha}, \mu)}{2h}$$
    若解析力与有限差分力出现超出数值离散误差的明显系统偏差，说明该体系不可忽略此项，需补全形状力或改用固定电荷差分/其他验证路线。

## 3. CPTI（恒电势热力学积分）

参考实现：[Yanggang-Wang-Group/CPTI](https://github.com/Yanggang-Wang-Group/CPTI)。用于全显式溶剂体系在没有自动恒电势 MD 引擎时沿反应坐标计算自由能曲线：
1. 在各个离散 CV 窗口以当前设定的 `NELECT` 运行固定电子数约束动力学（Slow-growth / Blue Moon）；
2. 按固定间隔抽帧在 VASPsol 下计算表面原子群的 **Bader 电荷**，换算表面过剩电荷密度 $\sigma$ 与瞬时电势 $U = \sigma / C_{\text{EDL}} + U_{\text{PZC}}$；
3. 根据线性响应回归斜率迭代调整各窗口 `NELECT`，使整条反应坐标各窗口均逼近目标恒定电势（如 $|U - U_{\text{target}}| < 0.05\,\text{V}$）；
4. 仅用收敛后的最后一段采样平均力 $\langle \partial F/\partial \xi \rangle$ 做梯形数值积分得到恒电势反应自由能剖面。
