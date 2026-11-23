# Stage 4. Training, Exported-Model Evaluation, and MD Validation

See the training package and the variable-charge or constant-potential extension. [MACE](https://github.com/ACEsuit/mace) · [CP-MACE](https://github.com/yuanyue-liu-group/CP-MACE)

## 1. Training Data and Leakage-Aware Validation

- **Selected and active-learning data**. If stage 2 already used time separation such as `>= 0.15 ps`, geometry deduplication, and role-resolved FPS, and stage 5 used comparable deduplication and time separation, train directly with the SCF-validated `labeled.extxyz` or `merged_labeled.extxyz`. Verify consistent isolated-atom `E0s` and finite `REF_energy` and `REF_forces` using `apply_constraint=False` for force extraction.
- **Training, validation, and held-out tests**
  - During active-learning iterations, use a proportional `train / val` split to maximize coverage and monitor `val` convergence.
  - To test generalization to unseen trajectories, temperatures, or sizes, hold out entire trajectories or conditions by `group_id` in a fixed `test.extxyz`. Keep nearby frames from the same source in one split.
- **Electronic states**. For fixed-electron or neutral DFT, geometric deduplication is sufficient. For varying `NELECT` or `potential` in `CP-MACE` or `FermiMACE`, use `$constant-potential-calculations` to align `potential` and excess electrons $\Delta N_e$.

## 2. Independent Committee Training Runs

Train several models with the same architecture and different seeds, for example `1, 2, 7, 42`.
- **Check the installed CLI**. Run `mace_run_train --help` to verify available options and confirm CPU or GPU DDP thread and node placement.
- **Use the same protocol for all seeds**.
  - Match `--energy_key`, `--forces_key`, and `--stress_key`, for example `REF_energy` and `REF_forces`.
  - Match the `E0s` convention, such as explicit DFT isolated-atom values or `average`, and the loss weights, including Stage Two and SWA.
- **Separate directories and run records**. Use an independent directory and initial model state for each `--seed`. At the end write `training_summary.csv` with `seed`, job ID, `epochs_completed`, best `checkpoint_epoch`, `valid_energy_rmse_meV_per_atom`, `valid_force_rmse_meV_per_A`, exported `.model`, and log location.

## 3. Evaluate Exported Models

Load the final exported `.model` with `MACECalculator` and run inference on representative frames or a test set before deployment. Confirm whether TorchScript or LAMMPS export is needed and supported.

```python
import numpy as np
from ase.io import read
from mace.calculators import MACECalculator

calc = MACECalculator(model_paths="model_seed_1.model", device="cpu", default_dtype="float64")
frames = read("test_or_val.extxyz", index=":20")

energy_absolute_errors = []
force_squared_error = 0.0
force_components = 0
for atoms in frames:
    ref_e = atoms.info["REF_energy"]
    ref_f = atoms.arrays["REF_forces"]
    probe = atoms.copy()
    probe.calc = calc
    pred_e = probe.get_potential_energy()
    pred_f = probe.get_forces(apply_constraint=False)
    energy_absolute_errors.append(abs(pred_e - ref_e) / len(atoms))
    force_error = pred_f - ref_f
    force_squared_error += np.sum(force_error ** 2)
    force_components += force_error.size

energy_mae = 1000.0 * np.mean(energy_absolute_errors)
force_rmse = 1000.0 * np.sqrt(force_squared_error / force_components)
print(f"E_MAE = {energy_mae:.2f} meV/atom, F_RMSE = {force_rmse:.2f} meV/Å")
```

For force-error outliers, check the stage 3 `review.csv` flags and whether the frame contains rare coordination outside training coverage.

## 4. Short NVE and NVT Stability Checks

Before deploying a committee for roughly 500 ps of enhanced sampling, such as OPES-Explore, test representative initial structures and system sizes. Clear stale calculators with `atoms.calc = None` and keep `FixAtoms`.
- **NVE energy conservation**. Run 2–5 ps at a small time step such as `0.5 fs`. Check total energy for monotonic drift or jumps and compute kinetic temperature from mobile degrees of freedom when using `FixAtoms`.
- **NVT structural checks**. Confirm that the surface, adsorbate, and solvent stay physically intact, with no atomic overlap (`min_mic_dist >= 0.75 Å`).
