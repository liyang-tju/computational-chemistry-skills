---
name: mlp-dataset-curation
description: "Curate labeled atomistic datasets for MACE or other MLPs, validate units and physical fields, deduplicate structures and construct leakage-aware or incremental train-validation-test splits."
---
# MLP 数据集整理

将已通过 DFT 标注验证的结构集合整理为高质量、防数据泄漏、格式与单位统一的机器学习势（MLP）训练/验证/测试集，并支持在主动学习迭代中安全追加新数据而不破坏既有测试集边界。

## 开始前确认

- **输入数据集与协议**：带标签 `extxyz` 文件（及对应的 `protocol.json`/`sample_map.csv`）；若为增量扩充，需提供已有数据集及 `split_index.csv`。
- **目标模型字段规范**：例如 MACE 常用的 `REF_energy`（或 `energy`）、`REF_forces`（或 `forces`）、`REF_stress`（或 `stress`），以及电化学/带电模型需要的特定字段（如 `charge`、`nelect`、`potential`，务必核对模型实际读取的 key 名称与单位）。
- **划分粒度与比例**：防泄漏分组键 `group_id`（如 `trajectory_id`、`system_id` 或 `condition_id`）、目标 `train/val/test` 比例、随机种子及孤立原子参考能量（`E0s`）。

## 工作流程

### 1. 字段映射、单位检查与异常值筛查

逐帧检查标签完整性和物理合理性，隔离缺标签或离群样本（绝不用 `0` 填补缺失能量/力）：
- 检查 `energy` 为有限标量、`forces` 形状为 `(natoms, 3)` 且有限、原子数与元素类型合法、晶胞和 PBC 完整。
- 统计单原子能量 $E/N$ 与最大受力 $\max \|\mathbf{F}_i\|$ 分布，排查潜在计算崩溃漏网帧（如 $\|\mathbf{F}_{\max}\| > 50\,\text{eV/\AA}$ 的畸变构型，核实是故意采样的高能态还是计算异常）。
- 不同 `protocol_id`（如不同泛函、截断能或赝势）的标签**不能**无标记混进同一数据集。

### 2. 跨集合重复与近重复排查

检查数据集内部及新旧数据之间是否存在重复构型：
- 判定重复时必须同时比较：**化学式/元素排序、晶胞/PBC、周期对齐几何（或结构指纹）以及电子状态字段（如 `charge`、`potential`、`spin`）**。
- 相同几何但处于不同外加电势或电荷态的样本属于不同标签，不可当作重复帧删除。

### 3. 防泄漏分组划分（或增量锁定划分）

按目标泛化问题选择 `group_id`（如按轨迹段分组，避免相邻 1 fs 的强相关帧被拆进训练集和测试集造成虚假高精度；具体原则见 [重复、分组与划分](references/splits.md)）：
- **新建划分**：使用 `sklearn.model_selection.GroupShuffleSplit` 或分层组划分，确保同一 `group_id` 全部落入同一个集合（`train` / `val` / `test` 之一）。
- **保留旧划分增量扩充**：锁定已有 `val` 和 `test` 成员身份不动，只检查新增数据是否与旧 `val`/`test` 同源或重复（若发生冲突立即报告并给出剔除/归并选项，不悄悄移动旧测试样本）。

### 4. 写出模型输入并回读核验

- 将各集合写出为独立 `extxyz`（如 `train.extxyz`、`val.extxyz`、`test.extxyz`），同时生成全局索引 `split_index.csv` 与字段说明 `schema.json`。
- 回读检验：
  1. 确认 `train ∩ val = ∅`、`train ∩ test = ∅`、`val ∩ test = ∅`（无论是 `sample_id` 还是 `group_id` 均零交集）；
  2. 确认所有字段名、单位与目标训练器（如 `mace_run_train --energy_key=... --forces_key=...`）完全匹配。

## 按需参考

- 防泄漏分组策略、重复识别与增量冲突处理代码：阅读 [重复、分组与划分](references/splits.md)。

## 交付产物与验收

1. **`train.extxyz` / `val.extxyz` / `test.extxyz`**：可直接送入训练的数据文件。
2. **`split_index.csv`**：`sample_id, source_id, group_id, split, protocol_id`。
3. **`schema.json`** 与 **`dataset_summary.csv`**：各分集帧数、分组数、元素覆盖、能量/力范围及被排除样本统计。
