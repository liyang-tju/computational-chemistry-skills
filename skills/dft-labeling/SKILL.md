---
name: dft-labeling
description: "Prepare chunked DFT single-point labeling jobs for selected structures, track sample_id provenance and collect verified energies, forces and electronic properties while isolating failed frames."
---
# DFT 批量标注

将筛选出的代表性构型转换为分块、可追溯的 DFT 单点计算任务，并在计算完成后按逐帧科学检查规则回收能量、力、应力及所需电子量，输出标准带标签数据集与失败清单。

## 开始前确认

- **待标注结构**：`selected.extxyz`（含唯一 `sample_id` 及来源索引），确认已清除旧力场/MLP 预测的 `energy`/`forces`/`stress`。
- **标注协议（`protocol.json`）**：DFT 引擎（VASP/CP2K 等）、泛函、色散、赝势/基组、截断能、k 点规则、`EDIFF`、自旋、`NELECT`/电荷及所需输出量（如能量、力、应力、电势、Fermi 能）。
- **分块与执行环境**：每个作业块（chunk）包含的帧数、目标执行主机（本地或配置好的远程集群）、资源模板及是否已获准提交。

## 工作流程

### 1. 校验输入与冻结协议

- 检查所有输入帧都具备唯一 `sample_id`、合法 `cell`/`pbc` 与明确电子态（如带电体系的 `charge`/`NELECT`）。
- 显式声明能量与力口径（例如 VASP 采集 `energy(sigma->0)` 还是 `free energy TOTEN`，原始力还是投影约束力），写入 `protocol.json`。

### 2. 按块生成计算目录与任务清单

采用清晰两级目录结构（如 `chunks/chunk_000/s00001/`），同时生成 `sample_map.csv` 记录每一帧的 `sample_id -> chunk_id -> task_dir -> expected_protocol`。
- 静态检查生成的输入文件（如 `POSCAR`/`INCAR`/`KPOINTS`/`POTCAR` 完整性与 `POTCAR` 顺序）及批处理脚本 `bash -n run_chunk.sh`。
- 若需要远程集群计算，先只读测试目标机器路径与工具可用性，再同步输入至新工作目录（不修改源目录）。

### 3. 提交与防重跑追踪

- 仅在获得明确提交授权后执行提交，并立即登记 `job_id` 与对应 `chunk_id`。
- 续跑或重试时，先读取 `label_status.csv` 跳过已成功验收的帧，不静默重复提交仍在运行或已完成的任务。

### 4. 逐帧验收与标签回收

一个 chunk 作业退出码为 `0`，**不代表**里面每一帧都成功收敛。必须按 [逐帧结果验收](references/labels.md) 逐帧解析：
- 仅当该帧同时满足“正常退出 + 电子步在 `NELM`/`MAX_SCF` 内收敛 + 原子数和力数组完整有限”时，才写入 `labeled.extxyz`；
- 失败帧单独登记到 `label_status.csv`（标明失败原因，如 `SCF_UNCONVERGED` / `OUTCAR_INCOMPLETE`），保留原输入和日志用于排查或单独重试。

### 5. 回读抽检与协议版本隔离

写出 `labeled.extxyz` 后随机抽检代表帧核对能量单位（eV）、力形状 `(N, 3)`（eV/Å）、原子顺序及额外字段（如 `charge`、`fermi_energy`）。若中途更改泛函/截断能/k 点协议，必须新建独立目录与新 `protocol_id`，不可将不同协议的标签无标记混入同一输出文件。

## 按需参考

- 逐帧状态机、ASE 原始力 vs 约束力陷阱、应力符号与重试规范：阅读 [逐帧结果验收](references/labels.md)。

## 交付产物与验收

1. **`labeled.extxyz`**：仅包含通过全部科学验收的帧（`energy`/`forces`/元数据完整且单位统一）。
2. **`sample_map.csv`** 与 **`label_status.csv`**：覆盖输入池 100% 的 `sample_id`，状态清晰区分 `pending` / `running` / `passed` / `failed`。
3. **`protocol.json`**：完整记录本次标注物理协议与标签字段定义。
