---
name: orca-calculations
description: "Prepare and audit molecular ORCA geometry optimizations, vibrational frequencies, single points and solvent calculations. Use for ORCA inputs, GBW restarts, imaginary-mode diagnosis, and same-geometry wavefunction handoff to ESP/RESP fitting."
---
# ORCA Molecular Calculations

Prepare molecular optimizations, vibrational frequency calculations, and single points in ORCA. Choose gas phase or implicit solvent for the task. Run stages independently as needed. When combining thermochemical results or exporting an ESP wavefunction, record the geometry, electronic state, and level of theory for each stage.

## Configure the Calculation

1. Check the geometry source, atom order, charge, multiplicity, and target stationary point. For low-valent species, radicals, or heavy elements, also check occupations, spin state, ECP, and valence basis.
2. Specify the functional, dispersion correction, orbital and auxiliary bases, integration grid, SCF, and solvent model for each stage. Use separate directories for `Opt/Freq`, `SP`, and retries. Record why any basis or solvent changed.
3. Check the ORCA version and MPI runtime against the executable and environment setup. Launch the ORCA driver once by absolute path so it can start the parallel modules. Match `%pal nprocs` to the process allocation and leave memory headroom above `%maxcore` in MB per process. Use the resources and submission authorization specified for the task.

## Validate and Deliver

- **Optimization.** Check `THE OPTIMIZATION HAS CONVERGED`, the final coordinates, and connectivity. `ORCA TERMINATED NORMALLY` confirms program termination.
- **Frequencies.** Check that the final frequency block is complete and identify rigid translations and rotations, physical vibrations, and numerical low-frequency modes. Inspect significant imaginary modes for minima. For a transition state, verify the imaginary mode and the reactant and product it connects. See [Staged Calculations and Validation](references/staged-calculations.md) for diagnosing modes and reoptimizing.
- **Single points.** Verify SCF convergence for the intended final calculation, `FINAL SINGLE POINT ENERGY`, normal termination, and nonempty outputs. For ESP fitting, export and reread the wavefunction from the same single point, checking elements, order, coordinates, and electronic state.
- **Restarts.** Start in a separate directory from a complete, physically valid geometry. Use a compatible `.gbw` for an orbital guess and the corresponding `.hess` for second derivatives or an initial Hessian. Record the files, which were actually read, and any changes.
- **Deliverables.** Keep `.inp`, input and final `.xyz`, `.out`, relevant `.gbw`, `.hess`, and wavefunction exports, plus the calculation settings. Use `$molecular-parameterization` for RESP grids, constrained fits, and force-field atom mappings.
