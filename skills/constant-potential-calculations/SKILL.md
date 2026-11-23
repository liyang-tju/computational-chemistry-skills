---
name: constant-potential-calculations
description: "Prepare and analyze constant-potential electrochemical simulations across fixed-charge NELECT scans, VASPsol++/SOLHYBRID, CP-VASP (LCEP/NESCHEME), TPOT, i-PI+VASP (implicit or Ne counter-electrode), CPTI, LAMMPS electrode/conp, CP-MACE and field-dipole corrections."
---
# 恒电势计算

汇总电化学固液界面常用的恒电势模拟路线与分析规范，覆盖隐式溶剂电荷扫描与二次拟合、VASPsol++ 原生恒电势、CP-VASP、SOLHYBRID+TPOT、i-PI+VASP（隐式/Ne 对电极）、CPTI、LAMMPS `ELECTRODE` 与 CP-MACE。

## 开始前确认

- **目标电极电势与参考标尺**：目标 $U$（`V vs SHE`、`V vs RHE` 或 `V vs PZC`）、对应绝对真空费米能标尺 $E_{F,\text{ref}}^{\text{SHE}}$（需按实际泛函、赝势与溶剂模型标定，常见如 `-4.44` 至 `-4.66` eV；若用 $U_{\text{vs PZC}}$ 则需先求同一界面中性参考 $E_F(\Delta N_e=0)$）。
- **物理模型与计算引擎**：
  - 纯隐式溶剂（VASPsol / VASPsol++）、显隐混合溶剂（`SOLHYBRID`）、全显式溶剂加虚拟对电极（Ne 层），还是经典极化恒电势电极（LAMMPS `ELECTRODE`）或机器学习势（`FermiMACE`）；
  - 当地可用二进制及补丁能力（例如是否已编入 `CP-VASP` `LCEP`、`VASPsol++` `ISOL=2`、`SOLHYBRID`、`TPOT` 或 `i-pi` socket `IBRION=24`）。
- **任务阶段**：单点/静态能量、结构/过渡态优化（IS/FS/CI-NEB/Dimer）、恒电势分子动力学（CP-AIMD / 经典 MD）、还是恒电势训练集提取与模拟。

## 方法选型速查

| 方法路线 | 核心控制机制 | 适用场景 | 主要优点 | 关键限制与陷阱 |
|---|---|---|---|---|
| **电荷扫描 + 二次拟合 / ASE FCP** | 扫多个固定 `NELECT` 或外层寻根，作 Legendre 变换 $\Omega(U)$ | 静态吸附能、反应能垒、IS/TS/FS 电势曲线、PZC 标定 | 不依赖复杂扩展补丁，标准 VASPsol/VASPsol++ 即可跑 | 计算量为单点 N 倍；非绝热质子转移帧不适用单曲线外推 |
| **VASPsol++ 原生恒电势** | `ISOL=2` + `EFERMI_ref` 在 SCF 内部自动调节电容电荷 `q_sol` | 单点、静态优化、CI-NEB / Dimer 过渡态搜索 | 一步到位直接给出指定电势下的收敛结构与巨势 | 需核对部分芯密度形状力（`DENCOR`）是否缺失；不能再手动减 $\Delta N_e\mu_e$ |
| **CP-VASP（`LCEP`）** | `NESCHEME=1–5` 按电容迭代或用 NHC 电子恒温器驱动 `NELECT` | CP-优化、CP-AIMD（尤其 `NESCHEME=5` 大正则 MD） | 可做真显式水恒电势 AIMD，支持变步长/热浴耦合 | `NESCHEME=3` 耗时高；`GCE` 含零温熵外推需核对能量口径 |
| **SOLHYBRID + TPOT** | `LSOLHYBRID` 屏蔽显式水空隙 + `LTPOT` 按真空平台调节 `NELECT` | 大尺度显式水+金属双电层 AIMD，防止隐式水渗入界面 | 可选 `METHOD_SH=1/2` 隔离显式层；支持真空平台 `TPOTTRUEVACLEVEL` | 需给对 `CORE_C` 顺序；重启需手动填 `UPDATED NELECT`；ASE 需注册关键词 |
| **i-PI + VASP（隐式 / Ne 层）** | VASP `IBRION=24` 经 socket 连 `i-pi` `<electrons>` 演化电荷 | 恒电势动力学提速、或用 Ne 层替代慢速隐式电解质 | 可用 `solvation_update_stride` 降频或 `Ne_doping` 免隐式求解 | Ne 层仅作**相对偏压**标定；需先核对参考窗口位于真空平坦平台 |
| **CPTI（恒电势热力学积分）** | 约束慢增长轨迹抽帧 + Bader 表面电荷/电容迭代修正各窗 `NELECT` | 显式溶剂中计算恒电势自由能垒（反应路径平均力积分） | 用常规固定电荷 AIMD 近似沿反应路径保持等电势 | 依赖表面原子划分、电容线性近似与多次迭代 |
| **LAMMPS `ELECTRODE`** | `fix electrode/conp` + `pppm/electrode` 实时求解高斯原子电极电荷 | 纳米级/几十纳秒电极-电解液双电层结构、电容与扩散 MD | 尺度和时长远超 AIMD，双电极电势差严格可控 | 经典非反应力场无键断裂；严格要求 `p p f` 与双极总电荷闭合 |
| **CP-MACE / FermiMACE** | 训练带 `potential` 与过剩 `electron` 的神经网络势并用 ASE 驱动 | 纳秒级反应性恒电势动力学与增强采样（可接 PLUMED） | 兼顾反应能力与低计算开销 | 对训练标签电子数基线极其敏感；不可直接外推到未覆盖电势区 |

