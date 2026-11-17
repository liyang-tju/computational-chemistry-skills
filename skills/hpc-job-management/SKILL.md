---
name: hpc-job-management
description: "Prepare scheduler jobs, inspect queues and dependencies, and measure progress on Slurm or PBS. Use for resource and execution management; scientific completion and restart selection belong to simulation auditing."
---
# 集群作业管理

将已明确的计算计划转换为适配当前集群的执行方案。只查询队列时，不启动输入重写或故障恢复流程。

## 工作流程

1. 识别调度器、用户请求的资源及已有可靠作业模板。读取适用的集群说明，并查询当前分区、队列和限制；历史节点状态仅供定位线索。
2. 分开记录任务数量、每任务资源和实际并发度。核对节点数、MPI ranks、每 rank CPU、线程数、GPU 数与启动命令的关系，不假定各引擎采用相同布局。
3. 在计算目录准备最小脚本。明确工作目录、程序命令、环境初始化、输出和错误日志；验证必需文件与 shell 语法。
4. 分阶段任务先确定科学依赖与验收产物，再选择调度依赖。上游退出成功并不保证下游所需的模型或检查点可用。
5. 获得提交授权后才提交，立即记录任务标识、工作目录、资源与提交时间。批次中断后利用这份记录避免重复提交。
6. 查询时区分排队、执行、进程退出和科学完成。估算速度采用有实际进展的时间窗口，说明预热、SCF 波动与排队时间是否计入。

## 按需参考

- Slurm、PBS、依赖关系与提交目录：读取 [调度适配](references/schedulers.md)。
- 持续监控与性能比较：读取 [监控与吞吐量](references/monitoring.md)。

## 输出

按任务需要交付 job.sh、jobs.csv 和简短的资源说明。jobs.csv 至少保留 task_id、job_id、workdir、scheduler、state、observed_at；仅查询时直接报告结果即可，无需强制生成文件。

不要用休眠占卡作业假装为后续大作业预留资源；不要把节点故障一次性观察固化成永久黑名单。

## 使用约定

- 依赖路径、环境名称、调度资源和科学参数从当前请求、项目文件或运行配置获取；只读探测缺失的环境信息，关键科学选择不明确时再询问。
- 保留源数据与既有结果，使用新的输出位置；提交、取消作业或破坏性操作须在当前授权范围内进行。准备输入本身不等于授权提交。
- 生成的脚本采用顶部配置、清楚的输入输出和相对资源引用。当前运行的本机路径可以记录在运行产物中，不回写到可分享的技能文件。

