---
name: lammps-md
description: "Prepare LAMMPS force-field MD, equilibration, production, replicas and supported electrode simulations. Use when topology, unit styles, fixed-charge or constant-potential protocols need explicit setup."
---
# LAMMPS 模拟准备

准备具有一致拓扑、单位和边界条件的经典 MD。电极模型按任务明确选择，不能把零外加电势、零总电荷和固定原子电荷混为同一条件。

## 工作流程

1. 检查 data/restart、atom_style、units、元素类型映射和所有势函数文件。确认边界、几何约束、水模型和温控压控对象。
2. 核对键合、非键合、长程静电、混合规则及 special_bonds。检查当前 LAMMPS 构建包含所需 style、package 和加速后端。
3. 设计最小化、平衡和生产阶段，明确各阶段目标、时间步、输出间隔和通过条件。受控比较保持初始结构来源与不变参数一致。
4. 生成重复模拟时记录种子、初始结构与速度初始化方法。来源于同一轨迹的相邻帧不能默认视为统计独立。
5. 电极设置检查电荷或电势约束、参考电极、总电荷条件、真空/slab 修正及相应库能力。
6. 准备恢复时核对二进制 restart 的兼容性和各 fix 的状态保留要求。继续累计步数与重新开始计时要明确区分。
7. 检查温度、能量、密度、压力及相关结构指标。平衡后测量的体相密度和界面峰分别报告；按标称盒长估算加水量只能作为初始构建估计。

## 按需参考

- 拓扑、电极和资源适配：读取 [MD 协议](references/protocols.md)。

## 输出

data/restart 引用、input.lammps、类型与元素映射、运行脚本和阶段/重复清单。大规模计算、基准测试和提交遵循当前授权与集群规则。

## 使用约定

- 依赖路径、环境名称、调度资源和科学参数从当前请求、项目文件或运行配置获取；只读探测缺失的环境信息，关键科学选择不明确时再询问。
- 保留源数据与既有结果，使用新的输出位置；提交、取消作业或破坏性操作须在当前授权范围内进行。准备输入本身不等于授权提交。
- 生成的脚本采用顶部配置、清楚的输入输出和相对资源引用。当前运行的本机路径可以记录在运行产物中，不回写到可分享的技能文件。

