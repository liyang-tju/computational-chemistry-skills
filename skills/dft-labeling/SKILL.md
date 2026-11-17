---
name: dft-labeling
description: "Prepare chunked DFT labeling of selected structures, preserve source metadata and collect successful energies, forces and requested labels. Support configured local or remote execution without assuming a particular host."
---
# DFT 批量标注

把已选择的构型转换为受控 DFT 标签，适配明确的计算引擎与执行地点。结构选择和训练集划分由各自流程完成。

## 工作流程

1. 读取 selected 结构、来源索引和标注协议，核对组成、cell/PBC、约束、电子数、目标标签与单位。确认旧预测能量或力不会误写为参考值。
2. 按实际体系准备计算输入，明确泛函、赝势/基组、k 点、精度、展宽、电子态与所用能量定义。统一协议不等于不同体系必须使用完全相同的所有数值。
3. 根据计算规模和环境限制划分 chunk，保存每帧稳定 sample_id 与任务目录映射。块大小和资源型号通过配置提供。
4. 远程工作先测试目标主机、工具和路径可用性，再在新目录复制必要输入；不改变源数据或模板目录。
5. 生成提交清单并静态检查。获准后提交，逐项记录 job_id。重新执行准备或收集不得静默重复提交已运行任务。
6. 按 [逐帧结果验收](references/labels.md) 收集实际成功标签；一个 chunk 的成功退出不代表其中每帧都成功。
7. 失败项保留原日志和输入，写明重试来源。改变标注协议时创建独立版本，不能把不同协议结果无标记合并。

## 输出

标注输入目录、sample_map.csv、任务清单、带标签 extxyz、label_status.csv 和 protocol.json。若用户要求全部重新标注，不复用旧能量或力。

## 使用约定

- 依赖路径、环境名称、调度资源和科学参数从当前请求、项目文件或运行配置获取；只读探测缺失的环境信息，关键科学选择不明确时再询问。
- 保留源数据与既有结果，使用新的输出位置；提交、取消作业或破坏性操作须在当前授权范围内进行。准备输入本身不等于授权提交。
- 生成的脚本采用顶部配置、清楚的输入输出和相对资源引用。当前运行的本机路径可以记录在运行产物中，不回写到可分享的技能文件。

