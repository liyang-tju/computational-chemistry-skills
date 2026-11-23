# Stages 1–2. Foundation-Model Sampling, Selection, and Coverage

Upstream libraries. [DScribe](https://github.com/SINGROUP/dscribe) · [QUESTS](https://github.com/dskoda/quests) · [MACE](https://github.com/ACEsuit/mace)

## 1. Stage 1. Presample with a Foundation Potential

Use a foundation MLP such as `mace-mp` or `mace-mh`, or an earlier model, to sample broadly at low cost and build a candidate pool of reactive and nonreactive trajectories.

1. **Unbiased MD across conditions**. Cover target cell sizes (such as small-cell training and multiple-size generalization), compositions (bare, single adsorption, coadsorption, different ion or solute counts), and temperatures (such as `300 K` for equilibrium configurations and `350–400 K` for faster solvent and ion rearrangement).
2. **Sampling along reaction coordinates with umbrella windows or starts from both sides**
   - When barriers are rarely crossed in unbiased MD, set consecutive umbrella windows along a coordinate such as a forming or breaking bond length $d$ with $V = \frac{1}{2}k(d - d_0)^2$. Increase sampling near the transition region.
   - **Independent starts from both sides**. Where possible, initialize each window from physically plausible structures from both reactant and product sides to reduce trapping in the same local hydrogen-bond cage.
   - **Completion records**. Record settings and thermodynamics, including bias energy, reaction coordinate, and maximum force. On successful completion write `complete.txt` or an equivalent frame-count marker. Check trajectory completeness before selection.

## 2. Stage 2. Filter Invalid Topologies and Preserve Reactive Configurations

Check each frame for topology and reaction state before selection and record exclusion counts.
- **Damaged frames**. Remove `NaN/Inf` coordinates, unintended dissociation or proton escape in nonreactive species (such as water $\text{O–H} > 1.30\ \text{\AA}$ or abnormal neighbor topology, as appropriate), severe atomic overlap (`< 0.70–0.75 Å`), and excessive umbrella-center deviations (`|d - d0| > max_offset`).
- **Reactive frames**. Keep plausible forming or breaking bonds, including transition-region bond lengths and `O–H ~ 0.95–1.30 Å` during proton transfer. Apply role-specific chemical ranges and label states by key coordinates, for example `bare`, `adsorbed`, `approach`, `barrier`, and `product`.

## 3. Role-Resolved Local Descriptors

In systems with a metal interface, a few reactants and ions, and many solvent molecules, whole-frame mean SOAP can obscure changes at two reactive centers with fluctuations from dozens of solvent molecules.

Pool descriptors by role and append physical features as needed.
1. Choose groups such as reactive group A, reactive group B, neighboring active surface atoms, key ions, and nearby solvent atoms. Use only these atoms as `centers` for local SOAP or QUESTS descriptors.
2. L2-normalize each atom vector, average within each role, L2-normalize the means, and concatenate them into one fixed-size frame vector.
3. Optionally append scaled and clipped physical features such as ion height, first-shell coordination, or nearest distance to the adsorbate.
4. Use local-environment information coverage and MSC to identify gaps across the set of atomic environments. [QUESTS](https://github.com/dskoda/quests)

## 4. State-Prioritized FPS, Time Separation, and Quotas

Use the following controls for correlated trajectories.
1. **Cross-trajectory deduplication**. Use SHA-256 fingerprints (`seen_signatures`) of atom indices and PBC-aligned, rounded coordinates to remove exact duplicates from branches or stationary segments.
2. **Minimum time separation**. Require at least `MIN_TIME_SEPARATION` between selected frames from one trajectory, such as `0.15 ps` or `150 fs`.
3. **State and environment coverage followed by farthest-point sampling (FPS)**
   - First select a representative of each observed reaction state and key environmental bin, such as a point near the group mean or the most distinct candidate.
   - For paired branches in neighboring windows, pass the already selected branch's features, such as the `reactant` branch, to `paired_branch`. Compute each candidate's minimum distance to selections from both branches to diversify coverage.
   - Fill remaining quotas by greedy FPS with cosine or Euclidean distance. Report a shortfall when candidates run out and preserve unique selections.

## 5. Clean Outputs and Audit Coverage (`coverage_analysis`)

1. **Remove stale predictions and retain constraints**. Clear `atoms.calc` in selected copies and remove stale keys from `atoms.info` and `atoms.arrays`. Write `selected.extxyz` with `write_results=False`, keeping provenance and constraints. For `FixAtoms`, use `columns=["symbols", "positions", "move_mask"]` as needed. Read back a sample with differing constraints and write frames individually if the installed ASE loses masks in multi-frame output.
2. **Traceability table**. Include `dataset_index`, source trajectory, 1-based source frame, reaction state, coordinate value, temperature, window, and seed in `frames.csv`.
3. **Coverage audit**. Compare the candidate pool (for example 40,000 frames) and selected subset (for example 1,800) using marginal distributions and two-dimensional grid coverage of reaction coordinates, ion heights, coordination, and nearest contacts. Use metrics such as `raw_bin_fraction` and multivariate `within_one_tolerance` to identify gaps, including at transitions between unbiased MD and umbrella windows.