## 工作流程

### 1. 统一参考零点、符号与基础设置

- **净电荷与多余电子符号**：记中性价电子数为 $N_0 = \sum_i N_i Z_{\text{val},i}$（必须从本次计算使用的 `POTCAR` 逐元素读取 `ZVAL` 核算）。定义多余电子数 $\Delta N_e = N_e - N_0$：$\Delta N_e > 0$ 表示向电极注入电子（物理净电荷 $q = -\Delta N_e < 0$，偏向负还原电势）。
- **电势标尺换算**：
  $$U_{\text{SHE}} = E_{F,\text{ref}}^{\text{SHE}} - \mu_e, \qquad \mu_e = E_F + \text{FERMI\_SHIFT} \quad (\text{或 } E_F - E_{\text{vac}})$$
  - `EFERMI_ref`（CP-VASP 的 `TARGETMU`）为负值（如 `-4.66 - U_SHE`）；TPOT 的 `TPOTVTARGET` 与 i-PI 的 `target_workfunction` 为正值功函数标尺（$= -\mu_e$）。
  - 使用相对零电荷电势时：$U_{\text{vs PZC}} = E_F(\Delta N_e=0) - E_F(\Delta N_e)$（同结构同溶剂参数下比较）。
- **排斥开关**：凡启用 VASP 隐式溶剂（`LSOL = .TRUE.`）时，**必须关闭偶极修正**（`LDIPOL = .FALSE.`，删去 `IDIPOL`/`DIPOL`）；只有在无隐式溶剂的纯真空/显式水-真空体系需要检查真实真空平台时，才考虑开启偶极修正。

### 2. 按路线加载对应协议

根据选定方法只读对应参考文件执行参数配置与脚本准备：
- **静态电荷扫描、ASE FCP、VASPsol++ 原生恒电势、CPTI 与部分芯密度力核验**：阅读 [电荷扫描与隐式恒电势](references/implicit-and-charge-scan.md)。
- **CP-VASP (`LCEP`)、SOLHYBRID+TPOT 与 i-PI (`IBRION=24` / Ne 对电极)**：阅读 [恒电势动力学与混合溶剂](references/cp-aimd-and-hybrid.md)。
- **LAMMPS `electrode/conp` 与 CP-MACE / FermiMACE 训练及运行**：阅读 [经典电极与 CP-MACE](references/classical-and-cp-mlp.md)。

### 3. 校验双重收敛与力–能量一致性

恒电势计算**不能**只看作业退出码或电子步 `EDIFF`：
1. **电子与化学势双收敛**：确认 SCF 未撞 `NELM` 上限，同时确认实时费米能与目标化学势之差落入 `FERMICONVERGE` / `EFERMI_tol` / `TPOTVDIFF` 允许误差内。
2. **模型开关自检**：检查 `OUTCAR`/日志确实打印了所启用的模块参数（如 `ISOL=2`、`LSOLHYBRID`、`LTPOT`、`LCEP`），防止未编入补丁的 VASP 静默忽略关键词。
3. **VASPsol++ 原子力交叉抽检**：对新元素/新赝势组合，在首次开展几何优化、NEB 或 AIMD 前，建议对表层吸附位代表原子按 [电荷扫描与隐式恒电势](references/implicit-and-charge-scan.md) 做一次中心有限差分力核对，排除部分芯密度（`DENCOR`）形状力省略造成的较大误差。

### 4. 统一巨正则势口径（严防重复扣减）

