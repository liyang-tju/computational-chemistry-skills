---
name: constant-potential-calculations
description: "Prepare and analyze constant-potential electrochemical simulations across fixed-charge NELECT scans, VASPsol++/SOLHYBRID, CP-VASP (LCEP/NESCHEME), TPOT, i-PI+VASP (implicit or Ne counter-electrode), CPTI, LAMMPS electrode/conp, CP-MACE and field-dipole corrections."
---
# Constant-Potential Calculations

Set up and analyze constant-potential simulations of electrochemical solid–liquid interfaces. Methods include implicit-solvent charge scans and quadratic fits, native constant potential in VASPsol++, CP-VASP, SOLHYBRID+TPOT, i-PI+VASP with implicit solvent or a Ne counter electrode, CPTI, LAMMPS `ELECTRODE`, and CP-MACE.

## Before Starting

- **Target potential and reference scale**. Specify the target $U$ (`V vs SHE`, `V vs RHE`, or `V vs PZC`). Calibrate the absolute SHE Fermi-energy reference $E_{F,\text{ref}}^{\text{SHE}}$ for the functional, pseudopotentials, and solvent model in use (typical examples range from `-4.44` to `-4.66` eV). For $U_{\text{vs PZC}}$, determine the neutral reference $E_F(\Delta N_e=0)$ for the same interface.
- **Physical model and simulation engine**
  - Choose pure implicit solvent (VASPsol or VASPsol++), mixed explicit and implicit solvent (`SOLHYBRID`), explicit solvent with a virtual Ne counter electrode, classical polarizable electrodes (LAMMPS `ELECTRODE`), or a machine-learning potential (`FermiMACE`).
  - Verify capabilities in the available executable, such as CP-VASP `LCEP`, VASPsol++ `ISOL=2`, `SOLHYBRID`, `TPOT`, or the `i-pi` socket interface with `IBRION=24`.
- **Task stage**. Identify whether the task is a static single point, structure or transition-state optimization (IS, FS, CI-NEB, or Dimer), constant-potential MD (CP-AIMD or classical MD), or data extraction for constant-potential model training and simulation.

## Method Selection

| Method | Control mechanism | Applications | Advantages | Limitations and checks |
|---|---|---|---|---|
| **Charge scan and quadratic fit or ASE FCP** | Scan fixed `NELECT` values or find the target with an outer root solver. Apply the Legendre transform to obtain $\Omega(U)$. | Static adsorption energies, barriers, IS/TS/FS potential curves, and PZC calibration | Runs with standard VASPsol or VASPsol++ | Costs $N$ single points. A single fitted curve cannot extrapolate across nonadiabatic proton-transfer frames. |
| **Native VASPsol++ constant potential** | `ISOL=2` and `EFERMI_ref` adjust screening charge `q_sol` in the SCF loop | Single points, static optimization, CI-NEB, and Dimer | Directly obtains a converged structure and grand potential at the target potential | Check for omitted partial-core-density (`DENCOR`) shape forces. The output already includes the $-\Delta N_e\mu_e$ term. |
| **CP-VASP (`LCEP`)** | `NESCHEME=1–5` updates `NELECT` by capacitance iteration or an electronic NHC thermostat | Constant-potential optimization and CP-AIMD, especially grand-canonical MD with `NESCHEME=5` | Supports explicit-water CP-AIMD, variable time steps, and thermostat coupling | `NESCHEME=3` is costly. Verify the energy convention for `GCE`, which includes zero-temperature entropy extrapolation. |
| **SOLHYBRID + TPOT** | `LSOLHYBRID` excludes implicit solvent from gaps in explicit water. `LTPOT` adjusts `NELECT` using the vacuum plateau. | AIMD of large explicit-water and metal double layers | `METHOD_SH=1/2` isolates the explicit layer. `TPOTTRUEVACLEVEL` uses the vacuum plateau. | Match `CORE_C` to element order, restart with `UPDATED NELECT`, and register keywords in ASE. |
| **i-PI + VASP (implicit solvent or Ne layer)** | VASP `IBRION=24` connects over a socket to `i-pi` `<electrons>` for charge evolution | Faster constant-potential dynamics or replacement of the implicit electrolyte with a Ne layer | `solvation_update_stride` reduces implicit solves. `Ne_doping` bypasses them. | The Ne layer calibrates relative bias. Verify that the reference window lies on a flat vacuum plateau. |
| **CPTI (constant-potential thermodynamic integration)** | Sample restrained slow-growth trajectories and iteratively correct `NELECT` in each window using Bader surface charge and capacitance | Constant-potential barriers in explicit solvent from mean-force integration | Approximates constant potential along the reaction coordinate with fixed-charge AIMD | Depends on the surface-atom partition, linear capacitance, and repeated iterations. |
| **LAMMPS `ELECTRODE`** | `fix electrode/conp` and `pppm/electrode` solve for Gaussian electrode charges during MD | Double-layer structure, capacitance, and diffusion | Controls the potential difference between two electrodes in long simulations | Match boundaries and charge constraints to slab or finite-field mode. |
| **CP-MACE / FermiMACE** | Train a neural potential with `potential` and excess `electron` labels and drive it with ASE | Nanosecond reactive constant-potential MD and enhanced sampling with PLUMED | Combines reactive modeling with low computational cost | Sensitive to the baseline electron count in the labels. Restrict predictions to the covered potential range. |

