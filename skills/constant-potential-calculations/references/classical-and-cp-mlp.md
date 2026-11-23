# Classical Constant-Potential Electrodes and CP-MACE

## 1. Classical Constant-Potential MD in LAMMPS (`ELECTRODE`)

The `ELECTRODE` package is built into upstream LAMMPS and supports long-timescale MD of nanoscale interfaces with explicit electrolytes, ionic liquids, or zwitterions. [lammps/lammps](https://github.com/lammps/lammps)

```lammps
boundary        p p f
pair_modify     mix arithmetic
kspace_style    pppm/electrode 1.0e-5
kspace_modify   slab 3.0 order 5 mesh 40 40 135   # Fix and record the mesh for benchmarking and reproducibility

group           mobile subtract all all_electrode
fix             freeze all_electrode setforce 0.0 0.0 0.0
compute         mobile_temp mobile temp

# Use VLOWER and VUPPER for the lower and upper electrodes. ETA is the inverse Gaussian charge width.
fix             conp elec_lower electrode/conp ${VLOWER} ${ETA} couple elec_upper ${VUPPER} algo mat_inv symm on etypes on ffield off
fix             nvt_mobile mobile nvt temp 300.0 300.0 100.0
fix_modify      nvt_mobile temp mobile_temp
```

### Settings and Validation
1. **Group temperatures and velocities**. With fixed electrode positions, use `mobile_temp` for thermostat feedback and temperature output. It excludes the fixed electrode degrees of freedom from the temperature calculation.
2. Sum each electrode's charge with `compute property/atom q` and `compute reduce sum`. `f_conp[1]` and `f_conp[2]` report potentials in fix electrode order. `symm on` constrains total electrode charge to zero, leaving the potential difference as the independent control variable. For an electrolyte with net charge, check the whole-cell charge and use `symm off` with `qtotal` if the model requires electrode compensation.
3. The example uses a `p p f` slab with `ffield off`. For finite-field `ffield on`, use a z-periodic cell as required by the installed version and check the potential difference and long-range solver settings.
4. With `read_restart`, redeclare `kspace_style pppm/electrode`, `kspace_modify`, `fix freeze`, `fix conp`, and `fix nvt_mobile`. After changing MPI layout, perform a short test of the electrode groups, charge constraint, and temperature.

## 2. CP-MACE / FermiMACE Training and Constant-Potential Dynamics

See the CP-MACE implementation and its upstream MACE project. [yuanyue-liu-group/CP-MACE](https://github.com/yuanyue-liu-group/CP-MACE) · [ACEsuit/mace](https://github.com/ACEsuit/mace)

### Data Preparation and Electron Counts
For `extxyz` training sets extracted from CP-VASP or SOLHYBRID+TPOT, retain positions, cells, `REF_energy`, and `REF_forces`. Include these values in each frame's `info` line.
- `potential` is the frame's actual electron chemical potential $\mu_e$ in eV. Use one energy reference for all samples.
- `electron` preferably stores excess electrons $\Delta N_e=N_e-\sum_i N_i Z_{\text{val},i}$, especially across compositions or sizes. For fixed composition, total electrons are also suitable if the training and dynamics share that baseline. When computing $\Delta N_e$, check `valence_map` against the DFT `POTCAR` `ZVAL`. Convert physical charge with $\Delta N_e=-q/e$.

### Training Settings
For branches that learn the Fermi level or potential, such as `FermiMACE`, specify the additional loss weight and error metrics explicitly.
```bash
mace_run_train \
  --model="FermiMACE" \
  --loss="fermi_weighted" \
  --error_table="Fermi_PerAtomRMSE" \
  --energy_key="REF_energy" \
  --forces_key="REF_forces" \
  --energy_weight=1.0 \
  --forces_weight=100.0 \
  --potential_weight=10.0
```
- Follow `$mlp-workflow` for splitting by trajectory or condition `group_id` to prevent leakage. Evaluate energy, forces, and `potential` on an independent test set.

### ASE Constant-Potential Dynamics
Use these settings with `ConstantPotentialNoseHoover` driving `FermiMACE` or a single-point `Vasp` `solhybrid` calculator.
- **Initial state**. Set `atoms.info["electron"]` using the convention shared by training and dynamics. For example, use `0.0` for an initially neutral system with the $\Delta N_e$ convention. Specify `targetmu` (electron chemical potential in eV), fictitious electron mass `Mne`, and electronic Nosé–Hoover chain length `eta_length`.
- **Committee uncertainty**. When running models from several seeds in parallel (`AverageForceCalculator`), record per-atom force disagreement `force_std` and chemical-potential disagreement `mu_std`. Screen frames above the calibrated `force_threshold` or `fermi_threshold` for structural failures before sending them for active-learning DFT labeling.
