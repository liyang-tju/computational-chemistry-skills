# 描述符与选择

## 1. QUESTS 与局部环境覆盖

- 使用 QUESTS（如 `quests.descriptor` + `quests.compression.msc`）时，先确认当前安装版本的 API 参数：
  - 典型参数：`k`（近邻数）、`cutoff`（截断半径，Å）、核带宽 `bandwidth`（若需拟合带宽，显式记录拟合所用的候选子集与样本量）。
- QUESTS 的优势在于直接在**局部原子环境集合**上评估信息覆盖度，能捕捉少量活性位点上的关键变化，避免被大量体相水分子或底层金属原子的均值池化稀释。

## 2. MACE 描述符提取与聚合陷阱

通过 `mace.calculators.MACECalculator`（或 `mace_mp` / 本地训练模型）提取原子特征时，必须记录：
1. 模型标识（如 `medium-mpa-0` 或本地检查点名称）；
2. `invariants_only=True`（仅标量不变量，适合旋转不变几何聚类）或 `False`；
3. `num_layers`（通常默认全部交互层拼接）。

- **均值池化陷阱**：对包含 150 个水分子和 2 个吸附反应物的界面，整帧所有原子取平均会掩盖反应位点差异。更合理的做法是：
  - **按角色掩码池化**（仅对吸附物 + 表层活性原子做特征聚合），或
  - 先基于逐原子局部环境距离做覆盖筛选。

## 3. 最远点采样（FPS）参考实现

在得到每帧定长特征向量矩阵 $X \in \mathbb{R}^{N \times D}$ 后，可执行确定性 FPS：

```python
import numpy as np

def farthest_point_sampling(features: np.ndarray, n_select: int, seed: int = 0) -> list[int]:
    """基于欧氏距离的贪心最远点采样。"""
    n_total = len(features)
    if n_select >= n_total:
        return list(range(n_total))
    rng = np.random.default_rng(seed)
    first_idx = int(rng.integers(0, n_total))
    selected = [first_idx]
    min_dists = np.linalg.norm(features - features[first_idx], axis=1)
    for _ in range(1, n_select):
        next_idx = int(np.argmax(min_dists))
        selected.append(next_idx)
        d = np.linalg.norm(features - features[next_idx], axis=1)
        min_dists = np.minimum(min_dists, d)
    return selected
```

## 4. 配额、近似与验证检查

- **配额策略**：
  - 按温度/电势/组分均衡覆盖（如每电势各选 50 帧）时，应分别在各分组内部运行选择，同时可把已选主集作为初始种子避免跨组重复。
- **候选池 vs 测试集**：在未标注候选池上拟合特征标准化或带宽，仅属于无监督覆盖建模，不涉及测试标签泄漏；但仍建议把预留给最终模型评测的独立验证轨迹完全隔离在候选池之外。
- **验收断言**：
  ```python
  assert len(selected_ids) == len(set(selected_ids)), "选中结果存在重复索引"
  assert len(selected_ids) <= len(candidates), "选中数不能超过候选总数"
  ```
