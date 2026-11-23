# VASP 原生增强采样配置（ICONST / Blue Moon / Umbrella / Metadynamics）

原生 VASP 的增强采样与约束动力学依赖编译宏 `-Dtbdyn`（关闭时相关 tag 会被忽略或报错）。以下所有原子编号均为 **`ICONST` 1-based 索引**（与 ASE 的 0-based 索引相差 1）。

参考开源工作流：i-PI + VASP Slow-growth 扩展 [zhangchenyu-USTC/i-pi_slow-growth](https://github.com/zhangchenyu-USTC/i-pi_slow-growth)、[i-pi/i-pi](https://github.com/i-pi/i-pi)。

## 1. 通用 MD 前置参数与 `ICONST` 语法

- 通用 `INCAR`：必须开启 `IBRION = 0`、`ISYM = 0`，并设置 `POTIM`（fs）、`NSW`、`TEBEG`（及恒温时的控温参数）。
- `ICONST` 常用几何类型（周期边界内按最小镜像约定 MIC 计算）：
  - `R a b <status>`：原子 `a-b` 距离（Å）。
  - `A a b c <status>`：以 `b` 为顶点的键角（**弧度 rad**）。
  - `T a b c d <status>`：四原子二面角（**弧度 rad**）。
  - `S c_1 c_2 ... c_M <status>`：对前面依次定义的 $M$ 个基元坐标作线性组合 $\xi = \sum_k c_k q_k$（例如键长差 $R_1 - R_2$ 写作前两行 `R ... 0` 后接 `S 1 -1 <status>`）。
  - 复合平方和类 CV 若自定义差值或加权距离，务必在首帧对比脚本算出的 CV 与 `REPORT` 输出是否一致。
- `ICONST` 末位 `status` 含义：
  - `0`：SHAKE 硬约束（用于 Constrained AIMD / Blue Moon 与 Slow-growth；作为 `S` 基元坐标的辅助行时通常也写 `0` 或 `7` 并由 `S` 行决定实际状态）。
  - `4`：Fermi 阶跃偏置（`FBIAS_A`、`FBIAS_D`、`FBIAS_R0`）。
  - `5`：高斯偏置 / Metadynamics（`HILLS_*`、`PENALTYPOT`、`HILLSPOT`）。
  - `7`：仅监控输出到 `REPORT`，不施加约束力或偏置（可配合 `VALUE_MIN`/`VALUE_MAX` 越界停算）。
  - `8`：谐波伞形/弹簧偏置（`SPRING_K`、`SPRING_R0`，可选 `SPRING_V0`）。

## 2. Blue Moon Constrained AIMD 与 Slow-Growth

用于沿已知一维反应坐标计算自由能梯度与积分 $\Delta A$：

- **Constrained AIMD（离散窗口）**：在多个离散 $\xi_k$ 初构型下固定约束，取各窗口平衡段平均广义力：
  ```fortran
  IBRION   = 0
  MDALGO   = 2            ! 1=Andersen, 2=Nose-Hoover, 3=Langevin
  ISYM     = 0
  LBLUEOUT = .TRUE.       ! 必须开启：向 REPORT 输出 Blue Moon 梯度项 (b_m>)
  ```
  `ICONST` 中目标坐标设 `status = 0`（如 `R 105 106 0`）。
- **Slow-growth（连续慢生长）**：在固定速度下连续推动约束坐标，仅适用于慢过程（典型每步步长 $|\text{INCREM}| \sim 10^{-4}$–$10^{-3}\ \text{Å/step}$）：
  ```fortran
  IBRION   = 0
  MDALGO   = 2
  ISYM     = 0
  LBLUEOUT = .TRUE.
  INCREM   = -0.0008      ! 每 MD 步约束目标增量，单位同 CV（需检验正反向滞后）
  ```
- **输出解析与续算陷阱**：
  - VASP 在 `REPORT` 中分别用 `cc>`（含当前 CV 值）与 `b_m>`（含 $-\lambda + \dots$ 与几何度量项）记录各步采样。
  - Slow-growth 从 `CONTCAR` 分段续算时，第 2 段的第 1 帧往往与前一段末帧的 $\xi$ 完全重合（`|xi[i] - xi[i-1]| < 1e-5`），梯形积分前必须去重，否则会导致权重错误或与后续步零步长异常。
  - 若 Slow-growth 速度过快，正反向路径会出现明显滞后；关键能垒应以 Constrained AIMD 分窗口或正/逆向对比校验。

## 3. VASP 伞形采样（Umbrella Sampling）与拉伸 MD

无需外部插件，原生 VASP 通过 `ICONST status = 8` 施加谐波偏置：

$$V_{\text{bias}}(\xi) = \sum_{\mu=1}^{M_8} \frac{1}{2}\kappa_\mu \left(\xi_\mu - \xi_0^\mu\right)^2$$

```fortran
IBRION    = 0
MDALGO    = 2
ISYM      = 0
SPRING_K  = 10.0         ! 弹性常数 kappa_mu（单位 eV/uc^2，例如 eV/Å^2 或 eV/rad^2）
SPRING_R0 = 2.10         ! 平衡中心 xi_0^mu（与 ICONST status=8 个数严格一致）
! SPRING_V0 = 0.0005     ! 可选：每 fs 移动速率 (uc/fs)，用于 Steered MD
```

注意核对 `SPRING_K` 确系 $\frac{1}{2}\kappa$ 形式，并在分析阶段传入一致的 `k` 值与角度单位（`rad`）。

## 4. VASP 原生 Metadynamics 与 `PENALTYPOT` / `HILLSPOT`

原生 VASP 支持标准 Metadynamics（**不支持 Well-Tempered Metadynamics 或 OPES**）：

```fortran
IBRION        = 0
ISYM          = 0
MDALGO        = 11       ! 11=Andersen+MetaD, 21=Nose-Hoover+MetaD
ANDERSEN_PROB = 0.10     ! MDALGO=11 时通常显式给出
HILLS_BIN     = 50       ! 每 N 步投掷一个高斯丘（默认可能不更新，务必显式指定）
HILLS_H       = 0.005    ! 高斯丘高度 (eV)
HILLS_W       = 0.05     ! 高斯丘宽度 sigma (CV 单位)
```

`ICONST` 中将需要施加高斯偏置的 CV 设 `status = 5`（例如 `R 1 5 0`、`R 1 6 0`、`S 1 -1 5`）。

- **`PENALTYPOT` 与墙势用法**：VASP 启动读取 `PENALTYPOT` 作为初始偏置山丘叠加，并在结束后写出完整山丘列表到 `HILLSPOT`。
  - **续算**：`cp HILLSPOT PENALTYPOT` 后继续提交下一步；切勿遗漏否则已积偏置清零。
  - **软边界墙**：可在初始 `PENALTYPOT` 放置高且宽的边界高斯（例如两侧 `[-3.0, 1.0, 0.3]` 与 `[3.0, 1.0, 0.3]`），防止非反应构型逃逸到过远区间。
  - **时间序列提取**：`REPORT` 中 `fic_p>` 行记录每步 CV 演化，可用于快速绘图排查是否发生有效跨越或卡在边界。

## 5. VASP 何时需要结合 PLUMED / 外部驱动器

官方封闭源码 VASP **不包含原生 `-DPLUMED` 开关**。当研究需要以下能力时：
- **Well-Tempered Metadynamics（`BIASFACTOR` / `CALC_RCT`）**
- **`OPES_METAD` 或 `OPES_METAD_EXPLORE`**
- **复杂可微 CV（如配位数切换函数 `COORDINATIONNUMBER`、Voronoi 质子转移、路径 CV）**

应优先按计算场景选择三条标准路径之一（细节见 [plumed-sampling.md](plumed-sampling.md)）：
1. **ASE / i-PI 外挂驱动**：用 ASE `Plumed` 计算器或 [i-pi/i-pi](https://github.com/i-pi/i-pi) 作为引擎驱动力计算器，在每步注入 PLUMED 偏置力。
2. **MLIP + LAMMPS / ASE + PLUMED**：先用 DFT 数据训练主动学习 MLIP（如 `$mlp-training-validation`），再以 LAMMPS/ASE + [plumed/plumed2](https://github.com/plumed/plumed2) 运行纳秒级 OPES / WT-Metadynamics。
3. **切换到原生支持 PLUMED 的 DFT/MD 引擎**：如 CP2K（`&FREE_ENERGY&METADYN USE_PLUMED .TRUE.`）。
