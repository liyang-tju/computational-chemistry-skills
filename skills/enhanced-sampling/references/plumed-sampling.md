# Enhanced Sampling with PLUMED and ASE or MD Engines

Upstream repositories. [PLUMED](https://github.com/plumed/plumed2) · [i-PI](https://github.com/i-pi/i-pi)

## 1. Units, Atom Indices, and Periodic Boundaries

1. **Explicit `UNITS`**. PLUMED defaults to `nm / ps / kJ/mol`. With ASE, VASP, or eV/Å force fields, declare units on the first line and check `BARRIER`, `HEIGHT`, `KAPPA`, and `TEMP` against them.
   ```plumed
   UNITS LENGTH=A TIME=fs ENERGY=eV
   ```
2. **Atom indexing and PBC**
   - `ATOMS=...` uses **1-based indices**. Convert each ASE index with `idx + 1` before writing `plumed.dat`.
   - When molecular distances, centers of mass, or coordination groups cross a periodic boundary, check imaging and reconstruct molecules with `WHOLEMOLECULES` if needed. Use `NOPBC` only when appropriate for the intended geometry.

## 2. Umbrella Sampling and `MOVINGRESTRAINT`

PLUMED `RESTRAINT` applies a harmonic bias with the $\frac{1}{2}\kappa$ convention.

$$V(s) = \frac{1}{2}\kappa (s - s_0)^2$$

```plumed
UNITS LENGTH=A TIME=fs ENERGY=eV
d: DISTANCE ATOMS=46,48
umb: RESTRAINT ARG=d AT=2.00 KAPPA=15.0
PRINT ARG=d,umb.bias FILE=COLVAR STRIDE=20
FLUSH STRIDE=100
```

- **Window spacing and spring constants**. The thermal width is approximately $\sigma_{\text{harm}} \approx \sqrt{k_B T / \kappa}$. For overlap, use $\Delta s_0 \lesssim (1.0\text{–}1.5)\,\sigma_{\text{harm}}$. At high barriers, use closer windows or increase $\kappa$ as needed.
- **Steered MD (SMD)**. `MOVINGRESTRAINT` moves `AT` linearly between specified `STEP` values. Treat pulled trajectories separately from equilibrated windows and check forward and reverse dissipation and the applicability of Jarzynski averaging.

## 3. Standard and Well-Tempered Metadynamics (`METAD`)

For long runs requiring control over bias convergence, prefer Well-Tempered Metadynamics with **`BIASFACTOR`, grid acceleration, and `CALC_RCT`**.

```plumed
UNITS LENGTH=A TIME=fs ENERGY=eV
cv: DISTANCE ATOMS=46,48

metad: METAD ARG=cv ...
  PACE=200
  HEIGHT=0.02
  SIGMA=0.05
  BIASFACTOR=10.0
  TEMP=300
  GRID_MIN=1.0 GRID_MAX=5.0 GRID_BIN=400
  CALC_RCT
  FILE=HILLS
  RESTART=NO
...

PRINT ARG=cv,metad.bias,metad.rct FILE=COLVAR STRIDE=50
FLUSH STRIDE=100
```

- **Settings and checks**
  - `BIASFACTOR` gives $\gamma = (T + \Delta T)/T$. Omitting it selects standard metadynamics with fixed hill heights, which can overfill wells or drift. Catalytic and solution reactions often use $\gamma \approx 6\text{–}20$ to bring $\gamma k_B T$ near the estimated barrier.
  - Set `SIGMA` below the unbiased well's CV standard deviation, for example $\sim 0.3\text{–}0.5\,\sigma_{\text{well}}$.
  - For a grid, `GRID_MIN` and `GRID_MAX` must cover the accessible CV range with margin beyond the walls. `METAD` can also sum Gaussians directly without a grid.
  - For time-dependent $c(t)$ reweighting, enable `CALC_RCT` in grid mode to print `metad.rct`. [PMF Estimators](estimators.md)
  - **Continuation**. Use `RESTART=YES`, retain `HILLS`, and check continuity from the previous segment's last step.

## 4. Choosing and Configuring `OPES_METAD` or `OPES_METAD_EXPLORE`

The OPES module in PLUMED 2.8+ uses adaptive kernel density estimation, reducing parameter tuning in high-dimensional CV space.

| Feature | `OPES_METAD` | `OPES_METAD_EXPLORE` |
|---|---|---|
| **On-the-fly estimate** | Estimates the **unbiased distribution $P(s)$** and maps it to the target | Directly estimates the **well-tempered target $p^{\text{WT}}(s)$** |
| **Bias behavior** | Bias converges smoothly near quasi-stationarity | Larger fluctuations, similar to standard or well-tempered metadynamics |
| **Applications** | Approximate barrier and good CV separation, with emphasis on fast free-energy convergence | **Unknown barriers**, exploration of multiple routes, or testing tentative or degenerate CVs |
| **Reweighting diagnostics** | Check the bias shape, recrossings, and block PMFs | Bias tends to fluctuate during exploration. Use the same checks to select a usable interval. |

Example using `eV / A / fs`.

```plumed
UNITS LENGTH=A TIME=fs ENERGY=eV
cc: DISTANCE ATOMS=46,48
co1: DISTANCE ATOMS=46,47
excluded: CUSTOM ARG=cc FUNC=step(x-4.5) PERIODIC=NO

# Use OPES_METAD for FES convergence or OPES_METAD_EXPLORE to explore unknown barriers or multiple paths.
opes: OPES_METAD_EXPLORE ...
  ARG=cc
  TEMP=300
  PACE=400
  BARRIER=0.6
  # BIASFACTOR=15.0        ! Optional. Defaults to BARRIER/(k_B*T).
  SIGMA_MIN=0.05
  EXCLUDED_REGION=excluded
  FILE=KERNELS
  STATE_WFILE=OPES_STATE
  STATE_WSTRIDE=4000
  RESTART=NO
...

PRINT ARG=cc,co1,opes.bias,opes.rct,opes.zed,opes.neff,opes.nker FILE=COLVAR STRIDE=50
FLUSH STRIDE=100
```

Check these settings before continuing.
1. `BARRIER` follows the `ENERGY` setting in `UNITS`. `0.6 eV` is approximately `58 kJ/mol`. With `ENERGY=eV`, `60.0` represents `60 eV` and changes the derived bias settings.
2. **`EXCLUDED_REGION` vs `UPPER_WALLS`/`LOWER_WALLS`**：
   - `EXCLUDED_REGION` refers to a scalar action. A nonzero value stops kernel deposition at the current location while existing kernels still exert bias. Use `UPPER_WALLS` or `LOWER_WALLS` for soft confinement and include wall terms according to the target ensemble.
   - Use `LOWER_WALLS` and `UPPER_WALLS` with `METAD` and `RESTRAINT`.
3. **Restart alignment**. Retain `KERNELS` and `COLVAR` and set `RESTART=YES`. For OPES, use `STATE_WFILE=OPES_STATE` and `STATE_RFILE=OPES_STATE` to recover compressed kernels and $Z_n$. Match the times and steps of `COLVAR`, `KERNELS`, and `OPES_STATE` before continuing.

## 5. Engine Interfaces and Pre-Run Checks

- **ASE**：`ase.calculators.plumed.Plumed(calc, plumed_lines, timestep=dt_fs*units.fs, atoms=atoms, kT=T*units.kB, log=...)`。
  - **Multiline input**. Avoid trailing whitespace on `...` continuation markers and line splits incompatible with ASE. Use one line per action or a clean multiline block.
  - **Modules**. Check that the shared library identified by `PLUMED_KERNEL` includes the `opes` module. Older builds may omit it.
- **GROMACS**：`gmx mdrun -s topol.tpr -plumed plumed.dat`。
- **LAMMPS**. Use `fix pl all plumed plumedfile plumed.dat outfile plumed.log` with the `PLUMED` package and consistent units.
- **CP2K**. Use `&MOTION -> &FREE_ENERGY -> &METADYN -> USE_PLUMED .TRUE.` with `PLUMED_INPUT_FILE ./plumed.dat`. Check default unit conversion and compare the first `COLVAR` frame with `driver`.
- **Offline checks with `plumed driver`**
  1. For XYZ coordinates in Å, run `plumed driver --plumed plumed.dat --ixyz init.xyz --length-units A`. This option sets input coordinate units. `UNITS` in `plumed.dat` sets bias and output units. For PBC, supply the actual cell with `--box` or choose a format that carries the cell. Compare first-frame CVs with the expected geometry.
  2. Verify `kT`, derivatives, and force directions for `METAD`, `OPES_METAD`, `OPES_METAD_EXPLORE`, `RESTRAINT`, and walls. [Reactive CVs](reactive-cv.md)
