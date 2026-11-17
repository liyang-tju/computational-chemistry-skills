---
name: mlp-dataset-curation
description: "Curate labeled atomistic datasets, check units and duplicate structures, and preserve or construct leakage-aware train-validation-test splits. Use after labeling and before model training."
---
# MLP 数据集整理

整理已有标签并建立可解释的数据划分，避免结构、轨迹或目标来源在训练和评估之间造成泄漏。

## 工作流程

1. 明确模型需要的字段与单位，建立输入到目标字段的显式映射。不能仅因字段名字接近就将 potential、potential_shift 或 electron 互相替代。
2. 核对原子数、力数组形状、有限值、晶胞、PBC、能量参考与计算协议。缺失必要标签的样本分别记录，不造零值填补。
3. 按 [重复与划分](references/splits.md) 检查数据内及新旧数据间的重复与关联。相同几何不同电荷/自旋/电势可能代表不同样本，不能只凭坐标丢弃。
4. 用户要求保留旧划分时，保持已有成员身份，只对新增数据作分组和分层。若发现既有泄漏或冲突，明确报告，不静默重排旧数据。
5. 选择适当的 train/validation/test 单位。构象帧、轨迹、体系和条件的外推测试具有不同含义，比例与随机种子由任务配置。
6. 写出数据与索引，再读回确认字段、约束、计数与划分一致性。测试集不参与超参数、特征筛选或归一化拟合。
7. 总结覆盖、排除项、协议差异和每组样本数；不同版本的标签可分组研究，但不能假装来自统一物理协议。

## 输出

模型所需数据文件、split_index.csv、schema.json、dataset_summary.csv 和来源记录。实际帧数与组别分布清楚列出，不硬编码训练比例或种子数量。

## 使用约定

- 依赖路径、环境名称、调度资源和科学参数从当前请求、项目文件或运行配置获取；只读探测缺失的环境信息，关键科学选择不明确时再询问。
- 保留源数据与既有结果，使用新的输出位置；提交、取消作业或破坏性操作须在当前授权范围内进行。准备输入本身不等于授权提交。
- 生成的脚本采用顶部配置、清楚的输入输出和相对资源引用。当前运行的本机路径可以记录在运行产物中，不回写到可分享的技能文件。

