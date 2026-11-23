---
name: lammps-md
description: "Prepare LAMMPS classical MD and electrode simulations, including data/topology checks, unit conversions, equilibration/production stages, independent replicas and restart continuations."
---
# LAMMPS Simulation Setup

Prepare classical MD inputs with consistent topology, units, boundary conditions, and stage protocols. Set up independent replicas, binary restarts, and fixed-charge or constant-potential electrode simulations.

## Before Starting

- **Units and atom style**. Specify `units` (`real`, `metal`, or `lj`) and `atom_style` (`full`, `charge`, or `atomic`).
- **Topology and potentials**. Locate the `data` or `restart` file, map elements to `atom type` explicitly, and identify required `pair_style`, `bond_style`, `angle_style`, `kspace_style`, and `special_bonds` settings (such as AMBER, CHARMM, or OPLS).
- **Stages**. Specify minimization (`minimize`), heating or NPT density equilibration, NVT pre-equilibration, production sampling, and `dump` fields.
- **Electrodes where applicable**. Choose fixed atomic charges, fixed total charge, or constant potential such as `fix electrode/conp` from `ELECTRODE`. Record the voltage and reference convention.
- **Build**. Verify the LAMMPS executable and compiled packages or styles for CPU, GPU, or Kokkos.

## Workflow

### 1. Verify Build Capabilities and Topology

Use read-only checks to identify the packages and acceleration backends supported by the actual executable.

```bash
lmp -h | grep -A 30 "Installed packages"
```

Read the `data` header and `Masses` section to map `type_id -> element -> role` (for example `type 1 = Pt`, `type 2 = Ow`, and `type 3 = Hw`). Check that the `bonds`, `angles`, `dihedrals`, and `impropers` match the styles in the input.

### 2. Verify Units, Force-Field Mixing, and Long-Range Electrostatics

- **Unit conversion**. Convert the time step, energy, charge, and spring constants to the selected `units`. For example, `1.0 fs` corresponds to `timestep 1.0` in `units real` and `timestep 0.001` in `units metal`. [MD Protocols](references/protocols.md)
- **Hybrid potentials and 1–4 rules**. With `pair_style hybrid` or `hybrid/overlay`, check each cross term `pair_coeff i j` and whether it is supplied explicitly or by the correct `geometric` or `arithmetic` mixing rule. Use the force field's `special_bonds` convention, such as `amber`, `charmm`, or `lj/coul 0.0 0.0 0.5`.
- **Slab electrostatics**. For vacuum or double-layer slabs, use `boundary p p f` with `kspace_style pppm 1.0e-4` and `kspace_modify slab 3.0`, or use `pppm/electrode` as appropriate. Check isolation when using long-range electrostatics on asymmetric interfaces.

### 3. Set Up Minimization, Equilibration, and Production

- **Rigid water and constraints**. Use `fix shake` or `fix rattle` with a compatible integrator. Since LAMMPS 15Sep2022 these fixes can approximate constraints with stiff harmonic restraints during minimization. With older versions, minimize using a compatible flexible potential before enabling MD constraints.
- **Controlled comparisons and independent replicas**
  - Keep topology source, force field, and cutoffs consistent across conditions and vary only the declared variable.
  - Record each `replica` seed used in `velocity all create <T> <seed>` or the source of each independent initial state. Adjacent frames from one trajectory share sampling history.

### 4. Configure the Electrode Model

- Identify the intended model.
  1. **Fixed atomic charges**. Electrode atoms carry fixed partial charges, often zero.
  2. **Conductor with zero total charge (Q=0)**. Charges can redistribute while the total remains zero.
  3. **Controlled potential or potential difference**. `fix electrode/conp` imposes the specified potentials. `fix electrode/thermo` uses a thermo-potentiostat to control the bias while allowing instantaneous potential fluctuations. Both require `ELECTRODE` and a compatible solver such as `pppm/electrode`.

### 5. Prepare Restarts and Verify Outputs

- **Completion and numerical stability**. Check `Total wall time` in `log.lammps`, the target final `Step`, and the absence of `ERROR` or `Lost atoms`. Inspect temperature, potential and total energies, and key bond lengths across the segment. If atoms scattered or the system deteriorated before a crash, restart from a healthy earlier binary checkpoint.
- **Restart method**. Use a binary `restart` to preserve velocities and supported internal `fix` state. For incompatible major versions or fixes, use `write_data` and `read_data` and record the resulting reinitialization of dynamics.
- **`read_restart` and final steps**. Redeclare nonpersistent `fix`, `pair_style` where needed, and `dump` settings. Continue in a separate directory and use `run <S_target> upto` to specify the absolute target step.
- **Zero-step test**. Check syntax, finite initial energies and forces, and activation of the intended `kspace` or GPU path.

```bash
lmp -in input.lammps -log check.log   # Set run 0 in the temporary test script.
```

## Reference

- See [MD Protocols](references/protocols.md) for `real` and `metal` conversions, a template, electrode solver compatibility, and restart checks.

## Deliverables and Validation

1. `input.lammps`, any stage scripts (`01_min.lmp`, `02_eq.lmp`, `03_prod.lmp`), the `data` file, and `type_map.json`.
2. `replicas.csv` with `replica_id`, initial state, seed, and target duration for each replica.
3. Verify that the test reports no `ERROR` or missing coefficients, that equilibrated temperature, total energy, and bulk density stabilize in the intended ranges, and that `dump` includes `id type x y z` or unwrapped `xu yu zu` as requested.
