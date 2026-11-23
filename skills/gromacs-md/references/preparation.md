# GROMACS Topology and Stage Inputs

## Coordinates, Topology, and Preprocessing

- Order coordinates by molecule and atom order in the expanded `[ molecules ]`. `.gro` uses nm, the MD time step uses ps, energy uses kJ/mol, and pressure uses bar. When converting LAMMPS or ASE inputs, also verify angle force constants, LJ mixing, 1–4 scaling, and the cell.
- Preserve the inclusion order for `[ defaults ]`, `[ atomtypes ]`, supplemental bonded terms, and molecule definitions. Check the water model, `[ pairs ]`, `[ exclusions ]`, and constraints in the active `define` branch. For parameters from different sources, record cross terms, compatibility, and the source of supplemental terms. The effect of `-DFLEXIBLE` depends on the topology's conditional branch.
- Generate the `.tpr` in a new stage directory and save the effective preprocessor outputs. For relative includes, preserve the directory layout in a copy or update the includes and search paths, then run `grompp` from the intended directory. Use `-n index.ndx` for custom groups and `-r restraint-reference.gro` for position restraints, and verify coordinate order.

```bash
gmx grompp -f stage.mdp -c system.gro -p topol.top \
  -o stage.tpr -po mdout.mdp -pp processed.top
```

Keep the default `grompp` warning limit. Fix mismatches and parameter problems, rerun preprocessing, and check molecule counts, atom counts, and the active topology branches. If an older run is missing parameter files, recover the original files or archived expanded topology for that stage and verify parameter sources. When preprocessing and running with different versions, confirm the final version reads the `.tpr`.

Verify the center-of-mass motion removal method and groups. In a periodic system, applying `comm-mode=Angular` only to a solid group can trigger warnings about angular removal with periodic boundaries and solvent outside the removal group. Record the warnings and original protocol for reproductions. For new runs, choose the method based on boundaries, mobile atoms, and the observables of interest.

## Choose Stages for the System

| System or stage | Protocol and applicability |
|---|---|
| Initial minimization | Use `integrator=steep`. Set `emtol` as the target maximum force. Record the atom with the largest force and the step count. Use a flexible topology branch where the force field specifies one and restore the intended water and bond constraints before MD. |
| Bulk or 3D liquid-filled systems | Generate velocities after minimization, run isotropic NPT, and switch to NVT if needed. With a solid present, verify that isotropic scaling suits the material model. |
| Liquid-filled solid–liquid interface with fixed in-plane area | For normal-only scaling, `pcoupltype=semiisotropic` takes parameters for xy and z in that order. Use zero xy compressibility to fix the in-plane area and choose z compressibility from the protocol. Verify box changes using `.edr` or framewise box vectors. |
| Specified film or solid–gas/gas–liquid interface | Use fixed-box NVT after minimization where appropriate. Define the film and vacuum thickness, periodic topology, and long-range electrostatics. For slab correction, check the box and normal-axis requirements of `ewald-geometry=3dc` and evaluate image effects. Avoid normal bulk pressure coupling to equilibrate density in a direction containing vacuum. |

Frozen coordinates, position restraints, and bond constraints describe distinct models. Enable `freezegrps`, `freezedim`, or position restraints according to the model and check thermostat degrees of freedom, pressure coupling, and `refcoord_scaling`. Preserve substrate, solvent, and mobile atom definitions. In fixed-charge models, keep charge parameters fixed.

## Velocities and Output Intervals

- For new MD after minimization, use `gen-vel=yes` if velocities should be generated and record the temperature and random seed. When carrying velocities forward, use `gen-vel=no`, preserve compatible state, and configure initial constraint treatment with `continuation`. See [Runs and Checkpoints](run-and-restart.md).
- With `dt=0.001` ps (1 fs), `nsteps=20000000` gives 20 ns. `nstxout-compressed=1000` produces an XTC frame about every 1 ps in this example. Sample at a rate that resolves the target timescale and verify the recorded trajectory timestamps.
- `.xtc` stores compressed coordinates and the box. To retain velocities or forces, set `nstvout` or `nstfout` and check the fields present in `.trr`. Verify how initial velocities were generated and which output fields were written.

## Official References

[grompp](https://manual.gromacs.org/current/onlinehelp/gmx-grompp.html) · [MDP Options](https://manual.gromacs.org/current/user-guide/mdp-options.html) · [Topology Formats](https://manual.gromacs.org/current/reference-manual/topologies/topology-file-formats.html)
