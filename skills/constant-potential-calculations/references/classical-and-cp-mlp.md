# 经典恒电势电极与 CP-MACE

## 1. LAMMPS 经典恒电势模拟（`ELECTRODE` 包）

原生集成于官方 [lammps/lammps](https://github.com/lammps/lammps)（`ELECTRODE` 包）。适用于带显式电解液/离子液体/两性离子的纳米尺度电化学界面长时 MD：

```lammps
boundary        p p f
pair_modify     mix arithmetic
kspace_style    pppm/electrode 1.0e-5
kspace_modify   slab 3.0 order 5 mesh 40 40 135   # 显式记录与固定网格以利基准与复现

group           mobile subtract all all_electrode
fix             freeze all_electrode setforce 0.0 0.0 0.0
compute         mobile_temp mobile temp

# 下电极设 VLOWER，上电极设 VUPPER，电极原子高斯电荷宽度 ETA
fix             conp elec_lower electrode/conp ${VLOWER} ${ETA} couple elec_upper ${VUPPER} algo mat_inv symm on etypes on ffield off
fix             nvt_mobile mobile nvt temp 300.0 300.0 100.0
fix_modify      nvt_mobile temp mobile_temp
```

### 关键设置与验收核查
1. **分组控温与速度**：电极原子坐标固定后，控温器和输出温度必须绑定到剔除了电极原子自由度的 `mobile_temp`，切勿用全体系 `temp` 计算均值或做恒温反馈。
2. **双电极电中性与电量监控**：通过 `compute qlower` / `compute qupper` 统计每步两端电极总电荷，确保总电极电荷之和（或加上电解液总电荷）严格守恒闭合；同时输出 `f_conp[1]` / `f_conp[2]` 检查电容矩阵求解耗时与收敛性。
3. **跨段重启要点**：使用 `read_restart` 续算时，必须在输入脚本中**完整重声明** `kspace_style pppm/electrode`、`kspace_modify`、`fix freeze`、`fix conp` 与 `fix nvt_mobile`；改变 MPI 进程网格（如 `processors` 或负载均衡 `balance`）后单条轨迹会混沌分叉，属双精度浮点求和顺序正常表现，应先跑 20–1000 步冒烟检查电极组、电中性与温度正常再投入生产。

## 2. CP-MACE / FermiMACE 训练与恒电势动力学

参考仓库：[yuanyue-liu-group/CP-MACE](https://github.com/yuanyue-liu-group/CP-MACE)（基于 [ACEsuit/mace](https://github.com/ACEsuit/mace)）。

### 数据准备与电子数约定（最易出错）
从 CP-VASP 或 SOLHYBRID+TPOT 轨迹提取 `extxyz` 训练集时，除标准原子坐标、晶胞、`REF_energy`、`REF_forces` 外，还须在每帧 `info` 行提供：
- `potential`：该帧对应的实际电子化学势 $\mu_e$（eV，**所有样本必须统一参考零点口径**）；
- `electron`：**必须转换为相对中性体系的过剩电子数 $\Delta N_e = N_e - \sum_i N_i Z_{\text{val},i}$**（绝不可直接把总电子数如 `1121.6` 写进 `electron` 混用！），且核对所采用的 `valence_map` 与 DFT `POTCAR` 的 `ZVAL` 逐元素完全一致。

### 训练参数对齐
使用支持费米能级/电势学习的分支（如 `FermiMACE`）时，明确指定额外损失权重与误差统计表：
```bash
mace_run_train \
  --model="FermiMACE" \
  --loss="fermi_weighted" \
  --error_table="Fermi_PerAtomRMSE" \
  --energy_key="REF_energy" \
  --forces_key="REF_forces" \
  --energy_weight=1.0 \
  --forces_weight=100.0 \
  --potential_weight=10.0
```
- 同样必须遵循 `$mlp-dataset-pipeline` 的按轨迹/条件 `group_id` 分组防泄漏切分，并在独立测试集上同时检验能量、力与 `potential` 预测误差。

### ASE 恒电势动力学驱动
使用 `ConstantPotentialNoseHoover` 驱动 `FermiMACE`（或单点 `Vasp` `solhybrid` 计算器）时：
- **初态设置**：初始结构 `atoms.info["electron"]` 设为初始过剩电子数 $\Delta N_e$（如 `0.0`），指定 `targetmu`（负值化学势 eV）、虚拟电子质量 `Mne`（如 ~660，调节电子响应惯性）及电子 Nosé-Hoover 链长 `eta_length`（如 `1` 或 `2`）；
- **委员会不确定性监测**：当并行加载多个随机种子模型推进轨迹时（`AverageForceCalculator`），同步记录逐原子力分歧 `force_std` 与化学势分歧 `mu_std`；超过标定阈值（如 `force_threshold` / `fermi_threshold`）的帧须先筛除几何崩溃帧后再送入主动学习 DFT 重标。
