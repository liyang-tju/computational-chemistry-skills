# Data Representation and Metadata

## 1. Recommended `frame_index.csv` Fields

Use logical source identifiers and paths relative to the dataset root for portability. Keep host-specific absolute paths in local run logs.

| Field | Meaning |
|---|---|
| `sample_id` | Globally unique frame ID, such as `sysA_rep1_s005000` |
| `source_id` | Logical name of the original run segment |
| `relative_path` | Path relative to the data source root |
| `source_frame` | Zero-based frame index in the source trajectory |
| `simulation_step` | Original engine step, blank if unknown |
| `time` | Physical time, blank if unknown |
| `time_unit` | `fs` or `ps` |
| `segment_id` | Continuation segment, such as `seg01` or `seg02` |
| `replica_id` | Independent replica, such as `rep01` |

## 2. Retain or Clear Fields by Intended Use

Work on a new copy and remove stale state according to its intended use.

| Intended use | Retain | Clear or reset |
|---|---|---|
| **Labeled MLP data** | Geometry, cell, PBC, validated reference `energy`/`forces`/`stress`, and `protocol_id` | Unrelated intermediate caches |
| **DFT labeling** | Geometry, cell, PBC, `FixAtoms`, target `charge`/`NELECT`/`spin`, and `sample_id` | Set `atoms.calc = None`. Remove stale `energy`/`free_energy`/`forces`/`stress` and `momenta`. |
| **Subsystem extraction** (such as solvent or adsorbate) | Subset geometry, cell, and new atom mapping | Original full-system scalar energy and stale atom indices |
| **MD starting state** | Geometry, cell, PBC, and constraints. Keep `momenta` or velocities for continuous restarts. | Clear `momenta` and old `energy`/`forces` for fresh initialization. |

```python
def sanitize_for_dft_labeling(atoms):
    """Clear old energy, force, and momentum data on a copy, retaining geometry, cell, and FixAtoms."""
    clean = atoms.copy()
    clean.calc = None
    for key in ("energy", "free_energy", "stress", "virial", "REF_energy", "REF_stress", "REF_virials"):
        clean.info.pop(key, None)
    for arr_key in ("forces", "force", "momenta", "REF_forces"):
        clean.arrays.pop(arr_key, None)
    return clean
```

- Identify custom labels and whether they live in `info` or `arrays`. After cleanup verify atom and constraint mappings, electronic state, and provenance.
- Record missing cell, `PBC`, or atom-order information explicitly and recover it from the source before using it.