## Workflow

### 1. Set Reference Energies, Signs, and Base Settings

- **Net charge and excess electrons**. Compute the neutral valence count $N_0=\sum_i N_i Z_{\text{val},i}$ from the `ZVAL` values in the actual `POTCAR`. Define $\Delta N_e=N_e-N_0$. Then $\Delta N_e>0$ means electron injection, and the physical charge is $q=-e\Delta N_e$, where $e>0$ is the elementary charge.
- **Potential scale conversion**
  $$U_{\text{SHE}} = (E_{F,\text{ref}}^{\text{SHE}} - \mu_e)/e, \qquad \mu_e = E_F + \text{FERMI\_SHIFT} \quad (\text{or } E_F - E_{\text{vac}})$$
  - `EFERMI_ref` (`TARGETMU` in CP-VASP) uses a negative electron-energy reference, for example `-4.66 - U_SHE`. TPOT `TPOTVTARGET` and i-PI `target_workfunction` use the positive work-function scale ($= -\mu_e$).
  - When using the same interface at zero charge as reference, $U_{\text{vs PZC}}=[\mu_e(0)-\mu_e(\Delta N_e)]/e$. Align both chemical potentials with the same reference method. A difference in eV gives the corresponding numerical potential in V. Compare reaction states on a common potential scale.
- **Compatible switches**. With implicit solvent (`LSOL = .TRUE.`), disable dipole correction (`LDIPOL = .FALSE.`) and remove `IDIPOL` and `DIPOL`. Consider dipole correction only for a pure vacuum or explicit-water/vacuum model where the actual vacuum plateau is needed.

### 2. Follow the Selected Method

Use the relevant reference for parameters and scripts.
- See [Charge Scans and Implicit Constant Potential](references/implicit-and-charge-scan.md) for static charge scans, ASE FCP, native VASPsol++, CPTI, and partial-core force checks.
- See [Constant-Potential Dynamics and Mixed Solvents](references/cp-aimd-and-hybrid.md) for CP-VASP (`LCEP`), SOLHYBRID+TPOT, and i-PI with `IBRION=24` or a Ne counter electrode.
- See [Classical Electrodes and CP-MACE](references/classical-and-cp-mlp.md) for LAMMPS `electrode/conp` and CP-MACE or FermiMACE training and dynamics.

### 3. Check Both Convergence Criteria and Force–Energy Consistency

Check the electronic state and chemical potential alongside the exit code and `EDIFF`.
1. **SCF and chemical potential**. Confirm convergence within `NELM` and a difference between the Fermi level and target chemical potential within `FERMICONVERGE`, `EFERMI_tol`, or `TPOTVDIFF`.
2. **Active model switches**. Verify that `OUTCAR` or the log reports the requested modules and settings, such as `ISOL=2`, `LSOLHYBRID`, `LTPOT`, and `LCEP`. An unpatched executable may silently ignore a keyword.
3. **VASPsol++ force check**. For a new element or pseudopotential combination, use the central finite-difference check in [Charge Scans and Implicit Constant Potential](references/implicit-and-charge-scan.md) on a representative surface adsorption site before optimization, NEB, or AIMD. Check for significant errors from omitted partial-core-density (`DENCOR`) shape forces.

### 4. Use a Consistent Grand-Potential Convention

