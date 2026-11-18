---
name: trajectory-tools
description: "Convert, inspect, extract and join VASP, CP2K, LAMMPS, GROMACS and extxyz trajectories using ASE while preserving cell, PBC, step/time metadata and atom provenance. Use for trajectory I/O and preprocessing; statistical observables belong to trajectory-analysis."
---
# 轨迹整理与转换

将来自 VASP、CP2K、LAMMPS、GROMACS 等引擎的结构与轨迹整理为标准化分析或标注输入（优先采用 ASE `extxyz`），完整保留晶胞、PBC、原子身份、步号/时间及来源索引。本技能负责格式转换、清洗、抽帧和分段拼接；统计观测量交由 `$trajectory-analysis`。

## 开始前确认

- **输入源与伴随文件**：轨迹文件及其必需的拓扑/晶胞/时间伴随文件（如 CP2K 的 `.cell` 与 `.ener`、LAMMPS 的 `data` 或 `type->element` 映射、GROMACS 的 `.gro`/`.tpr`、VASP 的 `POSCAR`/`INCAR` `POTIM`）。
- **目标用途**：
  1. **保留标签的数据集**（留存能量、力、应力）；
  2. **待 DFT 标注结构**（剥离旧预测能量/力，保留电子态与约束）；
  3. **MD 新初态**（明确是否清除速度，保留晶胞与约束）。

## 工作流程

### 1. 盘点格式与物理信息

不能只看文件扩展名。先检查第一帧与配套日志，核对：
- 原子总数与元素顺序（LAMMPS dump 若无 `element` 列，必须提供整数 `type -> element` 映射）；
- 晶胞是否随时间变化（NPT/变胞轨迹绝对不能整条沿用首帧晶胞）；
- 时间步长与输出间隔（计算 `time = simulation_step * dt`，区分 `frame_index` 与 `simulation_step`；缺少时间信息时保留 `None`/`NaN`，不凭帧数猜时长）。

### 2. 流式读取与完整性检验

对大轨迹使用 `ase.io.iread` 流式迭代，避免一次性爆内存，同时捕获异常截断尾帧并校验坐标有限性：

```python
import numpy as np
from ase.io import iread

frames = []
broken_tail = False
it = iread("traj.xyz", index=":")
for idx, atoms in enumerate(it):
    try:
        if not np.all(np.isfinite(atoms.positions)):
            raise ValueError(f"Frame {idx} contains NaN/Inf positions")
        frames.append(atoms)
    except Exception as exc:
        print(f"Stopped at frame {idx}: {exc}")
        broken_tail = True
        break
```

### 3. 抽帧、分段拼接与去重

- **按步号/时间抽帧**：按明确的时间窗或间隔抽取（如每 `stride` ps），导出 `frame_index.csv` 记录每一帧的 `source_id`、`source_frame`、`simulation_step` 与 `time`。
- **拼接续算段**：依据 `$simulation-audit-restart` 确定的检查点边界 `checkpoint_step` 截断父段尾部，再衔接子段 `step > checkpoint_step`；若需合并多条独立重复（replicas），必须保留 `replica_id` 列，不能拼成假连续时间轴。

### 4. 按目标用途处理标签与状态（仅在新副本操作）

写出前按需求决定保留或剥离哪些字段（详见 [数据表示与元数据](references/metadata.md)）：
- 清理 ASE 旧计算器缓存务必使用 `atoms.calc = None`，并同步清理不再适用的 `atoms.info`（如 `energy`, `free_energy`, `stress`）与 `atoms.arrays`（如 `forces`, `momenta`）。

### 5. 写出并回读抽检

写出 `extxyz` 等目标格式后，必须重新读回代表帧（首帧、中帧、末帧）核对原子数、元素顺序、晶胞、PBC 与约束语义（如 `FixAtoms`）未损坏：

```python
from ase.io import read, write

write("out.extxyz", frames, format="extxyz")
check_first = read("out.extxyz", index=0)
check_last = read("out.extxyz", index=-1)
assert len(check_first) == len(frames[0])
assert check_first.get_chemical_symbols() == frames[0].get_chemical_symbols()
assert np.allclose(check_first.cell.array, frames[0].cell.array)
```

## 按需参考

- VASP / CP2K / LAMMPS / GROMACS / `extxyz` 格式边界与解析技巧：阅读 [格式适配](references/formats.md)。
- `frame_index.csv` 字段、标签清理代码与状态保留规则：阅读 [数据表示与元数据](references/metadata.md)。

## 交付产物与验收

1. 转换后的结构/轨迹文件（如 `*.extxyz`）。
2. **`frame_index.csv`**：每帧对应 `source_id, relative_path, source_frame, simulation_step, time, time_unit, segment_id, replica_id`。
3. **`conversion.json`**：记录源文件列表、类型映射、截断/去重统计及回读校验结果。
