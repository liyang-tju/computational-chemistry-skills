---
name: trajectory-analysis
description: "Analyze MD/AIMD/MLP trajectories for density profiles, water orientation, RDF, coordination numbers, hydrogen bonds, RMSD and reaction events using consistent PBC, time windows and autocorrelation-aware statistics."
---
# 轨迹统计分析

在已整理和审计通过的轨迹上计算界面分布、氢键配位、构象 RMSD 与反应事件统计，保持时间窗口、原子选择、周期边界（PBC）与误差口径在所有对比条件间完全一致。纯格式转换、拼接与去重请用 `$trajectory-tools`。

## 开始前确认

- **输入轨迹与元数据**：`extxyz`/轨迹文件、晶胞与时间序列信息（`dt`、有效平衡截断时间 $t_{\text{eq}}$、独立重复 `replica_id` 列表）。
- **目标观测量与精确定义**：仅运行本次请求的指标（如水密度剖面、$\langle \cos\theta \rangle$ 取向、RDF/CN、氢键数、RMSD 或反应事件统计），不默认全量扫跑无关项目。
- **对比维度**：不同温度、电势、覆盖度或力场之间使用相同的判据、单位和有效可比窗口。

## 工作流程

### 1. 核对有效窗口与 PBC 完整性

- 确定丢弃的预平衡时长 $t_{\text{eq}}$ 及统计采样区间 $[t_{\text{start}}, t_{\text{end}}]$；确保变胞（NPT）轨迹读取的是**逐帧晶胞**而非首帧晶胞。
- 在任何矢量计算（O-H 键矢量、水偶极、分子质心）前，必须先基于周期性最小像距（MIC）**重建跨盒断裂的多原子分子**，切勿直接对原始坐标做几何平均。

### 2. 按需加载对应分析协议

根据当前所求物理量只读对应参考文档：
- **界面密度、水取向与 RDF/配位**：阅读 [界面分布](references/interface.md)。
- **氢键网络、供受体定义与质子转移重指派**：阅读 [氢键与配位](references/hydrogen-bonds.md)。
- **RMSD 对齐方式、反应事件驻留时间与误差统计**：阅读 [构象、事件与统计](references/conformation-statistics.md)。

### 3. 保留逐帧与分项中间数据

- 不要只输出一个最终总体均值，应保存**逐帧/逐块序列**及分项数据（例如溶质作为供体 vs 受体、各个氧位点、上/下界面、不同 `replica`），方便事后诊断时间漂移与各重复间一致性。
- 对密度分布与配位数做基本**积分自洽核对**（如 $\int \rho(z) A_{xy}\,\mathrm{d}z = N_{\text{waters}}$）。

### 4. 计算时间相关修正后的误差

- 分别报告单条轨迹内的分块误差（Block Averaging / 统计无效度 $g$）与多条独立重复（replicas）之间的离散程度，不将总帧数当成独立样本数。
- 对长度不等的轨迹合并统计时，明确选择“按帧加权”还是“先求各 replica 均值再等权平均”。

## 按需参考

- 相对表面坐标、bin 体积归一化、`cos(theta)` 测度与界面 RDF：阅读 [界面分布](references/interface.md)。
- 氢键角度两种定义、动态质子归属与归一化分母：阅读 [氢键与配位](references/hydrogen-bonds.md)。
- 表面对齐 vs 自身对齐 RMSD、事件滞回阈值与分块统计：阅读 [构象、事件与统计](references/conformation-statistics.md)。

## 交付产物与验收

1. **`analysis.py`**：参数集中于顶部配置区（路径、时间窗、cutoff、bin 宽），可跨条件复用（优先复用项目已有可靠脚本）。
2. **观测量表与逐帧/分块明细 CSV**：含清晰列名与单位（如 `z_rel_surf_A`, `rho_g_cm3`, `hbonds_per_solute`, `se_block`）。
3. **`analysis_summary.json`**：记录实际使用的定义公式、截断判据、时间窗口、$N_{\text{frames}}$、$N_{\text{replicas}}$ 及自检积分结果。
