# 结构构建要点

## 1. 晶体与表面构建

### 超胞与正交化
- `ase.build.surface(bulk, indices, layers, vacuum)` 得到的晶格默认保留原始斜交基矢；部分晶面（如 fcc `(111)`、hcp `(0001)`）可构造正交超胞，但并不是所有 `(hkl)` 面都存在小体积正交胞。
- 需要正交化时（如使用 `fcc111(..., orthogonal=True)` 或 `ase.build.make_supercell` 矩阵变换），变换后必须检查：
  1. 新超胞面积与层间原子数是否为原胞的整数倍；
  2. 晶格矢量手性为右手系（$\det(\mathbf{A}) > 0$），避免部分程序报错；
  3. 周期边界上未出现断裂的多原子分子或表面重构缺失。

### 固定层选择
不要把旧文件的 `FixAtoms(indices=[...])` 直接复制到新体系。统一采用几何或标签规则：
```python
# 示例：按 z 坐标分层聚类后固定最底层 n_fix 层
import numpy as np
from ase.constraints import FixAtoms

z = atoms.positions[:, 2]
layer_tol = 0.4  # Å，视体系层间距调整
order = np.argsort(z)
layers = []
for idx in order:
    if not layers or z[idx] - z[layers[-1][-1]] > layer_tol:
        layers.append([idx])
    else:
        layers[-1].append(idx)

fixed_indices = [idx for layer in layers[:2] for idx in layer]
atoms.set_constraint(FixAtoms(indices=fixed_indices))
```

### 吸附位点与构象去重
- 批量枚举吸附位点（如用 `pymatgen` `AdsorbateSiteFinder` 或 ASE 网格扫描）时，保留 `site_type`、`orientation`、`conformer_id`。
- 判断初始构型是否重复时，应使用**周期性最小像距对齐后的重原子 RMSD**（如 `rmsd < 0.2 Å` 且元素配位指纹相同），不要仅凭晶格分数坐标接近或优化后能量接近就合并不同异构体。

## 2. 溶剂盒与离子放置

### Packmol 边界容差写法
Packmol 默认在非周期盒内排布分子。若直接指定 `inside box 0. 0. 0. Lx Ly Lz`，盒子边缘放置的原子可能与周期镜像发生重叠。通用做法是将放置区间向内缩进至少 `tol / 2`（通常取 `1.0–1.5 Å`）：

```text
tolerance 2.0
filetype xyz
output solvated_box.xyz

structure slab.xyz
  number 1
  fixed 0. 0. 0. 0. 0. 0.
end structure

structure water.xyz
  number 64
  inside box 1.0 1.0 <z_slab_top + 2.0> <Lx - 1.0> <Ly - 1.0> <Lz - 1.0>
end structure
```

- 若希望溶剂只填充至表面上方指定厚度 `H_sol`（保留上方真空），应以 `z_slab_top`（表面最高原子 $z$ 坐标）动态计算上下限：`[z_slab_top + d_gap, z_slab_top + d_gap + H_sol]`，不要硬编码绝对 $z$ 数值。
- 若存在双界面或上下双表面，需考虑下表面底部的排除区与顶面镜像之间的实际可及区间。

### 离子与质子缺陷
- 插入反离子（如 $\text{K}^+$、$\text{Na}^+$、$\text{ClO}_4^-$）时，按预设距离区间搜索无碰撞位点（如距离表面金属 $\ge 2.5\,\text{\AA}$，距离其他溶质/离子 $\ge 2.0\,\text{\AA}$）。
- 仅在实验明确研究恒定高度约束或面内扩散时，才对离子施加 `FixedLine` 或 `FixCartesian` 约束；默认应让离子全自由度弛豫。
- 由水生成 $\text{H}_3\text{O}^+$ / $\text{OH}^-$ 时，明确记录：变更的分子索引、新增/删除的 H 原子索引、新净电荷，以及后续电子结构计算所需的 `NELECT`（VASP）或 `CHARGE`（CP2K）。

## 3. 多初态与可重复性

- **受控比较**（例如对比不同吸附物或不同电势下的同一界面）：保留相同的基底几何、水分子初始构型及构建随机种子，并在元数据中记录 `reference_model_id` 与实际改变的参数。
- **独立重复采样（Replicas）**：不要把同一个构建构型简单复制 3 份当作独立重复。若需多个独立初态，应使用不同的 Packmol `seed` 重新生成，或从预平衡轨迹中相隔足够弛豫时间的不同帧抽取并分别重新赋速。
