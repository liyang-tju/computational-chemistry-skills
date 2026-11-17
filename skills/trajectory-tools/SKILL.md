---
name: trajectory-tools
description: "Convert, inspect, extract and join atomistic trajectories while preserving cells, time, atom identity and provenance. Use for VASP, CP2K, LAMMPS and ASE-readable formats; observable statistics belong to trajectory analysis."
---
# 轨迹整理与转换

把结构和轨迹整理成保留物理信息的分析输入，优先使用 ASE Atoms 作为内存表示。统计观测量由对应分析流程完成。

## 工作流程

1. 识别格式及伴随文件：轨迹、拓扑、晶胞、原子类型表和时间步信息。扩展名不足以确定文件包含哪些物理量。
2. 明确原子身份、元素、顺序、PBC、长度与时间单位、帧号和实际步数。文件中的 frame_index 与 simulation_step 分别保存。
3. 对大轨迹优先流式读取。检查完整帧、有限坐标、合法晶胞与逐段时间变化；保留未完整写出的尾部并报告，不能静默解释成正常末帧。
4. 抽帧按明示时间或步数执行，写出源文件与源帧映射。缺少时间信息时保留未知，不凭帧数猜测物理时长。
5. 拼接续算采用已确定的检查点边界；相同结构不自动等于重复时间帧。独立重复轨迹保留 replica 标签，不伪装成连续时间序列。
6. 将转换输出重新读取，核对原子数、元素顺序、晶胞、PBC、所需约束及代表帧的坐标。
7. 明确输出是完整带标签数据、待标注几何还是 MD 初态；只对新副本去掉不适用的能量、力和计算器缓存。

## 按需参考

- 格式伴随文件与边界情况：读取 [格式适配](references/formats.md)。
- 标注、初态和来源字段：读取 [数据表示](references/metadata.md)。

## 输出

结构或轨迹文件、frame_index.csv，以及必要时的 conversion.json。CSV 使用数据集内相对路径或逻辑 source_id；需要保存本机绝对位置时写入独立的本地运行记录。

## 使用约定

- 依赖路径、环境名称、调度资源和科学参数从当前请求、项目文件或运行配置获取；只读探测缺失的环境信息，关键科学选择不明确时再询问。
- 保留源数据与既有结果，使用新的输出位置；提交、取消作业或破坏性操作须在当前授权范围内进行。准备输入本身不等于授权提交。
- 生成的脚本采用顶部配置、清楚的输入输出和相对资源引用。当前运行的本机路径可以记录在运行产物中，不回写到可分享的技能文件。

