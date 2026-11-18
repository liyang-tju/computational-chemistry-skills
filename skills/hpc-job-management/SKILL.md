---
name: hpc-job-management
description: "Prepare Slurm or PBS job scripts, inspect partitions/queues, manage job dependencies and track execution progress. Use for resource layout and scheduling; scientific convergence auditing belongs to simulation-audit-restart."
---
# 集群作业管理

将计算任务转换为适配当前集群的 Slurm / PBS 作业脚本与依赖工作流，并准确查询队列状态与吞吐速率。仅查询队列或资源状态时，只执行只读命令，不修改任何计算输入。

## 开始前确认

- **调度器与目标分区**：Slurm 还是 PBS、分区/队列名称（`partition`/`queue`）、账户（`account`）与 QoS。
- **资源配置**：节点数（`nodes`）、总 MPI 进程数（`ntasks`）、每任务 CPU 核心数（`cpus-per-task`）、GPU 型号与卡数（`gres=gpu:...`）、内存（`mem`）和墙钟时限（`time`）。
- **运行命令与环境**：实际要激活的 conda/module 环境与可执行程序启动命令（由本地项目配置或当前环境探测获取）。
- **执行授权**：明确当前任务是**仅准备脚本**，还是**已授权提交/取消作业**。

## 工作流程

### 1. 探测集群资源与当前队列（只读）

先核对实际分区限制和当前排队状态，不盲目套用其他机器的分区名或 GPU 语法：

```bash
# Slurm：查看可用分区、节点状态与个人作业
sinfo -o "%P %a %l %D %t %G"
squeue -u "$USER" -o "%.12i %.9P %.20j %.8T %.10M %.6D %R"

# PBS：查看队列与个人作业
qstat -q
qstat -u "$USER"
```

### 2. 核对 MPI / 线程 / GPU 布局

分开明确以下四项参数并核对乘积关系，防止超配或只跑单核：

- `nodes × ntasks_per_node = total_mpi_ranks`
- `ntasks_per_node × cpus_per_task ≤ 单节点物理 CPU 核心数`
- `OMP_NUM_THREADS` 一般设为 `$SLURM_CPUS_PER_TASK`（或由目标程序要求固定为 `1`）
- GPU 绑定：仅当目标程序和集群已验证“1 GPU 对应 1 MPI rank”或特定绑定时才采用对应布局，不跨软件硬套。

### 3. 编写健壮的作业脚本并静态校验

在目标计算目录下写入 `job.sh`（具体 Slurm/PBS 模板见 [调度适配](references/schedulers.md)），必须包含：
1. 明确进入提交/计算目录（`cd "${SLURM_SUBMIT_DIR:-$PWD}"` 或 `cd "${PBS_O_WORKDIR:-$PWD}"`），避免 Slurm 从 spool 副本运行时找不到相对路径；
2. 启用 `set -euo pipefail` 或显式传递程序退出码（防止后处理命令覆盖主计算报错的退出码）；
3. 清晰的 `stdout`/`stderr` 日志文件名与环境变量设置。

检查脚本语法与目标输入文件是否就绪：
```bash
bash -n job.sh
```

### 4. 处理分阶段依赖与防重复提交

- 提交多阶段任务时使用调度器依赖（如 Slurm `sbatch --dependency=afterok:<job_id>`）。注意：`afterok` 仅说明前驱作业退出码为 0，下游脚本开头应先校验关键产物（如 `CONTCAR` 非空、`.restart` 存在）后再启动计算。
- 已授权提交后立即记录到 `jobs.csv`（至少包含 `task_id,job_id,workdir,scheduler,state,submitted_at`），批量任务中断重跑时先检查 `jobs.csv` 与 `squeue`，避免对同一计算目录重复提交写花输出。

### 5. 查询进度与计算吞吐率

查询时明确区分**排队（`PENDING`）**、**运行（`RUNNING`）**、**进程正常退出（`COMPLETED`）**与**科学目标完成**（后者交由 `$simulation-audit-restart` 判定）。吞吐量（`s/step`、`ns/day`）按 [监控与吞吐量](references/monitoring.md) 从有效连续进展窗口计算。

## 按需参考

- Slurm / PBS 作业脚本模板、常用诊断命令与依赖语法：阅读 [调度适配](references/schedulers.md)。
- 作业进度报告、批量轮询约束与吞吐量换算：阅读 [监控与吞吐量](references/monitoring.md)。

## 交付产物与验收

- 仅查询队列时：直接输出当前状态汇总表（含观察时间与命令证据）。
- 准备/提交作业时：交付 `job.sh`、`jobs.csv`（或提交记录），并通过 `bash -n job.sh` 语法检查；禁止提交占卡空跑脚本来“占位”。
