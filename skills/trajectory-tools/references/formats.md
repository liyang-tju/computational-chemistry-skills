# Format Handling

## 1. VASP (`XDATCAR` / `OUTCAR` / `vasprun.xml`)

- **`XDATCAR` cells and steps**. In NPT (`ISIF=3`), `XDATCAR` writes the updated cell per frame. Fixed-cell runs (`ISIF=2`) write it once in the header. For older or unusual files read with ASE, check that cells for frames 1 and $N$ match the expected variable- or fixed-cell behavior. Use a complete `OUTCAR` or `vasprun.xml` when also reading energies or forces.
- **Recover time**. Get `POTIM` in fs and `NBLOCK` from `INCAR` or `OUTCAR` because `XDATCAR` omits both. Use `time = step * POTIM`.

## 2. CP2K (`*-pos-1.xyz` + `*-1.cell` + `*-1.ener`)

CP2K writes coordinates, cells, and energies to separate files. Different `&EACH` settings or interrupted writes can shift row alignment.

- **Align by step**. Parse `i = <step>, time = <t>` from the `.xyz` comment and match the integer step to the `.cell` `Step` column, or match time within a tolerance.

```python
import re
import numpy as np

# Build a step -> 3x3 cell_vectors (Å) mapping from the .cell file.
cell_by_step = {}
with open("proj-1.cell") as f:
    for line in f:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        step = int(parts[0])
        # CP2K .cell columns are Step, Time[fs], Ax, Ay, Az, Bx, By, Bz, Cx, Cy, Cz, Vol.
        vec = np.array([float(x) for x in parts[2:11]]).reshape(3, 3)
        cell_by_step[step] = vec
```

- **Fortran `D` exponents**. Older CP2K versions or auxiliary outputs may contain `1.234D-05`. For numeric preprocessing, replace matches of `r"([+-]?(?:\d+\.?\d*|\.\d+))[Dd]([+-]?\d+)"` with `\1E\2`. Restrict replacements to numeric fields to preserve element symbols such as `Dy` and comments.
- **Missing cells and partial frames**. Flag or exclude frames with no corresponding `.cell` entry. When an interruption leaves fewer than `natoms + 2` lines at the end of `*-pos-1.xyz`, exclude the partial frame and truncate the parsed segment at the last complete `restart` step.

## 3. LAMMPS (`dump` / `lammpstrj` + `data`)

- **Element mapping**. For a dump with integer `type` only, supply `specorder` or a map such as `{1: "Pt", 2: "O", 3: "H"}`. Sort by atom `id` or let `ase.io.read(..., format="lammps-dump-text", specorder=...)` do so.
- **Coordinate representation and periodic wrapping**. Check the `ITEM: ATOMS` columns.
  - `x y z` gives wrapped Cartesian coordinates.
  - `xs ys zs` gives fractional coordinates (`[0, 1]`).
  - `xu yu zu` gives already unwrapped coordinates. Use them directly.
  - With `ix iy iz` image flags, reconstruct continuous coordinates with the cell matrix as needed for diffusion.
- **Triclinic cells**. `ITEM: BOX BOUNDS xy xz yz` reports `xlo_bound xhi_bound` containing tilt offsets. Let ASE or MDAnalysis handle the bounds.

## 4. GROMACS (`.xtc` / `.trr` + `.gro` / `.tpr`)

- `.xtc` and `.trr` trajectories require a `.gro`, `.pdb`, or `.tpr` companion for elements and topology.
- **Units**. GROMACS uses **nm** and **ps**, with forces in kJ/mol/nm and energies in kJ/mol. ASE uses **Å** and **eV**. Verify coordinate and cell conversions when combining `MDAnalysis` (default Å) and `mdtraj` (default nm).

## 5. ASE `extxyz` Constraints and Visualization

- ASE commonly serializes `FixAtoms` as Boolean `move_mask` columns and reconstructs it in `atoms.constraints` on reading. Verify equivalent constraint behavior.
- For batch visualization checks, verify parsing and inspect rendered structures when visual validation is required.
