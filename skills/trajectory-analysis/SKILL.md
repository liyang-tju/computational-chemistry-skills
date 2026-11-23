---
name: trajectory-analysis
description: "Analyze MD/AIMD/MLP trajectories for density profiles, water orientation, RDF, coordination numbers, hydrogen bonds, RMSD and reaction events using consistent PBC, time windows and autocorrelation-aware statistics."
---
# Trajectory Analysis

Calculate interfacial distributions, hydrogen-bond coordination, conformational RMSD, and reaction events from prepared and verified trajectories. Use consistent time windows, atom selections, periodic boundary conditions (PBC), and uncertainty conventions across conditions. Use `$trajectory-tools` for conversion, concatenation, and deduplication.

## Before Starting

- **Trajectories and metadata**. Locate the `extxyz` or other trajectory files, cells, integration time step `dt`, equilibration cutoff $t_{\text{eq}}$, and independent `replica_id` values.
- **Requested observables and definitions**. Calculate only the requested quantities, such as water density, signed orientation $\langle \cos\theta \rangle$, RDF and coordination numbers, hydrogen bonds, RMSD, or reaction events.
- **Comparison conditions**. Match criteria, units, and comparable sampling windows across temperatures, potentials, coverages, or force fields.

## Workflow

### 1. Verify Sampling Windows and Periodic Geometry

- Specify the excluded equilibration period $t_{\text{eq}}$ and analysis window $[t_{\text{start}}, t_{\text{end}}]$. Use the cell of each frame for variable-cell trajectories, such as NPT.
- Reconstruct molecules split across boundaries with the minimum-image convention (MIC) before calculating O–H vectors, water dipoles, or molecular centers of mass.

### 2. Follow the Protocol for the Requested Observable

Consult the relevant reference.
- Interfacial density, water orientation, RDF, and coordination. [Interfacial Distributions](references/interface.md)
- Hydrogen-bond networks, donor and acceptor definitions, and proton reassignment. [Hydrogen Bonds and Coordination](references/hydrogen-bonds.md)
- RMSD alignment, reaction-event dwell times, and uncertainty. [Conformation, Events, and Statistics](references/conformation-statistics.md)

### 3. Retain Per-Frame, Per-Block, and Per-Group Results

- Save time series and block statistics as well as the mean. Preserve breakdowns for solute donors and acceptors, individual oxygen sites, upper and lower interfaces, and each `replica` to diagnose drift and agreement.
- Verify density and coordination by integration, for example $\int \rho(z) A_{xy}\,\mathrm{d}z = N_{\text{waters}}$.

### 4. Account for Time Correlation

- Report within-trajectory errors from block averaging or statistical inefficiency $g$, and between-replica variability. Estimate the effective sample count from correlation.
- For unequal trajectory lengths, state whether results are weighted by frame or averaged equally across replica means.

## References

- Surface-relative coordinates, bin-volume normalization, `cos(theta)` measures, and interfacial RDFs. [Interfacial Distributions](references/interface.md)
- Hydrogen-bond angle conventions, dynamic proton assignments, and normalization. [Hydrogen Bonds and Coordination](references/hydrogen-bonds.md)
- Surface and self alignment for RMSD, event hysteresis, and block statistics. [Conformation, Events, and Statistics](references/conformation-statistics.md)

## Deliverables and Validation

1. **`analysis.py`** with paths, time windows, cutoffs, and bin widths in a top-level configuration section. Reuse validated project scripts where available.
2. **Observable tables and per-frame or per-block CSVs** with clear column names and units, such as `z_rel_surf_A`, `rho_g_cm3`, `hbonds_per_solute`, and `se_block`.
3. **`analysis_summary.json`** with formulas, thresholds, time windows, $N_{\text{frames}}$, $N_{\text{replicas}}$, and integration checks.
