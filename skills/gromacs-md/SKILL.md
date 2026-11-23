---
name: gromacs-md
description: "Prepare GROMACS classical MD from GRO, TOP/ITP, MDP and NDX files. Use for grompp, energy minimization, NVT/NPT, bulk and solid-liquid interfaces, CPU/GPU mdrun settings, checkpoint continuation and run validation."
---
# GROMACS Molecular Dynamics

Prepare energy minimization, equilibration, production, or continuation from existing coordinates and a force-field topology. Supported systems include bulk solutions, nanomaterial–solvent interfaces, and interfaces with polymers or gases.

## Prepare the Inputs

1. Keep `topol.top`, the recursively included `.itp` files and `.ff` directories, the matching `.gro`, stage-specific `.mdp` files, and any `.ndx`. Check the expanded `[ molecules ]` ordering, coordinate atom order, charge, types, constraints, water model, and cross-group nonbonded terms. Identify the source of missing parameters before running `gmx grompp`.
2. Set boundaries and the stage protocol first. An isotropic NPT stage is suitable for a homogeneous liquid. A solid–liquid interface with fixed in-plane area can use normal pressure control or NVT at a specified film thickness. Set normal boundaries, electrostatics, and pressure control explicitly for systems with vacuum or a gas–liquid interface. See [Topology and Stage Inputs](references/preparation.md).
3. Generate each `.tpr` in a separate stage directory. Save the preprocessed topology and `mdout.mdp` and check each `grompp` warning for the installed version. Convert output intervals from physical time to steps and determine whether velocities and forces are needed.

## Run, Continue, and Validate

- Before the first run, check `gmx --version`, allocation, and CPU/GPU build. Configure ranks, threads, and GPU task assignments using [Runs and Checkpoints](references/run-and-restart.md). Verify actual offload from the runtime log.
- For a **stage change** such as NPT → NVT, generate a new `.tpr` from a new `.mdp`. For a **same-protocol continuation**, restore state from `.cpt`. Preserve the parent segment and checkpoints, and join by step number and physical time.
- For minimization, check `Fmax` against `emtol`. For MD, verify the final step, time, trajectory coverage, energy, and temperature. For NPT, also check box vectors, pressure, and density. Diagnose persistent LINCS errors, nonfinite energies, and constraint failures before resuming.
- Deliver reproducible inputs, output names, and stage notes, together with matched `.tpr`, `.log`, `.edr`, `.cpt`, final `.gro`, and trajectory. Use `$trajectory-tools` or `$trajectory-analysis` for conversion or observables.
