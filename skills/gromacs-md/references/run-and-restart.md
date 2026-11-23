# GROMACS Runs and Checkpoints

## Continue or Extend the Same Protocol

Resume a stage with its matching `.tpr` and complete `.cpt`. Check the step and time with `gmx dump -cp parent.cpt`. Verify the checkpoint exists because `mdrun -cpi` can start from the beginning when the input checkpoint is absent. Run the example from a new continuation directory with the parent segment as read-only input.

```bash
test -s ../parent/md.tpr && test -s ../parent/md.cpt && \
  gmx mdrun -s ../parent/md.tpr -cpi ../parent/md.cpt \
    -deffnm md_segment -cpo md_segment.cpt -noappend
```

- If the requested endpoint exceeds the original `.tpr`, run `gmx convert-tpr -s ../parent/md.tpr -extend 5000 -o extended.tpr`. This example adds 5000 ps. Start with `extended.tpr` and the same validated checkpoint.
- `-noappend` writes new log, energy, and trajectory files using GROMACS segment naming. Join by checkpoint step and physical time. If the parent outputs extend beyond the checkpoint, preserve the source files and omit the superseded interval and duplicate boundary frames from the joined result.
- The native `-append` option expects the complete parent outputs under their original names. If the engine rejects appending, use a new directory and `-noappend`. Additional hashes serve as provenance.

## Stage Changes Such as NPT → NVT

Verify the previous stage's final state, atom ordering, and box vectors. Supply the previous `.cpt` to `grompp -t` as the full-precision state. Use the chosen final box and `pcoupl=no` for NVT. To inherit velocities, set `gen-vel=no` and use `continuation=yes` when carrying existing constraints forward. Verify the coordinates, velocities, box, and time origin in the new `.tpr`.

```bash
gmx grompp -f nvt.mdp -c ../npt/npt.gro -t ../npt/npt.cpt \
  -p topol.top -o nvt.tpr -po mdout.mdp -pp processed.top
```

This workflow starts a new ensemble with the parent's coordinates and velocities. The new protocol determines thermostat and barostat state. Set `tinit` and `init-step` to start the new stage at zero or keep cumulative time. Checkpoint time and stage start time can differ. When changing only compatible parameters and retaining ensemble state, follow the installed version's instructions for also passing the checkpoint to `mdrun -cpi`, and verify time, step, and state fields. If starting from `.gro` alone, document velocity and state initialization.

## CPU/GPU Execution and Validation

- `gmx --version` shows the MPI, SIMD, threading, and GPU features. Compute-node builds may require CPU instruction sets unavailable on the login node. Use a compatible `grompp` for preprocessing and verify the `.tpr` with the runtime version. Use `-ntmpi` and `-ntomp` for thread-MPI, and the scheduler launcher for external MPI ranks. Use allocated GPUs and verify PP, PME, bonded, and update placement in `mdrun` logs. Tune against measured `ns/day`.
- `Finished mdrun` or a performance line confirms segment exit. Use `gmx dump -s run.tpr` to confirm `init-step`, `nsteps`, `dt`, and output intervals. Use `gmx check -f run.xtc` or check the TRR for frame count and actual coverage. Cross-check the last logged step, checkpoint, energies, and final structure at their respective output strides. After cascading LINCS warnings, runaway temperature, or corrupted geometry, return to a verified healthy checkpoint.
- Keep the `.tpr` that matches the trajectory for analysis. To rebuild a static structure from `.gro` and `.top`, retain the full recursive include tree and active macros. Spot-check atom count, ordering, units, and first and last frame times.

## Official References

[Managing Long Simulations and Restarts](https://manual.gromacs.org/current/user-guide/managing-simulations.html) · [mdrun](https://manual.gromacs.org/current/onlinehelp/gmx-mdrun.html) · [convert-tpr](https://manual.gromacs.org/current/onlinehelp/gmx-convert-tpr.html) · [dump](https://manual.gromacs.org/current/onlinehelp/gmx-dump.html)
