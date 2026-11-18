---
name: simulation-audit-restart
description: "Audit VASP, CP2K, LAMMPS or MLP simulation completion and numerical health, locate valid checkpoints and prepare traceable continuations. Use for interrupted runs or completion checks; routine queue status belongs to hpc-job-management."
---
# 计算审计与续算

从已有日志、轨迹、能量序列与检查点文件中核实一项模拟“真正完成了多少、数值是否健康”，并为未完成部分构建可追溯的续算目录与拼接边界。调度层作业退出码为 `0` 并不代表科学计算收敛或成功。

## 开始前确认

- **目标协议**：任务类型（优化 / MD / 单点 / 增强采样 / MLP 训练）、目标步数或物理时长、收敛判据（如 `EDIFFG`）以及所有关联的父段/子段目录。
- **当前需求**：仅做完成度审计，还是同时为未达标任务准备续算目录。

## 工作流程

### 1. 快速排查作业日志与正常终止标志

先按引擎检查实际完成标志与进度（详细判据见 [审计判据](references/completion.md)）：

| 引擎 | 正常结束标志 | 进度 / 收敛检查命令 |
|---|---|---|
| **VASP** | `OUTCAR` 含 `General timing` | 优化：`grep "reached required accuracy" OUTCAR`；MD/SCF：`tail -n 20 OSZICAR` |
| **CP2K** | 输出末尾含 `PROGRAM ENDED AT` | 检查 `*-1.ener` 末行步号与时间，日志搜索 `SCF run NOT converged` |
| **LAMMPS** | 日志末尾含 `Total wall time` | 检查 `log.lammps` 最后输出的 `Step` 及是否有 `ERROR` / `Lost atoms` |

### 2. 检验数值健康与化学稳定性

仅看最后一帧或最终退出码容易漏掉中间崩溃，必须联合检查整段序列：
- **电子收敛**：SCF 迭代是否反复触及 `NELM`/`MAX_SCF` 上限却勉强继续（此时能量和力往往不可靠）。
- **物理量稳定**：检查温度、势能/总能、晶胞体积（NPT 时）与最大受力是否发生剧烈跳变或发散。
- **结构/化学保持**：扫描轨迹关键键长与原子间距，记录任何意外解吸、飞散或断键时刻；若在崩溃前已发生结构畸变，续算起点应回退到崩溃前的健康检查点，而非强行接续失真末帧。

### 3. 定位匹配且完整的检查点

针对不同引擎核对重启文件完整性与兼容边界（具体检查清单见 [检查点](references/checkpoints.md)）：
- 确认结构（原子顺序、总数、晶胞）与速度/热浴/波函数/偏置状态（如 PLUMED `STATE`/`KERNELS`）处于**同一时间点或步号**。
- 对异常中断造成的截断尾帧，先用解析脚本核对完整帧数与最后有效步号，记录在 `audit.csv`。

### 4. 准备独立续算目录（若需要续算）

- **保留原段不动**：在独立新目录（如 `run_02/`）中建立续算输入，不直接覆盖原目录的输入、日志与轨迹。
- **计算剩余步数**：明确区分“累计总步数语义”（如 CP2K `EXT_RESTART` 配合 `RESTART_COUNTERS` 时的 `STEPS`、LAMMPS `run N upto`）与“相对增量步数语义”（如 VASP 新目录重启的 `NSW`）。
- **记录续算关系**：生成 `continuation.json`，写明 `parent_run`、选定的 `checkpoint_step`/`checkpoint_time`、`remaining_steps` 以及保留或重置的状态（如速度、热浴、波函数、偏置）。

### 5. 规范轨迹与日志的拼接边界

合并分析父段和子段数据时，保留原始段文件不变，仅在输出合并视图时**按选定检查点步号截断父段尾部**（防止崩溃后残余帧或重叠步重复计数）：
- 父段保留 `step <= checkpoint_step`（或 `time <= checkpoint_time`）；
- 子段保留 `step > checkpoint_step`（注意部分引擎续算首帧会重复输出 `checkpoint_step`，须去重保留子段前先核对）。

## 按需参考

- VASP / CP2K / LAMMPS / PLUMED 检查点校验与重启设置细节：阅读 [检查点](references/checkpoints.md)。
- 优化、MD、单点、增强采样及 MLP 训练的科学完成验收表：阅读 [审计判据](references/completion.md)。

## 交付产物与验收

1. **`audit.csv`**：至少包含 `task_id, dir, engine, status, last_valid_step, target_step, converged, health_issues, checkpoint_valid, notes`。
2. **`continuation.json`**（准备续算时）：记录父段引用、恢复点、步数换算及保留/重置的状态列表。
3. **独立续算目录**：包含校验就绪的新输入与作业脚本，且未修改原始父目录产物。