计算巨正则自由能 $\Omega(U) = E - \Delta N_e \cdot \mu_e$ 时，**必须先核实软件输出能量是否已包含电子库变换项**：
- 常规固定 `NELECT` 计算（VASPsol / `ISOL=2` 未设 `EFERMI_ref`）：输出能量为 $E(\Delta N_e)$，后处理需手动减去 $\Delta N_e \cdot \mu_e$；
- VASPsol++ 设置了 `EFERMI_ref < 0` 时：源码内部已加入 `-q_sol * EFERMI_ref` 项，**严禁在后处理脚本中再减一次 $\Delta N_e \mu_e$**；
- `TPOTGCENERGY = .TRUE.` 与 `CP-VASP` 的 `GCE` 字段：注意确认其是否已含 $\Delta N_e \mu_e$ 及熵外推定义（`TOTEN` vs `sigma->0`），跨方法对比必须转换至完全同一热力学定义。

### 5. 续算衔接与训练集导出规范

- **断点续算**：`TPOT` 续算须将新目录 `INCAR` 中的 `NELECT` 更新为上一段 `OUTCAR` 末尾的 `UPDATED NELECT`；`CP-VASP` 与 `LAMMPS electrode/conp` 续算前核对 `restart` 时步与电中性闭合，且在新目录续算不覆盖原段。
- **CP-MACE 数据提取**：导出 `extxyz` 供 `FermiMACE` 训练时，`electron` 字段统一写入**过剩电子数 $\Delta N_e = N_e - N_0$**（非总电子数 $N_e$），`potential` 统一写入同一参考零点下的化学势 $\mu_e$。

## 按需参考

- `NELECT` 二次拟合、ASE `FCP`、VASPsol++ `EFERMI_ref`、CPTI 与形状力差分检验：阅读 [电荷扫描与隐式恒电势](references/implicit-and-charge-scan.md)。
- CP-VASP `NESCHEME`、`SOLHYBRID+TPOT` 与 `i-PI` 隐式/Ne 层：阅读 [恒电势动力学与混合溶剂](references/cp-aimd-and-hybrid.md)。
- LAMMPS `fix electrode/conp` 与 `FermiMACE` 训练/ASE 驱动协议：阅读 [经典电极与 CP-MACE](references/classical-and-cp-mlp.md)。

## 上游方法仓库参考

| 方法 / 组件 | 参考仓库 |
|---|---|
| VASPsol / VASPsol++（`ISOL=1/2`、`EFERMI_ref`） | [henniggroup/VASPsol](https://github.com/henniggroup/VASPsol) · [VASPsol/VASPsol](https://github.com/VASPsol/VASPsol) |
| ASE `FCP` 恒电势计算器 | [hellozhaoming/FCP-vasp-ase](https://github.com/hellozhaoming/FCP-vasp-ase) |
| CP-VASP（`LCEP` / `NESCHEME 1–5`） | [yuanyue-liu-group/CP-VASP](https://github.com/yuanyue-liu-group/CP-VASP) |
| SOLHYBRID 混合溶剂与 TPOT 控制 | [comet-group/VASPsol](https://github.com/comet-group/VASPsol) · [comet-group/tpot](https://github.com/comet-group/tpot) |
| i-PI 恒电势扩展（`IBRION=24` / `Ne_doping`） | [zhangchenyu-USTC/i-pi_constant-potential](https://github.com/zhangchenyu-USTC/i-pi_constant-potential) · [i-pi/i-pi](https://github.com/i-pi/i-pi) |
| CPTI 恒电势热力学积分 | [Yanggang-Wang-Group/CPTI](https://github.com/Yanggang-Wang-Group/CPTI) |
| LAMMPS `ELECTRODE`（`fix electrode/conp`） | [lammps/lammps](https://github.com/lammps/lammps) |
| CP-MACE / FermiMACE | [yuanyue-liu-group/CP-MACE](https://github.com/yuanyue-liu-group/CP-MACE) · [ACEsuit/mace](https://github.com/ACEsuit/mace) |

## 交付产物与验收

1. **输入与运行协议清单**：完整计算目录（`INCAR`/`input.lammps`/`input.xml`）、标定基准说明（$E_{F,\text{ref}}^{\text{SHE}}$ 或 PZC、$\Delta N_e$ 符号约定与能量口径）。
2. **结构化汇总结果**：如 `charge_results.csv`、`quadratic_fits.csv`、`grand_potential_curve.csv` 或带 `potential`/`electron` 标签的 `extxyz`。
3. **验收标准**：全部状态电子 SCF 与目标电势/电极电中性双重收敛；拟合曲线二次项开口符号及 $R^2$ 合理；无重复扣除电子库能量错误。
