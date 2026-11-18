# 计算模式

## 1. 单点计算（Single Point）

适用于能量/力标注、固定构型电子性质分析（功函数、电荷密度、Bader）。

```ini
SYSTEM = single_point
PREC   = Accurate
ENCUT  = 450           # 依据任务协议与 POTCAR max(ENMAX) 确定
EDIFF  = 1E-6
NELM   = 120
ALGO   = Normal        # 难收敛体系可改用 All 或 Damped
ISMEAR = 0             # 金属可按协议用 1；分子/半导体务必用 0
SIGMA  = 0.05
LREAL  = .FALSE.       # 大超胞可按统一协议用 Auto
IBRION = -1
NSW    = 0
LWAVE  = .FALSE.       # 后续需复用波函数时设为 .TRUE.
LCHARG = .FALSE.       # 需 Bader/密度分析时设为 .TRUE.
```

- **能量口径区分**（`OUTCAR`）：
  - `free  energy   TOTEN`：电子自由能 $F = E - T_{\text{el}}S_{\text{el}}$（与原子受力精确自洽）。
  - `energy(sigma->0)`：外推至零展宽的能量 $E(\sigma \to 0)$，常用于 DFT 总能量比较与 MLP 训练集标签。同一项目内必须统一使用同一字段，不可混用。
- **附加输出开关**：
  - 功函数/静电势：`LVHAR = .TRUE.`（不含 XC 势，推荐用于真空能级），配合 `LDIPOL = .TRUE.`、`IDIPOL = 3`（z 方向真空 slab）。
  - Bader 全电子核密度：`LAECHG = .TRUE.` + `LCHARG = .TRUE.`。

## 2. 几何优化（Geometry Optimization）

```ini
SYSTEM = geo_opt
PREC   = Normal        # 终算高精度按协议切换为 Accurate
ENCUT  = 450
EDIFF  = 1E-5
EDIFFG = -0.02         # 负值表示最大原子力阈值 (eV/Å)；正值表示能量差，一般建议用负值
IBRION = 2             # 2=CG (稳健); 1=RMM-DIIS (近极小值快); 3+POTIM=0 配合 VTST IOPT
ISIF   = 2             # slab/吸附必须用 2 (固定晶胞只弛豫离子)；体相晶格优化用 3
NSW    = 200
POTIM  = 0.5
ISMEAR = 0
SIGMA  = 0.05
```

- **分阶段优化**：若采用粗优化 → 精优化两阶段，必须明确每阶段的参数变化与切换条件（如第一阶段达到 `EDIFFG = -0.05` 或用 `CONTCAR` 传给第二阶段），并校验 `CONTCAR` 中的 `Selective dynamics` 约束在衔接时未丢失。
- **收敛验收**：不仅看 `OSZICAR` 结束，还需确认 `reached required accuracy - stopping structural energy minimisation` 出现在 `OUTCAR` 中，区分“达到 `NSW` 上限退出”和“真正收敛”。检查最大力时仅统计可动原子（`T`），排除固定底层原子上的约束力。

## 3. 从头算分子动力学（AIMD）

```ini
SYSTEM = aimd_nvt
PREC   = Normal
ENCUT  = 400
EDIFF  = 1E-5
NELM   = 100
ALGO   = Fast          # 若电子难收敛可切 Normal
ISMEAR = 0
SIGMA  = 0.05
LREAL  = Auto
ISYM   = 0             # MD 务必关闭对称性，避免力和应力对称化误差
IBRION = 0
NSW    = 5000
POTIM  = 1.0           # 时间步长 (fs)；含 H 建议 <= 0.5–1.0 fs（或按协议使用 D 质量）
TEBEG  = 300
TEEND  = 300
MDALGO = 2             # 2=Nosé-Hoover; 3=Langevin; 1=Andersen
SMASS  = 0             # MDALGO=2 时 0 为默认 Nosé 质量；>0 自定义质量；-1 为速度缩放
NBLOCK = 1             # XDATCAR 输出间隔 (步数)，物理时间 = NBLOCK * POTIM
```

- **物理时间换算**：总物理时长 $= \text{NSW} \times \text{POTIM}$，`XDATCAR` 帧间隔 $= \text{NBLOCK} \times \text{POTIM}$。后处理时不要把帧数直接当作步数或飞秒数。
- **速度与续算**：`CONTCAR` 尾部包含速度块（单位 Å/fs）。重新初始化温度时需删除速度块并记录为新起点；连续续算则完整保留 `CONTCAR`（重命名为 `POSCAR`）与必要的 `WAVECAR`（`ISTART = 1`）。

## 4. 约束动力学 / 慢增长（Slow-Growth / Blue Moon）

- 若使用 VASP 原生 `ICONST` + `INCAR`（`MDALGO = 2` 等）或补丁接口（如 Plumed / 约束模块）：
  - 在 `ICONST` 中明确定义约束几何量类型（如键长 `R`、配位数 `S`、键角 `A`）和状态标签（`0` 为 SHAKE 约束，导出 `REPORT` 中的约束力 / Lagrange 乘子）。
  - 必须核对当前 VASP 编译版本实际读取的 `REPORT` 格式、约束力正负号定义以及所需 Blue-Moon 度量修正项，不要把不同版本的输出列直接混用。
  - 保留足够的平衡步数与采样网格（每个 CV 窗口单独目录），使后续积分能区分平衡段和统计平均段。
