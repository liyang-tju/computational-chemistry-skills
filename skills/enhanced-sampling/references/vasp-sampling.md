# Native VASP Sampling with ICONST, Blue Moon, Umbrella Sampling, and Metadynamics

Native VASP enhanced sampling and constraints require a build with `-Dtbdyn`. Without it, the executable may ignore tags or report an error. All examples use **1-based `ICONST` indices**, one greater than the ASE indices.

See the i-PI and VASP slow-growth workflows. [VASP slow-growth extension](https://github.com/zhangchenyu-USTC/i-pi_slow-growth) · [i-PI](https://github.com/i-pi/i-pi)

## 1. MD Settings and `ICONST` Syntax

- In `INCAR` set `IBRION = 0` and `ISYM = 0`, plus `POTIM` (fs), `NSW`, `TEBEG`, and thermostat settings when applicable.
- Common `ICONST` geometries use the minimum-image convention under PBC.
  - `R a b <status>` is the `a-b` distance (Å).
  - `A a b c <status>` is the bond angle at `b` in **radians**.
  - `T a b c d <status>` is the four-atom dihedral in **radians**.
  - `S c_1 c_2 ... c_M <status>` gives a linear combination $\xi = \sum_k c_k q_k$ of the $M$ primitive coordinates in order. For $R_1 - R_2$, use two `R ... 0` lines followed by `S 1 -1 <status>`.
  - For composite CVs involving sums of squares, custom differences, or weighted distances, compare the script's first-frame result with `REPORT`.
- The final `status` field selects how the coordinate is used.
  - **`0`** applies a SHAKE constraint for constrained AIMD, Blue Moon, or slow growth. For an auxiliary primitive of `S`, use `0` or `7` as appropriate, with the `S` line defining the effective status.
  - **`4`** is a Fermi-step bias (`FBIAS_A`, `FBIAS_D`, `FBIAS_R0`).
  - **`5`** is Gaussian bias or metadynamics (`HILLS_*`, `PENALTYPOT`, `HILLSPOT`).
  - **`7`** monitors the coordinate in `REPORT` without constraint or bias forces. `VALUE_MIN` and `VALUE_MAX` can stop a run outside the allowed range.
  - **`8`** is a harmonic umbrella bias (`SPRING_K`, `SPRING_R0`, and optional `SPRING_V0`).

## 2. Blue Moon Constrained AIMD and Slow Growth

Compute free-energy gradients and integrate $\Delta A$ along a known one-dimensional reaction coordinate.

- **Constrained AIMD (discrete windows)**. Constrain each initial structure at its $\xi_k$ and average the generalized force over the equilibrated segment.
  ```fortran
  IBRION   = 0
  MDALGO   = 2            ! 1=Andersen, 2=Nose-Hoover, 3=Langevin
  ISYM     = 0
  LBLUEOUT = .TRUE.       ! Write Blue Moon gradient terms (b_m>) to REPORT.
  ```
  Set `status = 0` for the target coordinate in `ICONST`, for example `R 105 106 0`.
- **Slow growth (continuous pulling)**. Move the constrained coordinate at a fixed slow rate. Typical increments are $|\text{INCREM}| \sim 10^{-4}$–$10^{-3}\ \text{Å/step}$.
  ```fortran
  IBRION   = 0
  MDALGO   = 2
  ISYM     = 0
  LBLUEOUT = .TRUE.
  INCREM   = -0.0008      ! Target increment per MD step in CV units. Check forward and reverse hysteresis.
  ```
- **Output parsing and restarts**
  - Align `cc>` CVs and `b_m>` multipliers, weights, geometric corrections, and weighted gradients by step and constraint channel. Use the [PMF Estimators](estimators.md) reference for fixed-window gradients.
  - Before concatenating slow-growth segments, verify checkpoints, global steps, and channels. Remove only confirmed boundary duplicates and keep genuine small increments.
  - Excessive pulling rates cause hysteresis. Check important barriers with discrete constrained AIMD windows or comparisons of forward and reverse pulls.

## 3. Native VASP Umbrella Sampling and Steered MD

Native VASP applies a harmonic bias through `ICONST status = 8` without an external plugin.

$$V_{\text{bias}}(\xi) = \sum_{\mu=1}^{M_8} \frac{1}{2}\kappa_\mu \left(\xi_\mu - \xi_0^\mu\right)^2$$

```fortran
IBRION    = 0
MDALGO    = 2
ISYM      = 0
SPRING_K  = 10.0         ! Spring constant kappa_mu (eV/uc^2, such as eV/Å^2 or eV/rad^2)
SPRING_R0 = 2.10         ! Equilibrium center xi_0^mu. Supply one per ICONST status=8 coordinate.
! SPRING_V0 = 0.0005     ! Optional rate (uc/fs) for steered MD
```

Verify the $\frac{1}{2}\kappa$ convention for `SPRING_K` and use consistent `k` values and angular units (`rad`) in analysis.

## 4. Native VASP Metadynamics with `PENALTYPOT` and `HILLSPOT`

Native VASP supports standard metadynamics. Well-Tempered Metadynamics and OPES require external interfaces.

```fortran
IBRION        = 0
ISYM          = 0
MDALGO        = 1        ! VASP 6: 1=Andersen, 2=Nose-Hoover；VASP 5.x: 11/21
ANDERSEN_PROB = 0.10     ! Set when using the Andersen thermostat.
HILLS_BIN     = 50       ! Deposit a Gaussian every N steps. Set explicitly because the default may disable updates.
HILLS_H       = 0.005    ! Gaussian hill height (eV)
HILLS_W       = 0.05     ! Gaussian sigma in CV units
```

Set `status = 5` in `ICONST` for the biased CV. An example is `R 1 5 0`, `R 1 6 0`, and `S 1 -1 5`.

- **`PENALTYPOT` and walls**. VASP reads initial hills from `PENALTYPOT` and writes the complete list to `HILLSPOT` at the end.
  - **Continuation**. Use `cp HILLSPOT PENALTYPOT` to retain the accumulated bias for the next segment.
  - **Soft walls**. Use tall, wide boundary Gaussians in the initial `PENALTYPOT`, for example `[-3.0, 1.0, 0.3]` and `[3.0, 1.0, 0.3]`, to discourage nonreactive structures from exploring distant regions.
  - **Time series**. Plot the per-step CVs from `fic_p>` lines in `REPORT` to identify crossings or trapping near a boundary.

## 5. External Drivers and PLUMED

The official VASP build has no native `-DPLUMED` switch. Use an external interface for the following features.
- **Well-Tempered Metadynamics（`BIASFACTOR` / `CALC_RCT`）**
- **`OPES_METAD` or `OPES_METAD_EXPLORE`**
- **Complex differentiable CVs** such as `COORDINATIONNUMBER` switches, Voronoi proton transfer, or path CVs.

Choose an interface based on the simulation engine. [PLUMED Sampling](plumed-sampling.md)
1. **ASE or i-PI**. Use the ASE `Plumed` calculator or i-PI to apply PLUMED bias forces at each step. [i-PI](https://github.com/i-pi/i-pi)
2. **MLIP with LAMMPS or ASE and PLUMED**. Train the MLIP using DFT and active learning (see `$mlp-workflow`), then run nanosecond OPES or WT-Metadynamics. [PLUMED](https://github.com/plumed/plumed2)
3. **Engine with native PLUMED integration**. For example, use CP2K with `&FREE_ENERGY&METADYN USE_PLUMED .TRUE.`.
