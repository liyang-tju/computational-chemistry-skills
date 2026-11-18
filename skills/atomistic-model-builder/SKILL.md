---
name: atomistic-model-builder
description: "Build molecules, crystals, slabs, adsorption structures, solvated cells and ion variants with ASE and Packmol. Use for geometry construction, PBC checks, FixAtoms constraints and atom mapping; force-field fitting and production MD belong to separate skills."
---
# 原子模型构建

使用 ASE（及可选 Packmol）构建分子、块体、表面 slab、吸附体系、溶剂盒与离子/质子缺陷变体，确保坐标、晶胞、周期性边界条件（PBC）、固定层约束及原子映射可追溯。本技能只负责几何构建与结构检查，不包含力场参数化或生产模拟。

## 开始前确认

- **体系组成与边界**：化学式、总电荷、质子化状态、PBC（三维周期 `pbc=True` 或二维 slab `pbc=(True, True, True)` + 真空层）。
- **表面参数**（若为界面）：参考体相来源、晶面 `(hkl)`、面内超胞、原子层数、终端面（termination）、固定层判据（按层/z 阈值）及真空厚度（常见 15–20 Å）。
- **溶剂与离子**（若含液相）：目标区间（相对表面高度还是全盒）、目标密度或粒子数、最小安全间距（如 $d_{\min} \ge 1.5\text{–}2.0\,\text{\AA}$）及随机种子。

## 工作流程

### 1. 构建参考结构与基础几何

- **体相/表面**：优先从核实过的实验 CIF 或已优化体相晶胞出发，使用 `ase.build.surface` / `fcc111` / `make_supercell` 切割并加真空层（`slab.center(vacuum=15.0, axis=2)`）。
- **吸附构型**：用 `add_adsorbate` 或旋转平移（`rotate`/`translate`）放置吸附质，保留位点名称（如 `top` / `bridge` / `fcc`）和取向标签。
- **固定层约束**：按原子层 `tags` 或几何高度规则（如 `z < z_cutoff`）生成 `FixAtoms`，避免直接硬编码另一体系的原子索引。

```python
from ase.build import fcc111, add_adsorbate
from ase.constraints import FixAtoms

slab = fcc111("Pt", size=(4, 4, 4), vacuum=15.0)
# 按底两层固定（依据 z 坐标聚类或 tag，而非猜测索引）
z_layers = sorted(set(round(z, 2) for z in slab.positions[:, 2]))
z_fix_max = z_layers[1] + 0.2
slab.set_constraint(FixAtoms(mask=slab.positions[:, 2] <= z_fix_max))
```

### 2. 添加溶剂、离子或缺陷

- **估算溶剂分子数**：按**可及自由体积** $V_{\text{free}}$（扣除表面/溶质排除体积）估算初始分子数，不要直接用整个模拟盒体积估算：
  $$N_{\text{sol}} \approx \frac{\rho \cdot V_{\text{free}}\,(\text{\AA}^3) \cdot 10^{-24} \cdot N_A}{M\,(\text{g/mol})}$$
  对常温纯水（$\rho \approx 1.0\,\text{g/cm}^3, M = 18.015\,\text{g/mol}$），约合 $0.0334\,\text{molecules/\AA}^3$。
- **Packmol 填充**：将放置盒子向内缩进半个 `tolerance`（如 `z_min + 1.0` 到 `z_max - 1.0`），避免 Packmol 在非周期边界放入分子后跨周期边界发生原子重叠。
- **质子/离子变体**：新增或删除原子（如 $\text{H}_2\text{O} \to \text{OH}^-$ 或 $\text{H}_3\text{O}^+$）时，同步记录化学计量变化、预期总电荷与电子数（供下游 DFT/MD 使用）。

### 3. 建立原子映射与逻辑分组

为所有原子记录稳定的分组标签（如 `slab`、`adsorbate`、`solvent`、`ion`），导出 `atom_mapping.csv`。对于发生重排、删减或拼接的结构，必须保留原始索引到新索引的映射：

| 列名 | 含义 |
|---|---|
| `new_index` | 输出结构中的 0-based 原子序号 |
| `source_id` | 来源结构标识 |
| `orig_index` | 原结构中的 0-based 序号（新建为 `-1`） |
| `element` | 元素符号 |
| `role` | 逻辑角色（`slab` / `adsorbate` / `solvent` / `ion`） |
| `fixed` | 是否被约束固定（`True` / `False`） |

### 4. 数值结构自检（必须执行）

写出结构后必须重新读回并用 **最小像距（MIC）** 检查跨周期边界接触、原子数和晶胞合法性：

```python
import numpy as np
from ase.io import read

atoms = read("model.extxyz")
dists = atoms.get_all_distances(mic=True)
np.fill_diagonal(dists, np.inf)
min_d = dists.min()
i, j = np.unravel_index(np.argmin(dists), dists.shape)
print(f"natoms={len(atoms)}, min_mic_dist={min_d:.3f} A ({atoms[i].symbol}{i}-{atoms[j].symbol}{j})")
assert np.all(np.isfinite(atoms.positions)), "存在 NaN/Inf 坐标"
assert min_d > 0.85, f"发现严重重叠原子对: {i}-{j} ({min_d:.3f} A)"
```

- 分子内部共价键（如 `O-H ~ 0.96–1.05 Å`）与非键最小距离（通常要求 `> 1.5 Å`）应分别检查。
- 对仅完成几何构建或预松弛（未收敛）的结构，标记为 `candidate` / `unrelaxed`，不能标记为已优化。

## 按需参考

- 表面切割、正交化陷阱、吸附位点去重及 Packmol 细节：阅读 [结构构建要点](references/geometry.md)。

## 交付产物与验收

1. **结构文件**：`*.extxyz` / `POSCAR` / `*.cif`（含完整 `cell`、`pbc`、`constraints` 及 `info` 元数据）。
2. **`build.py`**：顶部集中配置输入、目标参数、随机种子与输出路径，可直接复现。
3. **`atom_mapping.csv`**：完整原子索引与角色映射表。
4. **`build_summary.json`**：记录参考来源、元素计数、总原子数、净电荷、约束数量、最小 MIC 间距及随机种子。
