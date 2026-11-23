# 恒电势动力学与混合溶剂

## 1. CP-VASP（`LCEP = .TRUE.`）

参考仓库：[yuanyue-liu-group/CP-VASP](https://github.com/yuanyue-liu-group/CP-VASP)。CP-VASP 在 VASP 离子步/MD 主循环中按 `NESCHEME` 调节 `INFO%NELECT` 以维持费米能级接近 `TARGETMU`（负值，eV）：

| `NESCHEME` | 电子数更新逻辑 | 常见适用场景 | 关键控制参数 |
|---|---|---|---|
| `1` | 仅在 `NSTEP = 1` 循环调电子直至 `< FERMICONVERGE`，后续每 `NEADJUST` 步单次估算更新 | 快速起步单点 / 轻度调节 | `TARGETMU`, `FERMICONVERGE`, `CAP_MAX`, `NEADJUST` |
| `2` | 每 `NEADJUST` 步按前后两步差分电容 `CAP_CP`（钳位在 `[0.1, CAP_MAX]`）单次更新 `NELECT` | 恒电势几何优化、稳健 MD | `TARGETMU`, `CAP_MAX`, `NEADJUST`, `ECHANGE_MAX` |
| `3` | 每 `NEADJUST` 步内嵌循环重算 SCF，直到 `|TARGETMU - E_F| < FERMICONVERGE` | 严格瞬时恒电势控制（计算代价高） | `TARGETMU`, `FERMICONVERGE`, `CAP_MAX` |
| `4` | 虚拟电子坐标速度-Verlet 动力学（无独立电子控温） | 微正则电子测试 | `Mne`, `NEADJUST`, `TARGETMU` |
| `5` | 虚拟电子坐标 **Nosé-Hoover 链（NHC）大正则 MD** | **生产级恒电势 AIMD** | `NEADJUST = 1`, `TARGETMU`, `T_eta`, `eta_length`, `Mne` |

- **输出解析**：`OSZICAR` 中含 `CPM-ion` 行，记录实时过剩电子与化学势；将轨迹转为 `extxyz` 供分析或训练时，按 `NEADJUST` 步长对齐坐标/力与电子数，且确认记录的是相对中性价电子的差值或总值。
- **能量口径**：CP-VASP 报告的 `GCE` 包含零温熵外推（`TOTEN - EENTROPY/(2+NORDER)`）和电子库修正，核查力–能量一致性时须使用同一有限温度变分自由能定义。

## 2. SOLHYBRID + TPOT（显隐混合溶剂恒电势 AIMD）

参考仓库：混合溶剂模型 [comet-group/VASPsol](https://github.com/comet-group/VASPsol) + 目标电势控制 [comet-group/tpot](https://github.com/comet-group/tpot)。

### SOLHYBRID：防止隐式电解质渗入显式水层
在显式水+表面体系中直接开启普通 VASPsol，常因水分子之间局部低电子密度空隙导致隐式介电体错误渗入双电层内。`LSOLHYBRID = .TRUE.` 提供两种填充/隔离方式：

```ini
LSOL = .TRUE.
EB_K = 78.4
LAMBDA_D_K = 3.04
TAU = 0
LSOLHYBRID = .TRUE.
CORE_C = 1 6 11       # 必须严格对应 POSCAR 第 6 行各元素的核内/芯电子占位参数（按实际体系填写）
METHOD_SH = 1         # 1: 平面平均价电子密度补空隙电荷; 2: 按 ZMIN_SH/ZMAX_SH 划定显式保护区间
SIGMA_SH = 0.02222    # 界面过渡平滑宽度（分数坐标尺度）
ALPHA_SH = 0.1        # 补空隙系数
# 若使用 METHOD_SH = 2，显式声明保护区间（分数坐标，使隐式溶剂仅作用于区间外体相/真空侧）：
# ZMIN_SH = 0.0
# ZMAX_SH = 0.622222
```

- **注意事项**：若用 ASE `Vasp` calculator 驱动 `SOLHYBRID`/`TPOT`，必须预先向 `ase.calculators.vasp.create_input` 的 `bool_keys` / `int_keys` / `float_keys` 注册这些非标准关键词，否则 ASE 会跳过或报错。

### TPOT：目标真空功函数控制
```ini
LTPOT = .TRUE.
TPOTMETHOD = 2            # 1: SCF 步内调电子; 2: 每离子步末调节（AIMD 推荐）
TPOTTRUEVACLEVEL = .TRUE. # 用 -(EFERMI - VACLEVEL) 计算真实真空标尺电势；.FALSE. 则用 FERMI_SHIFT
TPOTVTARGET = 3.0         # 目标功函数（正值！例如 3.0 V 对应绝对费米能级 -3.0 eV）
TPOTVDIFF = 0.01
TPOTELECTSTEP = 0.05      # 单步最大电子数变化限制
TPOTDYNVRATE = .TRUE.
TPOTVRATE = -1.6
TPOTVRATELIM = 0.05
TPOTGCENERGY = .TRUE.
TPOTGCIONIC = .TRUE.
NELECT = <初始合理电子数>  # 建议先跑单点或用 TPOTMETHOD=1 充电到目标电势后再启 MD
```

- **重启规则**：每个离子步末 `OUTCAR` 会输出 `UPDATED NELECT`；断点续算开启新目录时，**必须**把 `INCAR` 中的 `NELECT` 改为前段末尾的 `UPDATED NELECT`，否则会退回初猜重新震荡。

## 3. i-PI + VASP（Socket 恒电势动力学与 Ne 对电极）

参考仓库：[zhangchenyu-USTC/i-pi_constant-potential](https://github.com/zhangchenyu-USTC/i-pi_constant-potential)（基于上游 [i-pi/i-pi](https://github.com/i-pi/i-pi)）。通过 patched VASP（`IBRION = 24` 开启恒电势电子坐标，`IBRION = 23` 为同配置固定电荷对照）连接 `i-pi` 的 `<electrons enabled="true">` 块（带虚拟质量 `mass` 与 SVR `potentiostat`）：

1. **隐式溶剂加速模式**：通过 `<solvation_update_stride>`（如每 5 步重算一次完整隐式电解质响应，其余步仅推进电子坐标 `q`）大幅降低隐式溶剂耗时。
2. **Ne 虚拟对电极模式（免隐式溶剂）**：在界面水上方真空区放置一层固定不动的 Ne 原子（在 `<fixatoms>` 中与底部金属层一起固定），设置 `Ne_doping="true"`。降低 `<target_workfunction>` 即可向金属-水界面注入电子，补偿电荷局域在 Ne 层上。
   - **标尺限制**：Ne 对电极法构建的是**相对偏压**（如相对零偏压参考降 1.0 V），不等同于绝对 SHE/RHE 电势标尺。
3. **公共必检项**：两种模式都必须绘制平面平均静电势 $V(z)$ 剖面，确认 `<potential_average_region>` 精确落在真空或体相溶剂的平坦平台内部（在 Ne 模式下须位于 Ne 层上方真空区）。
