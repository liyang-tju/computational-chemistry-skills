# 周期电子性质

## 1. 功函数与平面平均静电势（`LOCPOT`）

- **计算设置**：求静电势与功函数时，VASP 建议开启 `LVHAR = .TRUE.`（仅输出 Hartree + 离子静电势，不含振荡的 XC 势，真空平台更平滑）；若体系为非对称 slab（如仅单侧吸附），应配合 `LDIPOL = .TRUE.` 和 `IDIPOL = 3`（沿真空轴方向），使真空两侧出现明显分离的上下真空平台。
- **功函数公式**：
  $$\Phi = E_{\text{vac}} - E_F$$
  （单位 eV；注意从 `OUTCAR` 读入的 `E-fermi` 仅在三维/二维体相真空平台合理参考下才有绝对意义。）
- **常见错误检查**：
  1. 绘制平面平均静电势 $V(z)$ 曲线，检查真空区域是否存在足够宽且平坦的平台（如斜率 $|\mathrm{d}V/\mathrm{d}z| \approx 0$）；若原子跨周期太近导致无平坦真空区，**绝不能随便取一个点当真空势**。
  2. 非对称 slab 在开启偶极修正后，存在**吸附侧真空势**与**裸露侧真空势**两个不同平台，必须分别说明所求的是哪一侧表面的功函数。
  3. 固液界面算相对电极电势或势剖面时，记录选定的水相平均窗口是相对于即时表面位置还是固定坐标，并做窗口宽度敏感性检验。

## 2. 电荷密度差（$\Delta\rho$）

对于界面吸附体 $AB$ 拆分为片段 $A$ 和 $B$：
$$\Delta \rho(\mathbf{r}) = \rho_{AB}(\mathbf{r}) - \rho_A(\mathbf{r}) - \rho_B(\mathbf{r})$$

- **严格前置条件**：三个 `CHGCAR` 的**晶胞矢量、坐标原点（勿居中移动）、原子坐标及 FFT 网格 (`NGXF, NGYF, NGZF`) 必须完全一致**。
- **电荷积分核对**：在中性体系计算完逐点相减后，在三维网格上积分 $\int_{\Omega} \Delta \rho(\mathbf{r})\,dV$（注意 VASP `CHGCAR` 写出的是 $\rho(\mathbf{r}) \times V_{\text{cell}}$，求和除以总格点数 $N_{\text{grid}}$ 即得总电子数变化），核对总积分应接近 `0`（除非刻意比较带不同总电子数的片段）。

## 3. Bader 电荷分析

VASP PAW 赝势仅输出价电子密度到 `CHGCAR`，直接对 `CHGCAR` 做 Bader 会把原子核周围内层空洞误认为盆地边界。必须联合全电子核电荷密度：

```bash
# 1. 前置 VASP 单点需设置 LAECHG = .TRUE. 与 LCHARG = .TRUE.
# 2. 合并全电子核密度作为参考，再在 CHGCAR 上做拓扑分割
chgsum.pl AECCAR0 AECCAR2
bader CHGCAR -ref CHGCAR_sum
```

- **结果核对（`ACF.dat`）**：
  - `ACF.dat` 给出的 `CHARGE` 列是**分配到该原子的电子数**（对应所选参考总密度下的价电子数），并非直接净电荷！
  - 净电荷计算：$q_i = Z_{\text{val}, i} - N_{\text{Bader}, i}$（其中 $Z_{\text{val}, i}$ 从对应 `POTCAR` 的 `ZVAL` 读取）。
  - 检查 `ACF.dat` 底部的 `NUMBER OF ELECTRONS` 与 `OUTCAR` 中的 `NELECT` 是否一致（网格误差通常在 `0.01–0.05 e` 内）。

## 4. 偶极矩与跨条件对比

- 带净电荷体系的偶极矩**依赖坐标原点选择**（$\mathbf{p}(\mathbf{r}_0 + \Delta\mathbf{r}) = \mathbf{p}(\mathbf{r}_0) - Q \Delta\mathbf{r}$），跨体系比较带电体系偶极必须明确统一参考原点（例如以表面顶层质心为原点）。
- 不要给取了绝对值或模长的平均偶极事后人为补加正负号，需要带符号分量时应回到逐帧向量重算。
