# 输入与运行适配

## 1. POTCAR 与元素映射检查

- **一致性原则**：`POSCAR` 第 6 行的元素种类和出现顺序必须与 `POTCAR` 中 `TITEL` 的顺序严格一致。如果 `POSCAR` 包含重复元素段（如 `Pt O Pt`），尽量先合并排序再生成对应 `POTCAR`，或确保 `POTCAR` 完全按段拼接。
- **赝势版本记录**：同一种元素常有标准版、`_pv`、`_sv`、`_h`、`_s` 或 GW 变体（例如 `O` vs `O_s` vs `O_h`，`Fe` vs `Fe_pv`）。同一对比系列计算必须采用完全一致的赝势组合，并在 `protocol_notes.md` 中记录 `TITEL` 列表。
- **截断能基准**：常规 `ENCUT` 建议不低于所含所有 `POTCAR` 中最大 `ENMAX` 的 1.3 倍（或严格遵照项目统一协议，如 `400/450/520 eV`）。

## 2. KPOINTS 与 k-spacing 约定

使用自动生成网格或 `KSPACING` 时，必须注意不同工具对“倒空间间距”是否包含 $2\pi$ 的差异：

- **VASP 原生 `KSPACING`**（定义含 $2\pi$）：倒格矢长度 $|\mathbf{b}_i| = 2\pi |\mathbf{a}_j \times \mathbf{a}_k|/V$，网格数 $N_i = \max(1, \lceil |\mathbf{b}_i| / \text{KSPACING} \rceil)$。例如 `KSPACING = 0.20 Å⁻¹` 对应不含 $2\pi$ 记法中的 `0.032 × 2π Å⁻¹`。
- **VASPKIT 等工具的 `2π` 记法**：常见如 `0.03` 或 `0.04`（单位 $2\pi\cdot\text{\AA}^{-1}$），实际分母是 $|\mathbf{b}_i| / (2\pi)$。

若将两者数值直接混填，会导致 k 网格密度相差 $2\pi \approx 6.28$ 倍！生成后务必检查 `KPOINTS`（或 `IBZKPT`）的实际 $(N_1, N_2, N_3)$ 网格数是否符合预期，并确认 slab 真空方向固定为 `1`。

## 3. 二进制变体与 GPU/MPI 并行布局

- **变体选择**：
  - `vasp_std`：通用复数版（支持任意 k 点）。
  - `vasp_gam`：仅 Gamma 点实数波函数加速版（仅用于 `KPOINTS` 为 `1 1 1` Gamma-centered；切勿用于多 k 点）。
  - `vasp_ncl`：非共线自旋 / SOC 版（`LNONCOLLINEAR = .TRUE.` 或 `LSORBIT = .TRUE.`）。
- **并行参数（`KPAR` / `NCORE` / `NPAR`）**：
  - 优先采用当前集群和当前 VASP 构建已验证的脚本配方，不要把“1 GPU 对应 1 MPI rank”或某台机器的 `NCORE` 值直接硬套到所有节点与 VASP 版本。
  - GPU OpenACC 版本常见做法是使总 MPI rank 数等于可用 GPU 卡数（如单机 4 卡设 `ntasks=4`），`KPAR` 取 `1` 或整除 GPU 数且整除不可约 k 点数；部分 GPU 版本建议省略或固定 `NCORE = 1`。提交后务必查看 `OUTCAR` 开头几行确认实际运行的 `running on N total cores`、`distrk` 和 GPU 绑定信息。
- **补丁与标签兼容性**：如使用 VTST（`IOPT`、`ICHAIN`）、VASPsol（`LSOL`、`EB_K`）、CP-VASP/Fermi-level 控制等补丁，须先核对当前二进制是否确实编入了对应模块（避免被未识别的 INCAR 参数静默忽略）。

## 4. 重启、停止与常见错误排查

- **兼容边界**：
  - 修改 `ENCUT`、`ISPIN`、`LNONCOLLINEAR`、晶胞大小/形状或原子数后，**禁止**直接复用旧 `WAVECAR`；`CHGCAR` 在原子数和 FFT 网格（`NGXF/NGYF/NGZF`）不变时才兼容。
  - 若结构在上一轮因 SCF 崩溃或原子飞散发生畸变，勿直接从末帧 `CONTCAR` 续算，应回退到崩溃前最后一个健康离子步或初始合理构型。
- **正常中止（`STOPCAR`）**：
  - 写入 `LSTOP = .TRUE.`：当前离子步完成后安全退出，写出完整 `CONTCAR` 与 `WAVECAR`（推荐）。
  - 写入 `LABORT = .TRUE.`：当前电子步完成后立即退出，适合卡死急救，但末步力可能未收敛。
- **结果自检命令**：
```bash
# 检查离子收敛与电子步迭代是否触及 NELM 上限
grep "reached required accuracy" OUTCAR
awk '/DAV:|RMM:|SDA:/ {step=$2} /free  energy   TOTEN/ {print "last_elec_iter=", step, $0}' OSZICAR | tail -n 10
```
