---
name: solvation-energy
description: "Prepare and analyze frozen-fragment energy decompositions (AWS, WS, AS, S, A) from solvated trajectories or static geometries with strict geometry provenance, electronic-state matching and frame-wise completeness checks."
---
# Solvation Energies and Frozen-Fragment Analysis

Build fragments from a common frozen geometry or explicitly defined optimized geometries. Examples are the full interface `AWS`, water and surface `WS`, adsorbate and surface `AS`, bare surface `S`, and isolated adsorbate `A`. Prepare single points, verify all fragments per frame, and calculate energy decompositions. Interpret each formula in its defined ensemble. Equilibrium $\Delta G_{\text{solv}}$ also involves relaxation and entropy.

## Before Starting

- **Observable and decomposition**. Define the four-term frozen adsorption-energy correction $\Delta \Delta E_{\text{solv}} = [E(AWS) - E(WS)] - [E(AS) - E(S)]$ and any frozen adsorption energies that also use $E(A)$.
- **Geometry source**. Label frozen MD or AIMD snapshots, vacuum-optimized structures, and implicit-solvent-optimized structures by their origin.
- **Electronic protocol**. Choose fixed charge (neutral or specified `NELECT`) or constant potential with $\Omega = E - \mu_e \Delta N_e$. Check consistent functional, cutoff, k-point sampling, and pseudopotentials across fragments.

## Workflow

### 1. Extract Frames and Map Atom Roles

- Sample verified stable trajectories at a specified stride and record `sample_id`, `replica_id`, `simulation_step`, and `time`.
- Use the `slab`, `adsorbate`, and `solvent` mapping to check for unintended dissociation or proton escape. For proton transfer, classify the frame under the applicable rule, such as a post-reaction species group, and document any index reassignment.

### 2. Preserve the Geometry of Frozen Fragments

Extract `AWS`, `WS`, `AS`, `S`, and any required `A`, `W`, or `AW` with the original cell, PBC, and absolute positions.

```python
# Slice by role indices and retain the original positions without .center() or .wrap().
def extract_fragment(atoms, indices):
    frag = atoms[indices].copy()
    frag.calc = None
    frag.info.clear()
    return frag
```

For real-space charge-density or electrostatic-potential differences, use the same cell origin and grid for every fragment so values align point by point.

### 3. Define Fragment States and the Single-Point Protocol

- Specify total charge or `NELECT` and spin multiplicity for each fragment. [Energy Decomposition and References](references/decomposition.md)
- Prepare single-point inputs in separate chunks or directories and record `fragment_mapping.csv`. If the task calls for a full recalculation under a new protocol, rerun every fragment under that protocol.

### 4. Validate Complete Fragment Sets Before Combining Energies

Compute a difference only when all fragments for a `sample_id` have completed with converged SCF.
- Mark frames with missing fragments, such as an unconverged `WS`, as `incomplete`. Exclude them from the estimate and leave missing values such as `E(S)` or `E(WS)` unset.
- Use eV consistently and investigate outliers for incorrect spin states or charge oscillations.

### 5. Aggregate and Report Uncertainty

- Aggregate from frames to independent replicas and then to condition means. Account for autocorrelation and between-replica uncertainty.
- Align dipole, charge-transfer, or other electronic data frame by frame before correlation analysis. A correlation between condition means alone provides no evidence of frame-level causation.

## Reference

- See [Energy Decomposition and References](references/decomposition.md) for four- and five-term formulas, charged fragments, and statistics.

## Deliverables and Validation

1. **`fragment_mapping.csv`**：`sample_id, fragment_type, natoms, formula, charge_or_nelect, task_dir`。
2. **`energies_by_fragment.csv`** and **`decomposition_results.csv`** with fragment energies, convergence flags, and combined differences per frame.
3. **`sampling.json`** with the formula, geometry categories, protocol ID, effective sample count, and missing-frame statistics.
