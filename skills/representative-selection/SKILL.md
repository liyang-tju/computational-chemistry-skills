---
name: representative-selection
description: "Select representative atomistic structures using QUESTS or MACE descriptors and minimum set coverage. Use for candidate filtering, diversity selection and source indexing before expensive labeling."
---
# 代表性构型选择

从候选结构中选择规定规模、覆盖明确描述符空间的子集，保留从输出构型到原始帧的映射。

## 工作流程

1. 明确候选来源、选择总数、必需的组别配额及需要覆盖的化学状态。配额来自任务目标，不沿用历史项目比例。
2. 读取结构及其 cell/PBC，建立稳定 source_id 和 frame_index。筛选无效几何或数值异常时保存原因；不要把少见但有效的反应事件当作错误自动丢弃。
3. 区分完全重复、容差内近重复和物理对称等价结构。采用与任务目标相符的规则，保留被合并来源与组别信息。
4. 选择 QUESTS、MACE 或明确标为近似的几何描述符。按 [选择方法](references/selection.md) 确定逐原子到逐结构的聚合、尺度和距离。
5. 大数据先估计存储与计算成本，按需缓存或分层选择。GPU 描述符计算和长任务使用合适计算资源。
6. 返回原始索引，检查数量、唯一性、配额与几何保持。分层近似不能称为与全量精确选择等价。
7. 输出用于标注的副本时清理不适用预测标签，但保留电子态、约束及来源字段。选择质量报告与后续 DFT 科学收敛分别判断。

## 输出

selected.extxyz、selected_indices.csv、必要的 filtered.csv 和 selection.json。记录方法、模型/描述符版本、预处理、随机种子、配额和实际选择规模。

## 使用约定

- 依赖路径、环境名称、调度资源和科学参数从当前请求、项目文件或运行配置获取；只读探测缺失的环境信息，关键科学选择不明确时再询问。
- 保留源数据与既有结果，使用新的输出位置；提交、取消作业或破坏性操作须在当前授权范围内进行。准备输入本身不等于授权提交。
- 生成的脚本采用顶部配置、清楚的输入输出和相对资源引用。当前运行的本机路径可以记录在运行产物中，不回写到可分享的技能文件。

