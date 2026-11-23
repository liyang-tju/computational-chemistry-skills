---
name: vasp-calculations
description: "Prepare and verify VASP inputs for single points, relaxations, AIMD, NEB/CI-NEB, dimer searches and finite-difference frequencies. Use for POTCAR/KPOINTS checks, compatible restarts, Bader charge and work-function outputs."
---
# VASP Calculation Setup

Prepare inputs and restarts for VASP single points, geometry optimization, AIMD, reaction paths, transition-state searches, and frequencies. Verify `POSCAR`, `POTCAR`, `INCAR`, `KPOINTS`, executable capabilities, and any required charge-density and electrostatic-potential outputs.

## Before Starting

- **Calculation mode**. Choose a single point, ionic or cell relaxation, AIMD, constrained dynamics, NEB or CI-NEB, Dimer, or frequencies. Use single points with the appropriate output for Bader charges and work functions.
- **Electronic protocol**. Specify the functional (such as PBE, RPBE, or HSE06), dispersion (`IVDW`), pseudopotential variants (such as `PAW_PBE` with `_pv`, `_sv`, or `_h`), `ENCUT`, `EDIFF`, `ISPIN`, and `NELECT` if charged.
- **System and boundaries**. Identify bulk, molecule, or slab. For a slab specify the vacuum direction, any `LDIPOL` and `IDIPOL` settings, and any implicit solvent such as VASPsol.
- **Runtime resources**. Identify the executable (`vasp_std`, `vasp_gam`, or `vasp_ncl`), MPI ranks, GPUs, and cluster-specific parallelization settings (`KPAR` and `NCORE`).

## Workflow

### 1. Check `POSCAR` and Assemble `POTCAR`

- Verify element order, total atom count, coordinate format (`Direct` or `Cartesian`), and `Selective dynamics` flags (`T/F`) in `POSCAR`.
- For ASE exports, check whether identical elements were split into multiple groups or reordered in a way that changes the expected `POTCAR` order.
- Concatenate `POTCAR` datasets in the species order on `POSCAR` line 6 and verify the result. Assemble licensed pseudopotentials locally in the calculation directory and keep their contents out of the shared skill repository.

```bash
# Verify that the species in POSCAR match the POTCAR TITEL entries in order.
sed -n '6,7p' POSCAR
grep -E "TITEL|ENMAX|ZVAL" POTCAR
```

### 2. Prepare `KPOINTS`

- Prefer VASPKIT task `102` to generate SCF `KPOINTS` using a copy of the target `POSCAR` in a separate preparation directory. Use `1` along the slab's vacuum direction and verify `1 1 1` for isolated molecules or Γ-only calculations.
- Use `vasp_gam` for Γ-only single points, optimizations, and AIMD when the electronic settings are supported by the real-valued build.
- Record the VASPKIT resolution and the resulting mesh. [Inputs and Runtime](references/inputs-runtime.md)

### 3. Write `INCAR` for the Calculation Mode

Group scientific and parallelization parameters in `INCAR`. Use the template and settings for the requested calculation. [Calculation Modes](references/modes.md)

- **Smearing (`ISMEAR` and `SIGMA`)**
  - The Cu(100) single-point, relaxation, and AIMD templates all use `ISMEAR = 0` and `SIGMA = 0.05`. For other metals, choose smearing based on the k-point mesh, occupations, and observable.
  - For molecules, semiconductors, insulators, and gas-phase references, use Gaussian smearing (`ISMEAR = 0`) with small `SIGMA = 0.02–0.05` to limit fractional-occupation errors.
- **Real-space projection (`LREAL`)**. Keep this setting consistent within each comparison series. The Cu(100) templates use `LREAL = Auto`. Validate any alternative against the system and target accuracy.
- **Net charge and electrochemistry**. Let $N_0=\sum_i N_i Z_{\mathrm{VAL},i}$ and express the net physical charge in elementary-charge units as $q/e$. Set `NELECT` to $N_0-q/e$ and specify the compensating background or implicit electrolyte.

### 4. Configure Parallelization and Check Restart Compatibility

- **Parallel settings**. Choose `KPAR` as a divisor of the total MPI rank count and distribute irreducible k points as evenly as possible. Set `NCORE` for the supported CPU or GPU layout.
- **Restarts**
  - Geometry. Copy a complete `CONTCAR` to `POSCAR` in a new directory. Check that the file is nonempty, the atom count matches, and `Selective dynamics` is retained.
  - Electronic state. `ISTART = 1` attempts to read compatible orbitals from `WAVECAR` and resets the basis for the current cell and `ENCUT`. `ICHARG = 1` can initialize charge from a compatible `CHGCAR`. Check compatibility of each file and confirm successful reads in `OUTCAR`. [Inputs and Runtime](references/inputs-runtime.md)

### 5. Check Inputs and Validate the Results

Use the following checks before submission.
```bash
# Check the four required inputs and match the POSCAR atom count to the coordinate rows.
ls -l INCAR POSCAR POTCAR KPOINTS
python3 -c '
from ase.io import read
a = read("POSCAR")
print("natoms:", len(a), "formula:", a.get_chemical_formula(), "pbc:", a.pbc)
'
```
After execution, check all three criteria.
1. Normal completion using `grep -q "General timing" OUTCAR`.
2. Electronic convergence at each ionic step. Check whether SCF iterations hit `NELM` as well as checking the exit code.
3. Ionic or MD completion, using the maximum force on mobile atoms versus `|EDIFFG|` or the actual number of `NSW` steps.

## References

- Shared Cu(100) settings, single points, geometry optimization, AIMD, constrained dynamics, NEB, Dimer, frequencies, Bader charges, and work functions. [Calculation Modes](references/modes.md)
- `POTCAR`, VASPKIT k-point generation, `GPU/MPI` settings, and restart compatibility. [Inputs and Runtime](references/inputs-runtime.md)

## Deliverables and Validation

- A separate calculation directory with `POSCAR`, `INCAR`, `KPOINTS`, locally assembled `POTCAR`, a job script, and `protocol_notes.md`.
- Use a new directory for a new protocol or restart and preserve the original inputs and logs.
