# MD Protocols

## 1. Units in `real` and `metal`

Verify units when importing literature, VASP or ASE, and machine-learning potential parameters into LAMMPS.

| Quantity | `units real` (common classical force fields) | `units metal` (common EAM and MLP) |
|---|---|---|
| Length | Å | Å |
| Time | fs (often `timestep 1.0`) | ps (`timestep 0.001` for `1 fs`) |
| Energy | kcal/mol | eV ($1\,\text{eV} = 23.0605\,\text{kcal/mol}$) |
| Mass | g/mol | g/mol |
| Pressure | atm | bar ($1\,\text{atm} = 1.01325\,\text{bar}$) |
| Charge | $e$ | $e$ |
| Thermostat damping `Tdamp` | Often `100.0` (100 fs) | Often `0.1` (0.1 ps) |

LAMMPS `bond_style harmonic` and `angle_style harmonic` use $E=K\Delta^2$, where $\Delta$ is the displacement in bond length or in angle in radians. Convert from the source convention. For $\frac12 k\Delta^2$, set $K=k/2$. Native AMBER and GAFF bond and angle terms already use $K\Delta^2$, so retain the coefficients when units match. LAMMPS takes equilibrium angles in degrees and interprets angular force constants per radian squared.

## 2. Interface and Electrolyte Template (`units real`)

```lammps
units           real
atom_style      full
boundary        p p f

pair_style      lj/cut/coul/long 12.0 12.0
pair_modify     mix arithmetic tail no
kspace_style    pppm 1.0e-4
kspace_modify   slab 3.0

bond_style      harmonic
angle_style     harmonic
special_bonds   amber

read_data       system.data

# Define groups using type_id values from the current data file.
group           slab type 1
group           water type 2 3

# 1. Fix the substrate and minimize the liquid.
fix             freeze slab setforce 0.0 0.0 0.0
minimize        1.0e-4 1.0e-6 1000 10000
reset_timestep  0

# 2. Enable rigid water constraints after minimization and equilibrate in NVT.
fix             water_shake water shake 1.0e-4 20 0 b 1 a 1
velocity        water create 300.0 48271 dist gaussian
fix             thermo_nvt water nvt temp 300.0 300.0 100.0

thermo          500
thermo_style    custom step temp pe ke etotal press vol
dump            traj all custom 1000 eq.lammpstrj id type element xu yu zu
dump_modify     traj element Pt O H sort id

timestep        1.0
run             100000
write_restart   eq.restart
```

- For element labels in `dump_modify ... element ...`, match the list to `type 1, 2, 3...` so ASE and OVITO read the intended elements.

## 3. Constant-Potential Electrodes (`ELECTRODE`)

- With `fix electrode/conp` or `fix electrode/thermo`, check the following settings.
  1. Use a compatible `kspace_style`, such as `pppm/electrode` or `ewald/electrode`. Incompatible solvers cause a runtime error.
  2. Define the electrode groups (`group elec1` and `group elec2`), specify whether the parameter is a difference or an individual electrode potential, and record units. For `units real`, electrode potential is usually in volts. Confirm with the installed version's `fix electrode/conp` documentation.
  3. Verify actual electrode solver acceleration and performance with a short compute-node test. A build with `GPU` or `KOKKOS` alone does not establish GPU support for the `electrode` solver.

## 4. Equilibration, Bulk Density, and Restart Checks

- **NPT and vacuum interfaces**. Use `fix npt` for density equilibration in 3D bulk solution. For a slab with vacuum, keep the z dimension fixed. Use a fixed liquid thickness or pre-equilibrate a 3D solution box before adding the surface. Estimate bulk density away from the double layer and report the first interfacial peak separately.
- **Continuations and hardware changes**
  - Check `Total wall time`, the final `Step`, and the absence of `ERROR` or `Lost atoms` in `log.lammps`. For a continuation, use `read_restart` in a new directory and `run <S_target> upto`. Redeclare `fix shake`, `fix nvt` or `npt`, `fix setforce`, `fix electrode/*`, and `dump` as applicable.
  - When continuing from `write_restart`, check that the log starts at the previous segment's final `Step`. `write_data` retains velocities and `Image flags` unless explicitly cleared, but omits `fix` history.
  - Changing only MPI ranks or GPU count can cause trajectories to diverge after tens to hundreds of steps due to floating-point summation order. Steady-state thermodynamic averages should agree.
