# 数据表示与元数据

## 1. `frame_index.csv` 推荐字段

保留相对数据集根路径与逻辑标识，便于跨主机和跨目录复用（本机绝对路径只另存局部运行日志）：

| 字段 | 说明 |
|---|---|
| `sample_id` | 全局唯一帧标识（如 `sysA_rep1_s005000`） |
| `source_id` | 原始计算段逻辑名 |
| `relative_path` | 相对数据源根目录的路径 |
| `source_frame` | 在源轨迹文件中的 0-based 帧索引 |
| `simulation_step` | 引擎原始步号（未知留空） |
| `time` | 物理时间（未知留空） |
| `time_unit` | `fs` 或 `ps` |
| `segment_id` | 续算分段号（如 `seg01`, `seg02`） |
| `replica_id` | 独立重复编号（如 `rep01`） |

## 2. 按下游任务清理与保留字段

在**新副本**上按场景显式清理不需要的旧状态：

| 目标用途 | 保留字段 | 必须清理/重置的字段 |
|---|---|---|
| **带标签 MLP 数据** | 几何、晶胞、PBC、可靠参考 `energy`/`forces`/`stress`、协议版本 `protocol_id` | 无关中间缓存 |
| **待 DFT 标注结构** | 几何、晶胞、PBC、`FixAtoms` 约束、预期 `charge`/`NELECT`/`spin`、`sample_id` | `atoms.calc = None`、旧预测 `energy`/`free_energy`/`forces`/`stress`、`momenta` |
| **子体系抽取**（如裁剪溶剂/吸附质） | 裁剪后的几何、晶胞、新原子映射 | **必须删除**原完整体系的标量总能量与原子旧索引信息 |
| **MD 初态** | 几何、晶胞、PBC、约束；仅连续重启时保留 `momenta`/速度 | 新初始化时清空 `momenta` 与旧 `energy`/`forces` |

```python
def sanitize_for_dft_labeling(atoms):
    """在副本上清除旧预测能量、力和动量，但保留几何、晶胞与 FixAtoms 约束。"""
    clean = atoms.copy()
    clean.calc = None
    for key in ("energy", "free_energy", "stress", "virial"):
        clean.info.pop(key, None)
    for arr_key in ("forces", "force", "momenta"):
        clean.arrays.pop(arr_key, None)
    return clean
```

- 清理前后务必检查 `len(clean) == len(atoms)`、`clean.get_chemical_symbols() == atoms.get_chemical_symbols()` 且约束数量一致。
- 绝不能为了让解析器通过而凭空猜填缺失晶胞、`PBC` 或原子顺序。
