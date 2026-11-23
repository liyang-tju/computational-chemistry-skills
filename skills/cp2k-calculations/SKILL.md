---
name: cp2k-calculations
description: "Prepare CP2K Quickstep inputs for ENERGY_FORCE, GEO_OPT, CELL_OPT and NVT/NPT AIMD, including Poisson periodicity, OT/diagonalization SCF and EXT_RESTART continuations."
---
# CP2K Calculation Setup

Prepare runnable CP2K Quickstep inputs for single points (`ENERGY_FORCE`), optimization (`GEO_OPT` or `CELL_OPT`), and molecular dynamics (`MD`). Verify basis and pseudopotential files, grid accuracy, Poisson and periodicity settings, SCF strategy, and restart boundaries.

## Before Starting

- **Run type**. Select `RUN_TYPE` (`ENERGY_FORCE`, `GEO_OPT`, `CELL_OPT`, or `MD`).
- **System and electronic state**. Specify the structure (XYZ or CIF), cell parameters `ABC` and `ALPHA_BETA_GAMMA`, net `CHARGE`, spin `MULTIPLICITY`, and whether to use unrestricted spin (`UKS`).
- **Boundary conditions**. Choose three-dimensional bulk or solution (`PERIODIC XYZ`), a two-dimensional slab (`PERIODIC XY` with a suitable Poisson solver), or an isolated molecule (`PERIODIC NONE`).
- **Runtime environment**. Locate the CP2K executable, such as `cp2k.psmp` or `cp2k.ssmp`, and verify `CP2K_DATA_DIR` or local basis and pseudopotential files such as `BASIS_MOLOPT`, `GTH_POTENTIALS`, and `dftd3.dat`.

## Workflow

### 1. Locate CP2K and Its Data Files

Use read-only checks to confirm the target CP2K version and locate its data files from the run configuration or `CP2K_DATA_DIR`. Keep shared skill documentation portable.

```bash
command -v cp2k.psmp cp2k.ssmp || true
cp2k.psmp --version | head -n 5
```

Verify that the files referenced by `BASIS_SET_FILE_NAME`, `POTENTIAL_FILE_NAME`, and `PARAMETER_FILE_NAME` (such as DFT-D3 parameters) in `&DFT` are readable from the run directory.

### 2. Configure `&DFT` and `&SUBSYS`

- **Check each `&KIND`**. Define one entry for each element or custom atomic kind in the structure. Confirm that the referenced files contain the specific `BASIS_SET` (such as `DZVP-MOLOPT-SR-GTH`) and `POTENTIAL` (such as `GTH-PBE-q6`) and that the valence electron counts match the intended charge.
- **Grid and precision (`&MGRID` and `&QS`)**. Specify `CUTOFF` (such as 400–600 Ry, depending on the hardest pseudopotential), `REL_CUTOFF` (often 50–60 Ry), and `EPS_DEFAULT` (such as `1.0E-12`).
- **Periodicity and Poisson solver**. Match `PERIODIC` in `&SUBSYS/&CELL` and `&DFT/&POISSON`. Recheck both when changing the cell dimensions.
  - Three-dimensional systems use `PERIODIC XYZ` with the default periodic Poisson solver.
  - Two-dimensional slabs can usually use `&CELL PERIODIC XY`, `&POISSON PERIODIC XY`, and `POISSON_SOLVER ANALYTIC`. With `MT`, check that the nonperiodic cell dimension accommodates the full electron density and sufficient isolation. With `WAVELET`, verify which periodic directions the installed version supports (for example, CP2K 2024.1 requires `PERIODIC XZ` for two-dimensional `WAVELET`) and confirm that the density decays to zero at the nonperiodic boundary.
  - Isolated molecules use `PERIODIC NONE` with `POISSON_SOLVER MT` or `WAVELET`.

### 3. Choose an SCF Solver (`&SCF`)

- **Insulators, liquids, and other gapped systems**. For efficient time and memory use, prefer OT (`&OT ON` with `MINIMIZER DIIS` or `CG` and `PRECONDITIONER FULL_SINGLE_INVERSE`) and `&OUTER_SCF` (`EPS_SCF 1.0E-6`). OT requires integer occupations, so keep `&SMEAR` disabled.
- **Metals and small-gap systems**. Disable OT and use `&DIAGONALIZATION` with `&MIXING` (such as `BROYDEN_MIXING`), `&SMEAR` (`METHOD FERMI_DIRAC`, `ELECTRONIC_TEMP [K] 300`), and sufficient `ADDED_MOS`.

### 4. Configure `&MOTION` and Restarts (`&EXT_RESTART`)

- Specify `ENSEMBLE`, `STEPS`, `TIMESTEP [fs]`, `TEMPERATURE [K]`, and `&THERMOSTAT` (such as `TYPE CSVR` and `TIMECON [fs] 50`) explicitly in `&MD`.
- For continuation or a change in temperature or ensemble, set `RESTART_POS`, `RESTART_VEL`, `RESTART_CELL`, `RESTART_THERMOSTAT`, and `RESTART_COUNTERS` in `&EXT_RESTART` as described in [Dynamics and Restarts](references/md-restart.md). Check that the step number, start time, and wavefunction guess (`SCF_GUESS RESTART`) agree.

### 5. Align Outputs and Check Input Syntax

- Set compatible `&PRINT` frequencies for `&TRAJECTORY`, `&VELOCITIES`, `&CELL`, and `&RESTART`. Use `Step` and `Time` to align trajectories, cells, and energies.
- Run CP2K's built-in input check before submission or execution to verify syntax and file accessibility.

```bash
cp2k.psmp -c input.inp
```

## Reference

- See [Dynamics and Restarts](references/md-restart.md) for an `MD` template, OT and diagonalization settings, `&EXT_RESTART` semantics, and step and time alignment.

## Deliverables and Validation

1. An independent run directory containing `input.inp`, any files referenced by `@INCLUDE`, the initial structure, and the job script.
2. A successful syntax check with `cp2k.psmp -c input.inp`.
3. After execution, verify the `PROGRAM ENDED AT` marker, SCF convergence within `MAX_SCF`, and attainment of the target step count or optimization criteria.
