---
name: enhanced-sampling
description: "End-to-end enhanced sampling and free energy workflow: design CVs and run inputs (VASP ICONST/Blue Moon/slow-growth/harmonic umbrella/MDALGO metadynamics, and PLUMED RESTRAINT/METAD/WT-Metadynamics/OPES_METAD/OPES_METAD_EXPLORE with ASE/CP2K/LAMMPS/i-PI), verify derivatives and bias convergence, and reconstruct PMFs with Blue Moon metric correction, WHAM, MBAR (pymbar), or c(t)/opes.bias reweighting and block error bars."
---
# Enhanced Sampling and Free-Energy Analysis

Design and select collective variables (CVs), prepare and validate VASP, PLUMED, ASE, or MD inputs, diagnose sampling coverage and hysteresis, and reconstruct potentials of mean force (PMFs) with uncertainties. Use `$che-calculation` for static zero-point energy, entropy, and computational hydrogen electrode diagrams.

## Before Starting

1. **Physical coordinates and dimensionality**. Identify the reactant and product minima, index conventions (VASP `ICONST` and PLUMED are **1-based** and ASE is **0-based**), and periodic crossings. Check that the CV distinguishes intermediates and side reactions.
2. **Method and engine**. Choose slow growth, Blue Moon constrained AIMD, umbrella sampling, metadynamics, WT-Metadynamics, `OPES_METAD`, or `OPES_METAD_EXPLORE`, and identify the engine (native VASP, CP2K, LAMMPS, ASE with an MLP, or i-PI).
3. **Available output and statistics**. Check file formats (VASP `REPORT` or `HILLSPOT`, CP2K `.lagrange_mult`, and PLUMED `COLVAR`, `HILLS`, `KERNELS`, or `OPES_STATE`), temperature $T$, and target energy units (`eV` or `kJ/mol`).

## Method Selection

| Method | Native VASP | PLUMED | Application | Key inputs | Free-energy reconstruction |
|---|---|---|---|---|---|
| **Slow-growth AIMD** | Yes (`-Dtbdyn`) | via i-PI / SMD | Fast scans along a known 1D path, with hysteresis checks | `ICONST status=0`, `LBLUEOUT`, `INCREM` | Trapezoidal integration of deduplicated `REPORT` gradients |
| **Constrained AIMD (Blue Moon)** | Yes (`-Dtbdyn`) | via CP2K / i-PI | Integrate gradients along a known 1D CV | `ICONST status=0`, `LBLUEOUT=.TRUE.` | Estimate metric-weighted window gradients and integrate |
| **Umbrella Sampling** | Yes (`status=8`) | `RESTRAINT` | High barriers, known coordinates, and parallel window sampling | `SPRING_K` / `SPRING_R0` or `AT` / `KAPPA` | WHAM or `pymbar` MBAR with overlap checks |
| **Standard Metadynamics** | Yes (VASP 6 `MDALGO=1/2`, VASP 5.x `11/21`) | `METAD` | Native VASP AIMD exploration with fixed hill heights | `status=5`, `HILLS_BIN/H/W`, `PENALTYPOT` | Sum `HILLSPOT` hills and check convergence |
| **WT-Metadynamics** | External interface | `METAD` with `BIASFACTOR` | Classical MD, MLIP, CP2K, or ASE with tempered hill heights | `BIASFACTOR`, `GRID_*`, `CALC_RCT` | `sum_hills` or $c(t)$ reweighting with `metad.rct` |
| **`OPES_METAD`** | External interface | `OPES_METAD` | Fast PMF convergence with a suitable CV and approximate barrier | `BARRIER`, `PACE`, `TEMP`, `STATE_*` | Reweight by `opes.bias` after discarding the initial transient |
| **`OPES_METAD_EXPLORE`** | External interface | `OPES_METAD_EXPLORE` | Unknown barriers, multiple pathways, or new CVs | `BARRIER` / `BIASFACTOR`, `EXCLUDED_REGION` | Discard a longer exploration transient, then reweight by `opes.bias` |

## Workflow

### 1. Design CVs and Check Derivatives and Limits
- Prefer smooth, nonsingular coordinates that track the target process, such as distances, angles, dihedrals, and differences like `R1 - R2` for proton transfer. For complex rearrangements or coordination switches, see [Reactive CVs](references/reactive-cv.md).
- Check complex reactive CVs on static structures and verify derivatives and forces by finite differences before long simulations.

