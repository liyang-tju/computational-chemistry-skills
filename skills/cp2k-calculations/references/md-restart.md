# Dynamics and Restarts

## 1. Example NVT AIMD Input

```text
&GLOBAL
  PROJECT water_slab_nvt
  RUN_TYPE MD
  PRINT_LEVEL LOW
&END GLOBAL

&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME  BASIS_MOLOPT
    POTENTIAL_FILE_NAME  GTH_POTENTIALS
    &MGRID
      CUTOFF 500
      REL_CUTOFF 60
    &END MGRID
    &POISSON
      PERIODIC XY
      POISSON_SOLVER ANALYTIC
    &END POISSON
    &QS
      EPS_DEFAULT 1.0E-12
      EXTRAPOLATION ASPC
      EXTRAPOLATION_ORDER 3
    &END QS
    &SCF
      SCF_GUESS RESTART
      EPS_SCF 1.0E-6
      MAX_SCF 30
      &OT
        MINIMIZER DIIS
        PRECONDITIONER FULL_SINGLE_INVERSE
      &END OT
      &OUTER_SCF
        EPS_SCF 1.0E-6
        MAX_SCF 10
      &END OUTER_SCF
    &END SCF
    &XC
      &XC_FUNCTIONAL PBE
      &END XC_FUNCTIONAL
      &VDW_POTENTIAL
        POTENTIAL_TYPE PAIR_POTENTIAL
        &PAIR_POTENTIAL
          TYPE DFTD3(BJ)
          PARAMETER_FILE_NAME dftd3.dat
          REFERENCE_FUNCTIONAL PBE
        &END PAIR_POTENTIAL
      &END VDW_POTENTIAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 15.0 15.0 30.0
      PERIODIC XY
    &END CELL
    &TOPOLOGY
      COORD_FILE_NAME init.xyz
      COORD_FILE_FORMAT XYZ
    &END TOPOLOGY
    &KIND O
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q6
    &END KIND
    &KIND H
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q1
    &END KIND
  &END SUBSYS
&END FORCE_EVAL

&MOTION
  &MD
    ENSEMBLE NVT
    STEPS 5000
    TIMESTEP 0.5
    TEMPERATURE 300.0
    &THERMOSTAT
      TYPE CSVR
      &CSVR
        TIMECON 50.0
      &END CSVR
    &END THERMOSTAT
  &END MD
  &PRINT
    &TRAJECTORY
      &EACH
        MD 1
      &END EACH
    &END TRAJECTORY
    &CELL
      &EACH
        MD 1
      &END EACH
    &END CELL
    &RESTART
      BACKUP_COPIES 1
      &EACH
        MD 100
      &END EACH
    &END RESTART
  &END PRINT
&END MOTION
```

## 2. Ensembles, Time Steps, and Constraints

- **Time step and hydrogen mass**. Use `TIMESTEP 0.5` fs as a starting point for ordinary hydrogen. If using heavier hydrogen (for example, `MASS 2.014` in `&KIND H`) with `TIMESTEP 1.0` fs, record the mass choice and verify energy and temperature stability.
- **NPT and surfaces**. `ENSEMBLE NPT_I` or `NPT_F` is suitable for homogeneous three-dimensional bulk systems and liquids. For slabs with vacuum, isotropic or fully flexible NPT can collapse the vacuum gap. Use a defined cell-relaxation protocol with constrained degrees of freedom if a variable cell is needed.
- **Metal electrodes and conductors**. Remove `&OT` from `&SCF` and use `&DIAGONALIZATION`, `&SMEAR`, `&MIXING` (for example, `ALPHA 0.2`), and `ADDED_MOS`. Partial occupations require a solver other than OT.

## 3. `&EXT_RESTART` and Changes of State

When restarting from a previous `*-1.restart`, `STEPS` is the number of new MD steps, `STEP_START_VAL` is the initial step number, and `MAX_STEPS` is the cumulative step limit. To add 3000 steps from step 2000 with `RESTART_COUNTERS .TRUE.`, set `STEPS 3000` and ensure any configured `MAX_STEPS` is at least 5000.

| Scenario | `RESTART_POS/VEL` | `RESTART_CELL` | `RESTART_THERMOSTAT` | `RESTART_COUNTERS` | `SCF_GUESS` |
|---|---|---|---|---|---|
| Continuous restart with the same protocol | `.TRUE.` | `.TRUE.` for NPT | `.TRUE.` | `.TRUE.` | `RESTART` with `.wfn` |
| Change in target temperature or thermostat | `.TRUE.` | Depends on ensemble | `.FALSE.` | Prefer fresh counters for the new segment | `RESTART` if the system is unchanged |
| Restart from a new initial structure | `.FALSE.` | `.FALSE.` | `.FALSE.` | `.FALSE.` | `ATOMIC` with a fresh wavefunction guess |

## 4. Align Step Numbers, Times, and Files

Different `&EACH` frequencies and interrupted writes can produce unequal tails in `*-pos-1.xyz`, `*-1.cell`, and `*-1.ener`. Align them by step and time.

```python
# Check that step and time match across pos-1.xyz, 1.ener, and 1.cell
import re
steps_xyz = []
with open("proj-pos-1.xyz") as f:
    for line in f:
        m = re.search(r"i\s*=\s*(\d+),\s*time\s*=\s*([0-9.eEdD+-]+)", line)
        if m:
            t_val = float(m.group(2).replace("D", "E").replace("d", "e"))
            steps_xyz.append((int(m.group(1)), t_val))
print("xyz frames:", len(steps_xyz), "first/last:", steps_xyz[0], steps_xyz[-1])
```

- Compare floating-point times within a tolerance such as `abs(t1 - t2) < 1e-4`.
- Replace `D -> E` only in numeric fields. Preserve text fields such as the element symbol `Dy`.
- After an interruption, exclude a final incomplete `*-pos-1.xyz` frame with fewer than `natoms + 2` lines before merging or continuing. If energy or structure deteriorated before the crash, select a healthy earlier `*-1.restart.bak-*` and verify that `STEP_START_VAL` matches `*-1.ener`.
- Verify `PROGRAM ENDED AT`, stable energy and temperature, absence of sustained `MAX_SCF` saturation, and agreement between the final `.restart` step and the last complete trajectory frame.
