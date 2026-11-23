# Constant-Potential Dynamics and Mixed Solvents

## 1. CP-VASP（`LCEP = .TRUE.`）

CP-VASP adjusts `INFO%NELECT` in the VASP ionic or MD loop using `NESCHEME` to keep the Fermi level near `TARGETMU` (negative, in eV). [yuanyue-liu-group/CP-VASP](https://github.com/yuanyue-liu-group/CP-VASP)

| `NESCHEME` | Electron-count update | Typical use | Key settings |
|---|---|---|---|
| `1` | Iterate only at `NSTEP = 1` until the error is `< FERMICONVERGE`, then apply one estimated update every `NEADJUST` steps | Fast single-point initialization or mild adjustment | `TARGETMU`, `FERMICONVERGE`, `CAP_MAX`, `NEADJUST` |
| `2` | Update `NELECT` once every `NEADJUST` steps using the two-step finite-difference capacitance `CAP_CP`, clamped to `[0.1, CAP_MAX]` | Constant-potential optimization and robust MD | `TARGETMU`, `CAP_MAX`, `NEADJUST`, `ECHANGE_MAX` |
| `3` | Repeat SCF every `NEADJUST` steps until `\|TARGETMU - E_F\| < FERMICONVERGE` | Strict instantaneous control at high cost | `TARGETMU`, `FERMICONVERGE`, `CAP_MAX` |
| `4` | Velocity-Verlet dynamics of the fictitious charge coordinate without a separate electronic thermostat | Microcanonical electronic tests | `Mne`, `NEADJUST`, `TARGETMU` |
| `5` | Grand-canonical MD with a **Nosé–Hoover chain (NHC)** for the fictitious electronic coordinate | **Production CP-AIMD** | `NEADJUST = 1`, `TARGETMU`, `T_eta`, `eta_length`, `Mne` |

- **Output parsing**. `CPM-ion` lines in `OSZICAR` record instantaneous excess electrons and chemical potential. When exporting `extxyz`, align positions and forces with electron counts at the `NEADJUST` interval. Verify whether the recorded quantity is excess electrons relative to the neutral valence count or total electrons.
- **Energy convention**. CP-VASP `GCE` includes zero-temperature entropy extrapolation (`TOTEN - EENTROPY/(2+NORDER)`) and the electron-reservoir term. Use the same finite-temperature variational free-energy definition when checking force–energy consistency.

## 2. SOLHYBRID + TPOT for Mixed-Solvent CP-AIMD

See the mixed-solvent model and target-potential controller repositories. [comet-group/VASPsol](https://github.com/comet-group/VASPsol) · [comet-group/tpot](https://github.com/comet-group/tpot)

### SOLHYBRID Exclusion of Implicit Electrolyte from Explicit Water
Standard VASPsol can allow the implicit dielectric to enter low-density gaps between explicit water molecules in the double layer. `LSOLHYBRID = .TRUE.` provides two ways to fill those gaps or exclude implicit solvent.

```ini
LSOL = .TRUE.
EB_K = 78.4
LAMBDA_D_K = 3.04
TAU = 0
LSOLHYBRID = .TRUE.
CORE_C = 1 6 11       # Match the core-electron filler parameters to the elements on POSCAR line 6
METHOD_SH = 1         # 1 fills gaps using plane-averaged valence density. 2 protects the ZMIN_SH/ZMAX_SH interval.
SIGMA_SH = 0.02222    # Interfacial smoothing width in fractional coordinates
ALPHA_SH = 0.1        # Gap-filling coefficient
# With METHOD_SH = 2, define a fractional-coordinate interval. Implicit solvent acts only outside it, on the bulk or vacuum side.
# ZMIN_SH = 0.0
# ZMAX_SH = 0.622222
```

- When driving `SOLHYBRID` or `TPOT` with ASE `Vasp`, register their nonstandard keywords in `bool_keys`, `int_keys`, or `float_keys` in `ase.calculators.vasp.create_input`. Otherwise ASE may skip them or raise an error.

### TPOT Control of the Target Vacuum Work Function
```ini
LTPOT = .TRUE.
TPOTMETHOD = 2            # 1 updates charge inside SCF. 2 updates after each ionic step and is recommended for AIMD.
TPOTTRUEVACLEVEL = .TRUE. # Use -(EFERMI - VACLEVEL) on the vacuum scale. .FALSE. uses FERMI_SHIFT.
TPOTVTARGET = 3.0         # Positive target work function. 3.0 V corresponds to an absolute Fermi level of -3.0 eV.
TPOTVDIFF = 0.01
TPOTELECTSTEP = 0.05      # Maximum electron-count change per step
TPOTDYNVRATE = .TRUE.
TPOTVRATE = -1.6
TPOTVRATELIM = 0.05
TPOTGCENERGY = .TRUE.
TPOTGCIONIC = .TRUE.
NELECT = <reasonable initial electron count>  # Start MD after a single point or charging to the target with TPOTMETHOD=1.
```

- **Restart**. `OUTCAR` reports `UPDATED NELECT` at the end of each ionic step. Continue in a new directory with `NELECT` in `INCAR` set to the final `UPDATED NELECT` from the previous segment to avoid restarting the charge transient.

## 3. i-PI + VASP Socket Dynamics and the Ne Counter Electrode

Connect patched VASP to the i-PI `<electrons enabled="true">` block with fictitious `mass` and an SVR `potentiostat`. Use `IBRION = 24` for the constant-potential electronic coordinate and `IBRION = 23` for the equivalent fixed-charge control. [Constant-potential i-PI](https://github.com/zhangchenyu-USTC/i-pi_constant-potential) · [Upstream i-PI](https://github.com/i-pi/i-pi)

1. **Faster implicit-solvent dynamics**. Use `<solvation_update_stride>` to reduce the cost of implicit solvent by recalculating the full electrolyte response at intervals, for example every 5 steps. The intervening steps evolve only the electronic coordinate `q`.
2. **Ne virtual counter electrode without implicit solvent**. Place a fixed Ne layer in the vacuum above the interfacial water. Include it in `<fixatoms>` with the bottom metal layers and set `Ne_doping="true"`. Lower `<target_workfunction>` to inject electrons into the metal–water interface. The compensating charge localizes on the Ne layer.
   - The Ne model defines a **relative bias**, for example a 1.0 V decrease from zero bias. An absolute SHE or RHE potential requires a separate calibration.
3. For both modes, plot the planar-averaged electrostatic potential $V(z)$. Check that `<potential_average_region>` lies entirely in a flat vacuum or bulk-solvent plateau. In Ne mode, use the vacuum region above the Ne layer.
