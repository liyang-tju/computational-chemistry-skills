---
name: mlp-training-validation
description: "Prepare single-model or committee MACE/CP-MACE training, monitor convergence, validate exported models on grouped test sets and run NVE/NVT stability or uncertainty-sampling checks."
---
# MLP 训练与验证

在明确模型实现（如标准 MACE 或 CP-MACE 等定制变体）与数据协议下，完成单模型或委员会（Committee）训练配置、导出模型实测验证、独立测试集分组误差评估以及短程 MD 稳定性检查。

## 开始前确认

- **模型实现与环境**：确认当前环境实际安装的版本与 CLI（如 `mace_run_train --help`、`mace_eval_configs --help`；使用 CP-MACE 等定制分支时，先查看实际源码支持的参数与电子输入字段）。
- **数据集与键名**：`train.extxyz` / `val.extxyz` / `test.extxyz` 路径、`energy_key` / `forces_key` / `stress_key`、`E0s` 策略、额外电子目标键名（如有）。
- **训练策略**：从头训练、微调（foundation model）还是续训；单模型还是委员会（模型个数及各自随机种子）；GPU 集群资源。

## 工作流程

### 1. 核对数据键名、架构与训练模式

- 只读核实训练脚本/CLI 支持的真实参数，不把标准 MACE 的参数名直接假设为所有定制变体都支持：
  ```bash
  python3 -c "import mace; print(mace.__version__, mace.__file__)"
  mace_run_train --help | head -n 40
  ```
- 分清三类训练入口：
  - **从头训练**：新建独立目录，不引入旧模型权重或旧优化器状态。
  - **微调（Fine-tuning）**：加载基础模型权重时，明确冻结/学习率与目标能量参考基准（`E0s` / multihead 对齐）。
  - **恢复续训**：仅当架构、数据版本与损失定义未变时恢复优化器状态。

### 2. 准备训练配置与委员会目录

- 为单模型或委员会的每个成员建立独立运行目录（如 `committee/seed_1/`, `seed_2/`, `seed_3/`），各自保留独立的 `config.yaml` / 启动脚本与不同的 `--seed`。
- 若用户给定超参数，严格保持不变；只复制配置模板，绝不把旧运行目录的 `.pt` checkpoint 或旧结果拷贝进新目录。
- 静态检查配置与日志路径后，按授权提交到 GPU 计算资源。

### 3. 监控训练曲线与模型导出

- 不要仅凭作业正常退出或目录中出现 `*_compiled.model` / `final.pt` 就认为训练成功：
  - 检查训练日志中的训练/验证集损失曲线、最佳验证 epoch 位置以及最终停止原因（达到 `max_num_epochs` 还是早停 `patience`）；
  - 核对导出模型（`.model` / `_stagetwo.model`）的真实加载能力。

### 4. 在独立测试集上做实际推理评估

必须使用**导出的最终推理模型**在锁定 `test.extxyz`（绝不混用训练集）上跑一次完整评估（`mace_eval_configs` 或 `MACECalculator`）：
- 按体系/条件（`config_type` / `group_id`）分别输出：**总能量 MAE/RMSE**、**单原子能量 MAE/RMSE（meV/atom）** 与 **力分量 MAE/RMSE（meV/Å）**；
- 绘制或核对最大力误差离群帧，检查是否对应未覆盖化学键或标注异常。

### 5. 短程 MD 稳定性与委员会不确定性校验（按需）

仅在模型验证通过并获准时开展下游短程测试或主动学习采集（细节见 [模型验证与部署](references/validation.md)）：
- **初态清理**：跑 MD 前务必清除测试初态中的旧 DFT `energy`/`forces` 缓存，只保留电子态/电势与 `FixAtoms` 约束。
- **能量守恒与稳定性**：短 NVE 测试检查能量漂移与有限力，短 NVT 测试检查温度、RDF 和化学键完整性；短程跑通不等于可长期外推生产。
- **委员会分歧（Uncertainty）**：统计多模型对同一帧原子受力的标准差（如 $\max_i \sigma_{F_i}$），明确阈值来源与候选时间索引，区分“有价值的反应稀疏区”与“结构已飞散的崩溃构型”。

## 按需参考

- `mace_run_train` / `mace_eval_configs` 检查清单、NVE 守恒与委员会不确定性计算代码：阅读 [模型验证与部署](references/validation.md)。

## 交付产物与验收

1. 训练配置文件、启动脚本与成员清单（`models.csv`）。
2. **`test_metrics.csv`**：按 `group_id`/体系分组的能量（meV/atom）与力（meV/Å）误差表。
3. 经实际加载推理验证的导出模型文件（及适用边界说明：覆盖的温度/组分/电势范围）。
