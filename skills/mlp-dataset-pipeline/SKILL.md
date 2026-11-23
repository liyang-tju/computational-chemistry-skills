---
name: mlp-dataset-pipeline
description: "Select representative atomistic configurations (QUESTS, MACE descriptors, FPS/MSC) for DFT labeling and curate labeled MLP datasets with unit/outlier checks, electronic-state-aware deduplication and leakage-free grouped or incremental splits."
---
# MLP 数据集管线

统一负责机器学习势（MLP）训练前的两段数据工程：从候选模拟池筛选代表性构型送标（阶段 A），以及对已标注结构执行校验、去重与防泄漏数据集划分（阶段 B）。两阶段可按需单独执行或顺序衔接，全程保持 `sample_id` 与物理状态可追溯。

## 开始前确认

- **当前入口阶段**：
  - **阶段 A（构型选择 / 降采样）**：输入候选 `extxyz`/轨迹、条件分组键（`group_id`）、目标数量 `N_target` 与配额规则、描述符方案（`QUESTS` / `MACE` / 几何代理）。
  - **阶段 B（标签整理与划分）**：已标注 `extxyz`（及 `protocol.json`/`sample_map.csv`）、目标模型键名（如 MACE 的 `REF_energy` / `REF_forces` / `REF_stress` 及电化学扩展键）、防泄漏分组键 `group_id`、划分比例、孤立原子参考能 `E0s`，以及（增量扩充时）旧 `split_index.csv`。

## 工作流程

### 1. 建索引与几何健康筛查

先为全部输入帧绑定唯一 `sample_id` / `source_id` 与 `source_frame`，再过滤损坏或崩溃结构（记录到 `filtered.csv`）：
- 剔除坐标含 `NaN/Inf`、零或畸变晶胞体积，以及出现非物理核碰撞（如最小 MIC 间距 `< 0.70 Å`）的构型；
- **不要误杀化学反应态**：质子转移或表面成断键过渡态（如 `O-H ~ 0.95–1.3 Å`）属高价值构型，阈值不能过于保守。

### 2. 跨样本与跨集合去重（区分电子状态）

去除完全重复或超近重复构型，避免采样配额被静止构象占满或训练集与测试集撞车：
- 判定重复时必须联合比对：**元素组成与顺序、晶胞/PBC、周期对齐几何（或结构指纹）以及电子状态字段（如 `charge`、`NELECT`、`potential`、`spin`）**；
- 相同几何但处于不同外加电势、电荷态或自旋态的样本属于不同物理标签，**绝不能当作重复帧删除**。

### 3. 阶段 A：代表性构型选择与去标签（用于 DFT 标注时）

按当前环境可用库（`quests`、`mace`、`dscribe`）计算局部环境或整帧表示，并按配额采样（详见 [描述符与选择](references/selection.md)）：
- **描述符记录**：`QUESTS` 需记录 `cutoff`、`k` 与 `bandwidth`；`MACE` 需记录模型标识、`num_layers`、`invariants_only` 及聚合作法（界面体系推荐按活性位点角色掩码池化，避免被大量体相水稀释）。
- **配额与近似说明**：执行 FPS / k-center / QUESTS MSC；若因候选池过大采用分块分层先选再合并，在 `selection.json` 中注明近似；某分组候选不足配额时全选并报告缺口，绝不复制凑数。
- **剥离旧预测并校验几何无改**：写出 `selected.extxyz` 前必须置 `atoms.calc = None` 并清除旧力场/MLP 的 `energy`/`forces`/`stress`（保留 `sample_id`、`charge`/`NELECT`、`FixAtoms` 约束），同时校验输出坐标与原始候选帧逐位一致。

### 4. 阶段 B：标签校验与防泄漏划分（用于训练时）

对已标注数据做物理合理性核查后执行分组划分（详见 [重复、分组与划分](references/splits.md)）：
- **字段与离群筛查**：核实 `energy` 为有限标量、`forces` 形状 `(natoms, 3)` 且有限；排查 $\max \|\mathbf{F}_i\|$（如 `> 50 eV/Å`）及单原子能 $E/N$ 异常帧（绝不用 `0` 填补缺失值）；不同 `protocol_id`（泛函、截断能、赝势不同）的数据**不能**无标记混进同一数据集。
- **新建划分**：按 `group_id`（如 `trajectory_id`、`system_id`、`condition_id`）使用 `GroupShuffleSplit` 切分 `train` / `val` / `test`，避免同一轨迹相邻 1 fs 帧拆散到训练与测试集导致虚高分数。
- **增量扩充**：锁定已有 `val` 和 `test` 成员不动；若新批次存在与旧 `val`/`test` 同源 `group_id` 或几何重复的样本，立即报告冲突或剔除，严禁悄悄移动旧测试集样本。

### 5. 回读核验并写出交付产物

- **阶段 A 交付**：`selected.extxyz`、`selected_indices.csv`、`filtered.csv`（如有）、`selection.json`。
- **阶段 B 交付**：`train.extxyz` / `val.extxyz` / `test.extxyz`、`split_index.csv`（`sample_id, source_id, group_id, split, protocol_id`）、`schema.json` 与 `dataset_summary.csv`；回读确认 `train`/`val`/`test` 在 `sample_id` 和 `group_id` 上严格零交集，且键名/单位与目标训练器（如 `mace_run_train --energy_key=... --forces_key=...`）完全匹配。

## 按需参考

- QUESTS / MACE 描述符参数、角色掩码池化与 FPS 参考代码：阅读 [描述符与选择](references/selection.md)。
- 防泄漏 `GroupShuffleSplit`、增量扩充冲突处理与 `E0s` 规范：阅读 [重复、分组与划分](references/splits.md)。