Before computing $\Omega(U) = E - \Delta N_e \cdot \mu_e$, verify whether the reported energy already includes the electron-reservoir term.
- Standard fixed-`NELECT` calculations (VASPsol or `ISOL=2` without `EFERMI_ref`) report $E(\Delta N_e)$. Subtract $\Delta N_e \cdot \mu_e$ in post-processing.
- VASPsol++ with `EFERMI_ref < 0` includes `-q_sol * EFERMI_ref` internally. Use the corresponding output energy directly as the grand potential.
- For `TPOTGCENERGY = .TRUE.` and the CP-VASP `GCE` field, verify inclusion of $\Delta N_e \mu_e$ and the entropy extrapolation convention (`TOTEN` or `sigma->0`). Compare methods only under the same thermodynamic definition.

### 5. Restart Runs and Export Training Data

- **Continuation**. For `TPOT`, update `NELECT` in the new `INCAR` from the last `UPDATED NELECT` in the previous `OUTCAR`. For `CP-VASP` and `LAMMPS electrode/conp`, verify the `restart` step and charge balance. Continue in a new directory and preserve the previous segment.
- **CP-MACE extraction**. For mixed compositions, use excess electrons $\Delta N_e=N_e-N_0$ for `electron` and the same $\mu_e$ reference for `potential`. Fixed compositions can use total electrons. Match signs and reference baselines across training, export, and dynamics.

## References

- See [Charge Scans and Implicit Constant Potential](references/implicit-and-charge-scan.md) for `NELECT` fits, ASE `FCP`, VASPsol++ `EFERMI_ref`, CPTI, and finite-difference shape-force checks.
- See [Constant-Potential Dynamics and Mixed Solvents](references/cp-aimd-and-hybrid.md) for CP-VASP `NESCHEME`, `SOLHYBRID+TPOT`, and implicit-solvent or Ne-layer `i-PI`.
- See [Classical Electrodes and CP-MACE](references/classical-and-cp-mlp.md) for LAMMPS `fix electrode/conp` and `FermiMACE` training and ASE dynamics.

## Upstream Repositories

| Method or component | Repository |
|---|---|
| VASPsol / VASPsol++（`ISOL=1/2`、`EFERMI_ref`） | [henniggroup/VASPsol](https://github.com/henniggroup/VASPsol) · [VASPsol/VASPsol](https://github.com/VASPsol/VASPsol) |
| ASE `FCP` constant-potential calculator | [hellozhaoming/FCP-vasp-ase](https://github.com/hellozhaoming/FCP-vasp-ase) |
| CP-VASP（`LCEP` / `NESCHEME 1–5`） | [yuanyue-liu-group/CP-VASP](https://github.com/yuanyue-liu-group/CP-VASP) |
| SOLHYBRID mixed solvent and TPOT control | [comet-group/VASPsol](https://github.com/comet-group/VASPsol) · [comet-group/tpot](https://github.com/comet-group/tpot) |
| i-PI constant-potential extension (`IBRION=24` / `Ne_doping`) | [zhangchenyu-USTC/i-pi_constant-potential](https://github.com/zhangchenyu-USTC/i-pi_constant-potential) · [i-pi/i-pi](https://github.com/i-pi/i-pi) |
| CPTI constant-potential thermodynamic integration | [Yanggang-Wang-Group/CPTI](https://github.com/Yanggang-Wang-Group/CPTI) |
| LAMMPS `ELECTRODE`（`fix electrode/conp`） | [lammps/lammps](https://github.com/lammps/lammps) |
| CP-MACE / FermiMACE | [yuanyue-liu-group/CP-MACE](https://github.com/yuanyue-liu-group/CP-MACE) · [ACEsuit/mace](https://github.com/ACEsuit/mace) |

## Deliverables and Validation

1. **Inputs and run protocol** with the complete calculation directory (`INCAR`, `input.lammps`, or `input.xml`), the calibration reference ($E_{F,\text{ref}}^{\text{SHE}}$ or PZC), the $\Delta N_e$ sign, and the energy convention.
2. **Structured results** such as `charge_results.csv`, `quadratic_fits.csv`, `grand_potential_curve.csv`, or `extxyz` labeled with `potential` and `electron`.
3. **Validation** of SCF and target potential or electrode charge neutrality for all states, physically consistent quadratic curvature and $R^2$, and application of the electron-reservoir term exactly once.
