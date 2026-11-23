# Conformation, Events, and Statistics

## 1. RMSD and Alignment

Make molecules or polymer chains whole under PBC before computing RMSD. A chain split across the cell can produce a spurious increase. Specify the reference, atom selection, weighting, and alignment.
1. **Reference structure**. Choose the optimized starting structure, frame 0, or the mean structure. Use a common reference convention across conditions. Each trajectory's own frame 0 measures displacement relative to that trajectory's start.
2. **Atom selection**. Specify heavy atoms, backbone atoms, or additional water and hydrogen atoms, and whether the fit is mass-weighted.
3. **Alignment**
   - **Self-alignment**. Remove rigid translation and rotation with a Kabsch fit to measure internal conformational flexibility.
   - **Alignment to the substrate or no rigid fit**. Measure adsorbate translation, rotation, and changes in adsorption geometry in the surface frame. Report the alignment used.

## 2. Reaction-Event Detection

When detecting bond formation or breaking, proton transfer, or desorption, account for transient fluctuations.
- **Hysteresis or minimum dwell time**. A bond can cross a single threshold for one step and immediately return. Use separate break and recovery thresholds, for example $r > 1.35\,\text{\AA}$ and $r < 1.15\,\text{\AA}$, or a minimum dwell time $\tau_{\text{dwell}}$ such as $\ge 50\,\text{fs}$. Record the criteria in the script and results.
- Record `replica_id, event_id, event_type, atoms_involved, start_time, end_time, duration, reversible`. Distinguish reversible exchanges from persistent changes using the full event history.

## 3. Correlated Statistics and Replica Aggregation

- **Effective sample size $N_{\text{eff}}$**. Estimate correlation from the integrated autocorrelation time $\tau_{\text{int}}$ (`g = 1 + 2 * tau_int`) or block averaging.
- **Variability and uncertainty metrics**
  - `SD` is the across-frame standard deviation. It measures physical fluctuations and does not shrink simply because sampling is longer.
  - `SE_block` is the blocked standard error within a trajectory. Use blocks much longer than $\tau_{\text{int}}$.
  - `SE_replica` is the standard error across independent replica means and measures reproducibility.
  - `95% CI` is the confidence interval. State whether it uses a $t$ distribution or a normal approximation.
- **Multiple trajectories**. Report three independent 100 ps runs as three replicates. With equal lengths, average per replica and then calculate the across-replica mean and error. With unequal lengths, state whether replicas are equally weighted or weighted by the effective sample count.
