# 格式适配

## 1. VASP (`XDATCAR` / `OUTCAR` / `vasprun.xml`)

- **`XDATCAR` 变胞与步号**：NPT（`ISIF=3`）的 `XDATCAR` 每帧都会写出新晶胞，而固定晶胞（`ISIF=2`）只在文件头写一次晶胞。用 ASE 读取旧版或特殊格式 `XDATCAR` 时，务必回读验证第 1 帧和第 $N$ 帧晶胞是否与预期（变胞 vs 固定）一致；如需同时读取能量/力，优先读取完整的 `OUTCAR` 或 `vasprun.xml`。
- **时间还原**：`XDATCAR` 本身不包含时间步 `POTIM` 与输出间隔 `NBLOCK`，必须从同目录 `INCAR`/`OUTCAR` 读出 `POTIM`（fs）与 `NBLOCK` 后计算 `time = step * POTIM`。

## 2. CP2K (`*-pos-1.xyz` + `*-1.cell` + `*-1.ener`)

CP2K 轨迹默认把坐标、晶胞和能量分开存放，且不同 `&EACH` 频率或崩溃中断会导致行号不对应。

- **按步号精确对齐**：从 `.xyz` 注释行解析 `i = <step>, time = <t>`，以整数 `step`（或容差匹配 `time`）对齐 `.cell` 的 `Step` 列：

```python
import re
import numpy as np

# 读取 .cell 文件建立 step -> 3x3 cell_vectors (Å)
cell_by_step = {}
with open("proj-1.cell") as f:
    for line in f:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        step = int(parts[0])
        # CP2K .cell 列顺序: Step, Time[fs], Ax, Ay, Az, Bx, By, Bz, Cx, Cy, Cz, Vol
        vec = np.array([float(x) for x in parts[2:11]]).reshape(3, 3)
        cell_by_step[step] = vec
```

- **Fortran `D` 科学计数法**：旧版 CP2K 或部分辅助输出可能出现 `1.234D-05`；若需预处理数字，仅对数字正则 `r"([+-]?(?:\d+\.?\d*|\.\d+))[Dd]([+-]?\d+)"` 替换为 `\1E\2`，切勿全文件暴力替换 `D`，以免误伤元素 `Dy` 或注释文本。
- **缺失晶胞与尾半帧处理**：若某步在 `.cell` 中缺失，应显式记录缺失或剔除该帧，不要静默前向填充；异常中断导致 `*-pos-1.xyz` 末尾残留不足 `natoms + 2` 行的半帧时，应在解析阶段截断丢弃至最后一个完整 `restart` 步号。

## 3. LAMMPS (`dump` / `lammpstrj` + `data`)

- **元素映射**：若 dump 仅含 `type` 整数列，需传入 `specorder` 或映射字典（如 `{1: "Pt", 2: "O", 3: "H"}`）；确保按原子 `id` 排序（或用 `ase.io.read(..., format="lammps-dump-text", specorder=...)` 自动按 id 排序）。
- **坐标类型与周期包裹**：检查 dump `ITEM: ATOMS` 列头：
  - `x y z`：包裹后的笛卡尔坐标；
  - `xs ys zs`：分数坐标（`[0, 1]`）；
  - `xu yu zu`：已解包（unwrapped）坐标（不能再做一次周期解包！）；
  - 若带 `ix iy iz` image flags，可根据需要结合晶胞矩阵还原连续轨迹用于扩散分析。
- **三斜盒（Triclinic Box）**：`ITEM: BOX BOUNDS xy xz yz` 给出的 `xlo_bound xhi_bound` 含倾斜偏移量（与正交盒不同），建议直接交由 ASE/MDAnalysis 解析而非手工硬切边界值。

## 4. GROMACS (`.xtc` / `.trr` + `.gro` / `.tpr`)

- 压缩轨迹 `.xtc`/`.trr` 不含元素/拓扑，需配合 `.gro`/`.pdb`/`.tpr` 读取。
- **单位陷阱**：GROMACS 原生单位为 **nm** 与 **ps**（力和能量用 kJ/mol/nm 与 kJ/mol），而 ASE 默认 **Å** 与 **eV**；使用 `MDAnalysis`（默认 Å）与 `mdtraj`（默认 nm）混用时务必核对坐标与盒长量纲。

## 5. ASE `extxyz` 约束与可视化

- `FixAtoms` 写出到 `extxyz` 时常以 `move_mask` 布尔数组序列化到原子列中，读回时 ASE 自动还原为 `atoms.constraints` 中的 `FixAtoms`；验证时检查 `atoms.constraints` 行为等价即可。
- 涉及大批量可视化核查时，区分“解析无报错”与“人工查看图像渲染无异常”，不将前者替代后者。
