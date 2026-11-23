# Structure Building

## 1. Crystals and Surfaces

### Supercells and Orthogonal Cells
- `ase.build.surface(bulk, indices, layers, vacuum)` can produce oblique slab vectors. Some facets, such as fcc `(111)` and hcp `(0001)`, admit orthogonal supercells. A compact orthogonal cell may be unavailable for a general `(hkl)` facet.
- When constructing an orthogonal cell with `fcc111(..., orthogonal=True)` or a matrix passed to `ase.build.make_supercell`, check the following.
  1. The supercell area and number of atoms per layer are integer multiples of the corresponding primitive-cell quantities.
  2. The lattice vectors form a right-handed basis ($\det(\mathbf{A}) > 0$).
  3. Molecular connectivity and the intended surface reconstruction are preserved across periodic boundaries.

### Fixed-Layer Selection
Recompute `FixAtoms(indices=[...])` for each system using geometric criteria or atom tags.
```python
# Group atoms by z coordinate and fix the bottom n_fix layers.
import numpy as np
from ase.constraints import FixAtoms

z = atoms.positions[:, 2]
layer_tol = 0.4  # Å, adjust for the layer spacing
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

### Adsorption Sites and Conformer Deduplication
- For batches of sites generated using `pymatgen` `AdsorbateSiteFinder` or an ASE grid scan, record `site_type`, `orientation`, and `conformer_id`.
- Identify duplicate starting structures by heavy-atom RMSD after minimum-image alignment, for example `rmsd < 0.2 Å` with matching element-specific coordination fingerprints. Preserve distinct isomers even if their fractional coordinates or relaxed energies are close.

## 2. Solvent and Ion Placement

### Packmol Boundary Tolerance
Packmol uses nonperiodic placement by default. With `inside box 0. 0. 0. Lx Ly Lz`, atoms near opposite edges can overlap after imposing PBC. A common approach is to inset the placement region by at least `tol / 2`, typically `1.0–1.5 Å`.

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

- To fill a layer of thickness `H_sol` above the surface and leave vacuum, derive the bounds from `z_slab_top`, the highest surface-atom $z$ coordinate. Use `[z_slab_top + d_gap, z_slab_top + d_gap + H_sol]`.
- For two interfaces or two exposed slab faces, account for the accessible space between the lower surface's exclusion region and the upper surface's periodic image.

### Ions and Proton Defects
- For counterions such as $\text{K}^+$, $\text{Na}^+$, and $\text{ClO}_4^-$, search for sites satisfying the prescribed clearances, for example $\ge 2.5\,\text{\AA}$ from surface metal and $\ge 2.0\,\text{\AA}$ from other solutes or ions.
- Allow ions to relax in all directions by default. Use `FixedLine` or `FixCartesian` for studies that explicitly require fixed height or in-plane motion.
- When forming $\text{H}_3\text{O}^+$ or $\text{OH}^-$ from water, record the modified molecule index, added or removed H indices, net charge, and the required `NELECT` (VASP) or `CHARGE` (CP2K).

## 3. Starting Structures and Reproducibility

- **Controlled comparisons.** When comparing adsorbates or potentials at the same interface, retain the substrate geometry, initial water structure, and build seed. Record `reference_model_id` and the parameters that changed.
- **Independent replicas.** Generate separate starting structures with different Packmol `seed` values, or extract frames separated by sufficient relaxation time from an equilibrated trajectory and assign velocities independently.
