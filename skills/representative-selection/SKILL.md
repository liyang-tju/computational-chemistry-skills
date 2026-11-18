---
name: representative-selection
description: "Select diverse, representative atomistic configurations from candidate pools using QUESTS, MACE descriptors or FPS/minimum-set-coverage while tracking provenance. Use before DFT labeling or dataset subsampling."
---
# 代表性构型选择

从大量候选模拟轨迹或构型池中筛选出结构合法、去重且覆盖目标化学与构象空间的代表性子集，并保留每一帧回溯到原始来源的完整索引，用于后续 DFT 标注或主动学习扩充。

## 开始前确认

- **候选池与来源**：输入 `extxyz`/轨迹列表、各自条件标签（如温度、电势、组分 `group_id`）。
- **选择规模与配额**：总选择帧数 `N_target`、各条件/体系配额规则（按比例、等配额或全局联合覆盖）。
- **描述符方案**：`QUESTS`（局部环境压缩/MSC）、`MACE` 预训练模型描述符，还是轻量几何描述符代理（如 SOAP/距离直方图，仅在明确同意近似时使用）。

## 工作流程

### 1. 建索引与几何健康筛查

先为全部候选帧分配唯一 `source_id` 与原始 `frame_index`，再执行**只剔除物理上明显损坏结构**的预筛（输出到 `filtered.csv`）：
- 剔除坐标含 `NaN/Inf`、零/畸变晶胞体积，或出现非物理核碰撞（如最小 MIC 间距 `< 0.70 Å`）的崩溃帧；
- **不要误删反应事件**：例如质子转移或表面成断键过渡态（`O-H ~ 0.95–1.3 Å`）属于高价值采样构型，阈值设置不能误杀合理化学键变化。

### 2. 去重与化学状态区分

在描述符计算前去除完全重复或超近重复帧，避免后续选择被同一静止构象占满：
- 比较构型重复时，必须同时核对**元素组成、晶胞、PBC、对齐坐标以及关键电子状态字段（如 `charge`、`NELECT`、`potential`）**；同几何不同电荷/电势属于不同物理样本，不能合并删除。

### 3. 计算结构描述符

根据任务要求和当前已安装库（如 `quests`、`mace`、`dscribe`）计算表示（详见 [描述符与选择](references/selection.md)）：
- **QUESTS**：通常基于原子局部环境集合计算结构间分布距离/信息熵，或执行 Minimum Set Cover（MSC）；需记录所用截止半径 `rcut`、邻居数 `k` 与带宽 `bandwidth`。
- **MACE 描述符**：明确记录模型版本/路径、提取层数（`num_layers`）、`invariants_only=True/False` 及逐原子聚合方式（均值池化、最大池化或局部环境覆盖）。

### 4. 按配额与多样性算法挑选子集

- 执行最远点采样（FPS）、k-center 贪心覆盖或 QUESTS MSC。
- 若候选池过大需**分块分层先选再合并全局选择**，必须在 `selection.json` 中记录每块大小与近似策略，不将其报告为全局精确最优。
- 检查每个分组的实际有效候选数：若某组候选少于配额，全选该组并报告缺口，绝不通过复制同一帧凑数。

### 5. 输出与去标签校验

写出 `selected.extxyz` 时（若下游用于 DFT 标注）：
- 清理旧力场/MLP 预测的 `energy`/`forces`/`stress` 并置 `atoms.calc = None`，保留 `sample_id`、`charge`/`NELECT`、`FixAtoms` 约束与来源元数据；
- **校验选择后几何未被预处理修改**：确认输出坐标与原始候选帧坐标逐位一致（描述符标准化或居中仅用于打分，不改变输出原子坐标）。

## 按需参考

- QUESTS / MACE 描述符参数设置、FPS 示例脚本与分层近似要点：阅读 [描述符与选择](references/selection.md)。

## 交付产物与验收

1. **`selected.extxyz`**：选出构型文件（含清理后的必要条件标签与来源信息）。
2. **`selected_indices.csv`**：`sample_id, source_id, source_frame, group_id, min_mic_dist, selection_rank`。
3. **`filtered.csv`**（若有被筛除帧）：记录剔除原因。
4. **`selection.json`**：记录描述符版本/参数、随机种子、各组配额与实际选中数。
