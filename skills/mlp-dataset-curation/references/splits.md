# 重复、分组与划分

## 1. 为什么不能逐帧随机划分

连续 AIMD/MD 轨迹中相邻几帧（甚至相隔数百飞秒的帧）在构型空间高度自相关。如果用普通的 `train_test_split(..., shuffle=True)` 按帧随机划分：
- 验证/测试误差会被严重低估（仅测了“内插相邻帧”能力）；
- 测试模型对未见温度、未见表面覆盖度或新体系的泛化时，必须把 `group_id` 设为对应级别（如 `trajectory_id`、`adsorbate_id` 或 `system_id`）。

## 2. 分组防泄漏划分示例

```python
import numpy as np
from sklearn.model_selection import GroupShuffleSplit

# 1. 先按 group_id 划分出独立的 test 集，再从剩余中划分 val 与 train
gss_test = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=42)
trainval_idx, test_idx = next(gss_test.split(frames, groups=groups))

gss_val = GroupShuffleSplit(n_splits=1, test_size=0.15 / 0.85, random_state=42)
tr_rel, val_rel = next(gss_val.split([frames[i] for i in trainval_idx],
                                      groups=[groups[i] for i in trainval_idx]))
train_idx = trainval_idx[tr_rel]
val_idx = trainval_idx[val_rel]

# 必须验证 group_id 严格零泄漏
assert set(groups[i] for i in train_idx).isdisjoint(groups[i] for i in test_idx)
assert set(groups[i] for i in val_idx).isdisjoint(groups[i] for i in test_idx)
```

- 如果某些稀有构型族总组数极少（例如仅 1 条轨迹），可能无法同时出现在 `train`/`val`/`test` 三个集合中，应在 `dataset_summary.csv` 中如实报告该组的去向，不要复制同一帧来假造三集覆盖。

## 3. 保留旧划分的增量扩充原则

主动学习加入新标注批次时：
1. 读取已有 `split_index.csv`，提取所有已锁定的 `sample_id -> split` 和 `group_id -> split`。
2. 对新批次构型检查：
   - 若新样本来自已有 `test`/`val` 同源轨迹（同 `group_id`），**严禁直接放进 `train`**（否则导致测试集泄漏），应随原组归入或显式报告冲突请用户决策；
   - 若新样本与旧 `test`/`val` 构成几何重复（且物理状态一致），从新批次中剔除或保持同属原集。
3. 严禁为美化划分比例而悄悄移动原本属于 `test` 的样本。

## 4. 数据清洗与字段规范

- 检查孤立原子能量（`E0s`）或能量基准是否已明确：部分框架（如 MACE `config_type=IsolatedAtom`）支持直接在训练集中放置孤立原子帧，或在命令行传入 `E0s` 字典；不要在未记录基准的情况下混合不同原子能基准。
- 模型不需要的私有主机绝对路径不必写进 `extxyz` 的 `info` 行中，统一用逻辑 `sample_id` 关联到外部 `split_index.csv`。
