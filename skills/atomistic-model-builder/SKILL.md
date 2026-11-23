---
name: atomistic-model-builder
description: "Build molecules, crystals, slabs, adsorption structures, solvated cells and ion variants with ASE and Packmol. Use for geometry construction, PBC checks, FixAtoms constraints and atom mapping; force-field fitting and production MD belong to separate skills."
---
# Atomistic Model Building

Use ASE and optionally Packmol to build molecules, bulk crystals, slabs, adsorption structures, solvent boxes, and structures with ions or proton defects. Record coordinates, cells, periodic boundary conditions (PBC), fixed layers, and atom mappings. This skill covers geometry construction and validation.

## Before You Start

- **Composition and boundaries.** Confirm the formula, total charge, protonation state, and PBC. Use `pbc=(True, True, True)` for a 3D-periodic slab with vacuum. For a model periodic only in `xy`, use `pbc=(True, True, False)` and verify that the simulation engine and electrostatics solver support those boundaries.
- **Surface parameters.** For interfaces, record the source bulk structure, `(hkl)` plane, in-plane supercell, layer count, termination, fixed-layer criterion (layer or z threshold), and vacuum thickness (often 15–20 Å).
- **Solvent and ions.** For systems with liquid, specify the target region (surface-relative or whole-box), density or particle count, minimum separation (for example, $d_{\min} \ge 1.5\text{–}2.0\,\text{\AA}$), and random seed.

## Workflow

### 1. Build the Reference Structure

- **Bulk and surfaces.** Start from a verified experimental CIF or an optimized bulk cell. Use `ase.build.surface`, `fcc111`, or `make_supercell` to build the slab and add vacuum with `slab.center(vacuum=15.0, axis=2)`.
- **Adsorption geometries.** Place adsorbates with `add_adsorbate` or `rotate` and `translate`. Keep site labels such as `top`, `bridge`, and `fcc`, along with orientation labels.
- **Fixed layers.** Use layer `tags` or a geometry rule such as `z < z_cutoff` to construct `FixAtoms`. Derive indices from the current structure.

```python
from ase.build import fcc111, add_adsorbate
from ase.constraints import FixAtoms

slab = fcc111("Pt", size=(4, 4, 4), vacuum=15.0)
# Identify the bottom two layers from z coordinates or layer tags.
z_layers = sorted(set(round(z, 2) for z in slab.positions[:, 2]))
z_fix_max = z_layers[1] + 0.2
slab.set_constraint(FixAtoms(mask=slab.positions[:, 2] <= z_fix_max))
```

### 2. Add Solvent, Ions, or Defects

- **Solvent loading.** Estimate the initial molecule count from the accessible volume $V_{\text{free}}$ after subtracting the volume excluded by the surface and solutes.
  $$N_{\text{sol}} \approx \frac{\rho \cdot V_{\text{free}}\,(\text{\AA}^3) \cdot 10^{-24} \cdot N_A}{M\,(\text{g/mol})}$$
  For ambient pure water ($\rho \approx 1.0\,\text{g/cm}^3, M = 18.015\,\text{g/mol}$), this is about $0.0334\,\text{molecules/\AA}^3$.
- **Packmol placement.** Inset the placement box by half the `tolerance`, for example from `z_min + 1.0` to `z_max - 1.0`, to avoid overlaps between periodic images when packing with nonperiodic boundaries.
- **Proton and ion variants.** When adding or removing atoms, for example converting $\text{H}_2\text{O}$ to $\text{OH}^-$ or $\text{H}_3\text{O}^+$, record changes in stoichiometry, expected net charge, and electron count for downstream DFT or MD.

### 3. Map and Group Atoms

Assign stable role labels to all atoms, such as `slab`, `adsorbate`, `solvent`, or `ion`, and export `atom_mapping.csv`. When reordering, deleting, or joining atoms, retain the mapping from original to output indices.

| Column | Meaning |
|---|---|
| `new_index` | Zero-based atom index in the output |
| `source_id` | Source structure identifier |
| `orig_index` | Zero-based index in the source (`-1` for newly added atoms) |
| `element` | Element symbol |
| `role` | Atom role (`slab` / `adsorbate` / `solvent` / `ion`) |
| `fixed` | Whether the atom is fixed (`True` / `False`) |

### 4. Validate the Written Structure

Read the output back. Verify atom counts and cell geometry, and use minimum-image convention (MIC) distances to detect contacts across periodic boundaries.

```python
import numpy as np
from ase.io import read

atoms = read("model.extxyz")
dists = atoms.get_all_distances(mic=True)
np.fill_diagonal(dists, np.inf)
min_d = dists.min()
i, j = np.unravel_index(np.argmin(dists), dists.shape)
print(f"natoms={len(atoms)}, min_mic_dist={min_d:.3f} A ({atoms[i].symbol}{i}-{atoms[j].symbol}{j})")
assert np.all(np.isfinite(atoms.positions)), "Coordinates contain NaN or Inf"
assert min_d > 0.85, f"Severely overlapping atom pair: {i}-{j} ({min_d:.3f} A)"
```

- Check intramolecular covalent bonds (for example, `O-H ~ 0.96–1.05 Å`) and nonbonded separations (commonly `> 1.5 Å`) separately.
- Label built or partially relaxed structures as `candidate` or `unrelaxed` until optimization converges.

## References

- See [Structure Building](references/geometry.md) for surface cuts, orthogonal supercells, adsorption-site deduplication, and Packmol.

## Deliverables and Validation

1. **Structure files** (`*.extxyz`, `POSCAR`, or `*.cif`) with cell, PBC, constraint, and structure metadata preserved as supported by the output format.
2. **`build.py`** with inputs, target parameters, random seeds, and output paths at the top.
3. **`atom_mapping.csv`** with complete atom indices and role assignments.
4. **`build_summary.json`** with the reference source, element counts, total atom count, net charge, constraint count, minimum MIC separation, and random seed.
