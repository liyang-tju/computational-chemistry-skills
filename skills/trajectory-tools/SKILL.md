---
name: trajectory-tools
description: "Convert, inspect, extract and join VASP, CP2K, LAMMPS, GROMACS and extxyz trajectories using ASE while preserving cell, PBC, step/time metadata and atom provenance. Use for trajectory I/O and preprocessing; statistical observables belong to trajectory-analysis."
---
# Trajectory Preparation and Conversion

Convert VASP, CP2K, LAMMPS, GROMACS, and other structures and trajectories to standardized inputs for analysis or labeling, preferably ASE `extxyz`. Preserve cells, PBC, atom identities, steps, times, and source indices. This skill covers conversion, cleaning, frame selection, and segment joins. Use `$trajectory-analysis` for statistical observables.

## Before Starting

- **Sources and companion files**. Identify topology, cell, and time metadata. Examples are CP2K `.cell` and `.ener`, LAMMPS `data` or `type->element` mapping, GROMACS `.gro` or `.tpr`, and VASP `POSCAR` and `INCAR` `POTIM`.
- **Intended use**
  1. **Labeled dataset** retaining energies, forces, and stresses.
  2. **Structures for DFT labeling** with old predictions cleared and electronic-state metadata and constraints retained.
  3. **New MD starting states** retaining cells and constraints, with explicit treatment of velocities.

## Workflow

### 1. Identify Formats and Check Physical Metadata

Inspect the first frame and associated logs to verify the following information.
- Atom count and element order. Supply an integer `type -> element` map when a LAMMPS dump has no `element` column.
- Cell changes. For NPT or other variable-cell runs, read the cell of every frame.
- Integration time step and output stride. Distinguish `frame_index` and `simulation_step` when calculating `time = simulation_step * dt`. Use `None` or `NaN` when time information is missing.

### 2. Read Frame by Frame and Check Completeness

Process and write large trajectories frame by frame. `ase.io.iread` memory use depends on the format reader, which may build an index or read a prefix. Exceptions can occur while advancing the iterator. This example checks extxyz coordinates and writes the parsed prefix to a new file. Inspect the source and logs after errors to determine whether truncation is at the tail or corruption occurs earlier.

```python
import numpy as np
from ase.io import iread, write
from ase.io.extxyz import XYZError

first_frame = last_frame = None
written = 0
with open("out.extxyz", "x") as output:
    try:
        for atoms in iread("traj.extxyz", format="extxyz", index=":"):
            if not np.all(np.isfinite(atoms.positions)):
                raise ValueError(f"Frame {written} contains NaN/Inf positions")
            write(output, atoms, format="extxyz")
            if first_frame is None:
                first_frame = atoms
            last_frame = atoms
            written += 1
    except XYZError as exc:
        raise ValueError(f"Input parse error after {written} written frames: {exc}") from exc
if written == 0:
    raise ValueError("No complete trajectory frames")
```

### 3. Extract Frames, Join Segments, and Remove Duplicates

- **Select by step or time**. Use explicit windows or strides, such as every `stride` ps. Record `source_id`, `source_frame`, `simulation_step`, and `time` in `frame_index.csv`.
- **Join continuation segments**. Identify the last healthy `checkpoint_step` from logs and checkpoints. Fall back to an earlier complete checkpoint and exclude incomplete frames if the run diverged or the tail is truncated. Retain parent steps `step <= checkpoint_step` and child steps `step > checkpoint_step` so a repeated first checkpoint frame is included once. Preserve the parent. Keep `replica_id` when combining independent replicas and preserve independent timelines.

### 4. Manage Labels and State in New Copies

Select fields according to the downstream use. [Data Representation and Metadata](references/metadata.md)
- Clear stale calculators and remove actual stale keys from `atoms.info` and `atoms.arrays` as needed. `write_results=False` controls calculator-result output. Remove labels already stored in metadata or arrays separately.

### 5. Write Outputs and Read Back a Sample

Check the first, last, and representative middle frames against their sources for atom counts, element order, cells, PBC, and constraints. The example checks endpoints containing only `FixAtoms` or no constraints.

```python
from ase.io import read

for index, source in ((0, first_frame), (-1, last_frame)):
    check = read("out.extxyz", format="extxyz", index=index)
    assert check.get_chemical_symbols() == source.get_chemical_symbols()
    assert np.allclose(check.cell.array, source.cell.array)
    assert np.array_equal(check.pbc, source.pbc)
    assert [item.todict() for item in check.constraints] == [
        item.todict() for item in source.constraints
    ]
```

## References

- Format details and parsing for VASP, CP2K, LAMMPS, GROMACS, and `extxyz`. [Format Handling](references/formats.md)
- `frame_index.csv` fields, label cleanup, and state retention. [Data Representation and Metadata](references/metadata.md)

## Deliverables and Validation

1. Converted structures or trajectories, such as `*.extxyz`.
2. **`frame_index.csv`** with `source_id, relative_path, source_frame, simulation_step, time, time_unit, segment_id, replica_id` for every frame.
3. **`conversion.json`** with sources, type mappings, truncation and deduplication counts, and read-back checks.
