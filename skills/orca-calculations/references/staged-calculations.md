# ORCA Staged Calculations and Validation

## Templates for Optimization, Frequencies, and Single Points

These templates illustrate a neutral singlet in solution. Choose the functional, orbital and auxiliary bases, solvent model, charge, multiplicity, and parallel resources for the task.

Use `initial.xyz` in the optimization and frequency directory. `Freq` requests analytical frequencies. If the method or solvent combination lacks analytical frequencies, check the installed version before choosing `NumFreq`.

```text
! PBE0 D4 def2-SVP RIJCOSX def2/J Opt Freq TightSCF CPCM(Water)
%pal
  nprocs 4
end
%maxcore 2000
* xyzfile 0 1 initial.xyz
```

After verifying the optimization and frequencies, copy the converged XYZ to `optimized.xyz` in the single-point directory, preserving coordinates and atom order. Include `AIM` when the task requires ORCA's `.wfn` export.

```text
! PBE0 D4 def2-TZVP RIJCOSX def2/J TightSCF SP CPCM(Water) AIM
%pal
  nprocs 4
end
%maxcore 2000
* xyzfile 0 1 optimized.xyz
```

- Record orbital and auxiliary bases, ECPs, solvent models, and output energy definitions separately for each stage. If combining a single-point energy with thermochemical corrections at another level, identify the origin of ZPE, thermal enthalpy, and entropy. Check which solvent terms are already included in the reported energy.
- Run each stage in a new directory, for example `"$ORCA_EXE" optfreq.inp > optfreq.out 2>&1`, with `ORCA_EXE` set to its absolute path. Use the Open MPI version appropriate for the build, launch one ORCA driver, and reuse the scheduler binding strategy verified for that environment.
- `%maxcore` sets memory per process. ORCA recommends keeping `nprocs × maxcore` within about 75% of available memory. Actual peak usage depends on the modules. Use logs to distinguish measured runtime, wall-time requests, and memory limits.

## Frequency Checks and Recovery from Imaginary Modes

- Read the last `VIBRATIONAL FREQUENCIES` section and verify the geometry and `.hess` it describes. An unconstrained nonlinear molecule has `3N−6` vibrational modes, and a linear molecule has `3N−5`. Interpret partial Hessians and constrained optimizations in their active subspace.
- Significant imaginary modes can occur even after optimization converges and the program terminates normally. Inspect the mode to determine whether it reflects chemical rearrangement, internal rotation, or numerical noise. For a suspected saddle, make small displacements along both signs of the mode, then reoptimize and recompute frequencies in separate directories. For near-zero modes, check optimization thresholds, the integration grid, and the Hessian method.
- Use the following markers to help review each stage, then examine the full frequency table, SCF history, and final geometry.

```bash
rg -n 'THE OPTIMIZATION HAS CONVERGED|VIBRATIONAL FREQUENCIES|imaginary mode|ORCA TERMINATED NORMALLY' optfreq.out
rg -n 'SCF CONVERGED|FINAL SINGLE POINT ENERGY|ORCA TERMINATED NORMALLY' singlepoint.out
```

## Orbital Guesses, Conformer Searches, and RESP Handoff

- Isolate identically named `.gbw` files in separate stage directories. To reuse compatible orbitals on retry, specify `MOREAD` and `%moinp "previous.gbw"`. Check the basis, orbitals, electron count, and spin, and verify in the log that the file was read. Optimization history and Hessian data require their own restart files.
- If the starting conformer is uncertain, generate candidates from representative conformations using ORCA GOAT with a compatible xTB method. Check the ensemble, connectivity, and run status before reoptimizing and ranking candidates under a common protocol.
- Use the requested single-point wavefunction for ESP fitting. Read `singlepoint.wfn` from `AIM` or run the matching `orca_2mkl singlepoint -molden` to export Molden data from `singlepoint.gbw`. Read the export back with a supported downstream tool and check basis and ECP representation, coordinates, order, and charge.
- Include the wavefunction geometry, atom mapping, and total charge in the ESP/RESP handoff. Define equivalent atoms and fitting constraints for the current molecule and protocol.

## Official References

[ORCA Parallel Runs](https://www.faccts.de/docs/orca/6.1/manual/contents/essentialelements/parallel.html) · [Frequencies](https://www.faccts.de/docs/orca/6.1/manual/contents/structurereactivity/frequencies.html) · [Implicit Solvation](https://www.faccts.de/docs/orca/6.1/manual/contents/essentialelements/solvationmodels.html) · [GOAT](https://www.faccts.de/docs/orca/6.1/manual/contents/structurereactivity/goat.html) · [Utility Programs](https://www.faccts.de/docs/orca/6.1/manual/contents/utilitiesvisualization/utilities.html)
