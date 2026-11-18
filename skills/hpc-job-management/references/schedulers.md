# 调度适配

## 1. Slurm 模板与常用命令

### 标准 Slurm 脚本骨架
```bash
#!/usr/bin/env bash
#SBATCH --job-name=calc_job
#SBATCH --partition=<partition>
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:4              # 无 GPU 任务请删除此行，按集群真实 GRES 语法修改
#SBATCH --time=24:00:00
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$PWD}"

# 环境初始化（按当前集群/项目配置填入）
# module purge
# module load ...

export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"

# 示例启动命令（按实际 MPI 启动器与二进制替换）
mpirun -np "${SLURM_NTASKS}" <program_cmd> > run.log 2>&1
```

### 常用状态与排查命令
```bash
# 查看单个运行中作业的节点、工作目录与标准输出路径
scontrol show job <job_id>

# 查询历史或刚结束作业的退出码、耗时与峰值内存
sacct -j <job_id> --format=JobID,JobName%20,Partition,State,ExitCode,Elapsed,MaxRSS

# 带依赖提交（前驱成功退出后才启动；数组依赖用 afterok:<job_id> 或 aftercorr:<job_id>）
jid1=$(sbatch --parsable step1/job.sh)
jid2=$(sbatch --parsable --dependency=afterok:${jid1} step2/job.sh)
```

- **注意事项**：
  - Slurm 会把脚本复制到 `/var/spool/slurmd/...` 下执行，**切勿**在 `job.sh` 里用 `dirname "${BASH_SOURCE[0]}"` 来找项目目录，必须用 `$SLURM_SUBMIT_DIR` 或显式 `cd`。
  - 如果计算目录已有活跃作业或已有未处理完的输出，先核实两者关系再决定是否覆盖或另建目录。

## 2. PBS / Torque 模板与常用命令

### 标准 PBS 脚本骨架
```bash
#!/usr/bin/env bash
#PBS -N calc_job
#PBS -q <queue>
#PBS -l select=1:ncpus=16:mpiprocs=4:ompthreads=4:ngpus=4
#PBS -l walltime=24:00:00
#PBS -j oe

set -euo pipefail
cd "${PBS_O_WORKDIR:-$PWD}"

export OMP_NUM_THREADS=4
mpirun -np 4 <program_cmd> > run.log 2>&1
```

- 注意区分 PBS Pro 语法（`select=...:ncpus=...:mpiprocs=...`）与旧版 Torque 语法（`nodes=1:ppn=16`），以集群 `man qsub` 或现有可用模板为准。
- PBS 带依赖提交：`qsub -W depend=afterok:${jid1} step2/job.sh`。

## 3. 本地执行边界

- 无调度器时，仅在用户明确允许且当前节点资源足够的工作站上直接运行。
- 登录节点/控制节点通常禁止跑大型 DFT、MD 或模型训练；遇到需要计算资源的测试，默认先写好调度脚本并说明所需资源，再按授权提交。