### 2. Configure Engine Inputs and Units
- **Native VASP**. Set up `INCAR`, `ICONST`, and the bias as described in [VASP Sampling](references/vasp-sampling.md). For standard MetaD, select `MDALGO` for the installed version and set `HILLS_*` and optional `PENALTYPOT`. WT-Metadynamics and OPES use an external interface.
- **PLUMED, ASE, CP2K, and LAMMPS**. Configure units and biases using [PLUMED Sampling](references/plumed-sampling.md). WT-MetaD $c(t)$ reweighting requires `GRID_*` and `CALC_RCT`. For OPES, check `BARRIER` units, the action referenced by `EXCLUDED_REGION`, and restart state.
- Use single-frame `plumed driver` locally or on a head node to check syntax, kernel modules, and initial CVs. Align `COLVAR`, `KERNELS`, and `OPES_STATE` or `HILLSPOT -> PENALTYPOT` across restart segments.

### 3. Diagnose Sampling and Identify Steady Segments
- **Slow growth**. Compare forward and reverse pulls or use a smaller `INCREM` to check hysteresis. Remove confirmed boundary duplicates when merging restarts.
- **Umbrella sampling and constrained AIMD**. Check equilibration in each window and discard the initial relaxation. For umbrella sampling, verify substantial histogram overlap between neighbors.
- **WT-Metadynamics and OPES**. Check recrossings and PMF drift across time blocks. For OPES, use `opes.rct`, `opes.zed`, and the bias shape to assess quasi-stationarity, and `opes.neff` to assess the reweighted effective sample size.

### 4. Reconstruct the PMF and Quantify Uncertainty
- Follow the equations in [Free-Energy Estimators](references/estimators.md).
  - For Blue Moon or slow growth, extract gradients, apply metric corrections, and integrate by the trapezoidal rule. State all approximations.
  - For umbrella sampling, use WHAM or binless MBAR (`pymbar`). For a three-dimensional radial CV, evaluate whether to apply the $(d-1)k_B T \ln r$ Jacobian correction.
  - For WT-MetaD or OPES, use $k_B T$ consistent with `UNITS` for exponential reweighting with $c(t)$ or `opes.bias`. Check temporal block drift and report block errors or confidence intervals from bootstrap or `statistical_inefficiency` estimates.

## References and Open-Source Tools

- [Native VASP sampling with ICONST, Blue Moon, Umbrella Sampling, and Metadynamics](references/vasp-sampling.md)
- [PLUMED and ASE settings for Umbrella Sampling, WT-MetaD, OPES, and OPES Explore](references/plumed-sampling.md)
- [Reactive CVs, Voronoi and Grotthuss Tracking, and Derivative Tests](references/reactive-cv.md)
- [Free-Energy Estimators, Reweighting, and Block Errors](references/estimators.md)

Useful upstream projects are listed below.

| Tool or method | GitHub repository |
|---|---|
| PLUMED 2（Metadynamics / WT-Metad / Umbrella / OPES / `driver`） | [plumed/plumed2](https://github.com/plumed/plumed2) |
| PyMBAR (MBAR reweighting and `statistical_inefficiency`) | [choderalab/pymbar](https://github.com/choderalab/pymbar) |
| Grossfield WHAM（1D/2D Umbrella `wham`） | [agrossfield/wham](https://github.com/agrossfield/wham) |
| i-PI and VASP slow-growth extension | [i-pi/i-pi](https://github.com/i-pi/i-pi) · [zhangchenyu-USTC/i-pi_slow-growth](https://github.com/zhangchenyu-USTC/i-pi_slow-growth) |

## Deliverables and Validation

- **Input preparation**. Provide runnable `INCAR` fragments, `ICONST`, and `PENALTYPOT` or `plumed.dat` and its driver configuration. Verify units and first-frame CV values with a single-frame `driver` check or the first simulation step.
- **Analysis**. Provide reproducible Python reconstruction and diagnostic scripts, PMF plots and tables with statistical errors, and diagnostics such as recrossings, window overlap, or hysteresis. Document the $\frac{1}{2}\kappa$ convention, Jacobian correction, discarded transient length, and any omission of the metric $Z$.
