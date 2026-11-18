---
name: electronic-properties
description: "Analyze periodic and molecular electronic properties including work functions, planar electrostatic potentials, charge density differences, Bader charges, dipoles and Multiwfn wavefunction quantities. Verify input completeness, sign conventions and reference zeros."
---
# 电子结构与波函数分析

根据目标电子性质挑选包含真实电子密度、静电势或波函数信息的计算产物（纯几何 `.xyz`/`.poscar` 不能提供轨道电子性质），统一坐标方向、符号约定与参考零点并生成可复现分析结果。

## 开始前确认

- **目标物理量**：功函数 $\Phi$、平面平均静电势剖面、差分电荷密度 $\Delta \rho$、Bader 电荷、偶极矩、还是 Multiwfn 分子轨道/ESP/RESP/键级/体积/弱相互作用（NCI/RDG）分析。
- **输入可用性与收敛性**：确认 `OUTCAR`/日志显示电子步已真正收敛，且已输出对应密度/势场/波函数文件（如 `LOCPOT`、`CHGCAR`+`AECCAR0`/`AECCAR2`、`WAVECAR`、`.fchk`、`.wfx`、`.molden`）。
- **体系特性**：中性还是带净电荷、自旋极化（`ISPIN = 2`）与否、非对称 slab 是否开启偶极修正（`LDIPOL`/`IDIPOL`）。

## 工作流程

### 1. 核查输入与电子态完整性

- 先检查源计算目录正常终止且电子步收敛，核对净电荷、自旋多重度与原子总数是否与当前结构一致。
- 避免误读目录里遗留的旧版本 `CHGCAR`/`ACF.dat`/`.fchk`，核对修改时间与对应日志关联性。

### 2. 按体系类型执行对应分析路线

- **周期体系（VASP / CP2K）**：按 [周期电子性质](references/periodic.md) 处理：
  - 功函数与静电势剖面：平面平均 `LOCPOT`，校验真空平台平坦度与上下表面差异；
  - 电荷密度差：校验原胞、原点及 FFT 网格完全一致后再做逐点减法并检算总电荷积分；
  - Bader 电荷：联合全电子核密度 `AECCAR0` + `AECCAR2` 与 `CHGCAR` 计算并核算 `ZVAL` 总电荷闭合。
- **分子与波函数（ORCA / Gaussian + Multiwfn）**：按 [波函数与 Multiwfn](references/wavefunction.md) 选择格式并先单样本实测菜单编号，再生成 `answers.txt` 批量执行。

### 3. 明确符号、单位与参考原点

所有输出表必须写清：
- **电荷符号**：写出是**电子布居数**（$N_e$）还是**净电荷**（$q = Z_{\text{val}} - N_e$，正值代表失电子带正电）；
- **偶极矩**：写明单位（`e·Å` 或 `Debye`，$1\,\text{e\cdot\AA} \approx 4.8032\,\text{D}$）、方向定义（正负号指向）以及带电体系所选取的坐标原点；
- **势能零点**：显式区分费米能 $E_F$、真空平台能级 $E_{\text{vac}}$ 与体相内层参考窗口。

### 4. 在独立输出目录保存命令与结果

分析与临时大网格文件均放入新建输出目录（如 `analysis_elec/`），不覆盖原始波函数或全局软件配置（如 Multiwfn 全局 `settings.ini`）。

## 按需参考

- 功函数、`LOCPOT`、电荷密度差、Bader（`chgsum.pl` + `bader`）与带电偶极细节：阅读 [周期电子性质](references/periodic.md)。
- Multiwfn 输入格式转换（`.fchk`/`.wfx`/`.molden`）、无界面批处理模板与电荷/体积定义辨析：阅读 [波函数与 Multiwfn](references/wavefunction.md)。

## 交付产物与验收

1. **性质汇总表**（`electronic_properties.csv`）及剖面/网格输出（如 `planar_avg.csv`、`ACF.dat`、`*.cube`）。
2. **可复现脚本或命令序列**（如 `analyze_elec.py`、`answers.txt`、`settings.ini` 局部副本）。
3. **验收标准**：Bader 总电子数闭合误差在网格精度内（通常 `< 0.05 e`）；密度差积分 $\int \Delta\rho\,dV \approx 0$（中性片段拆分时）；真空平台标准差满足平坦度要求。
