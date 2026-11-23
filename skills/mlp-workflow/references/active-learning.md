# Stage 5. Committee Uncertainty Sampling, Quarantine, and SOAP Pruning

## 1. Production Dynamics and Logging

For sustained production MD, umbrella sampling, or PLUMED `OPES_METAD_EXPLORE`, propagate with the mean force of a committee of independently seeded models, for example four `.model` files evaluated in parallel. Write complete `uncertainty.csv` rows at a fixed stride, aligned with `step=` and `time_fs` in the `trajectory.extxyz` header.
- Record each total-energy prediction, such as `energy_seed_<s1>_eV` and `energy_seed_<s2>_eV`.
- **Force disagreement on mobile atoms**. Exclude `FixAtoms` substrate atoms since their forces do not drive the dynamics and extrapolation noise can affect the metric. Record the maximum per-atom standard deviation `force_std_max_atom_mobile_eV_A` and RMS disagreement `force_std_rms_mobile_eV_A`.
  $$\sigma_{F, i} = \left\| \operatorname{std}_{m}\bigl(\mathbf{F}_i^{(m)}\bigr) \right\|_2, \quad \sigma_{F,\max}^{\text{mobile}} = \max_{i \in \text{mobile}} \sigma_{F,i}$$

## 2. Baseline-Centered Energy Disagreement (`dE_cent`)

Independently seeded models may differ by constant energy offsets of a few to tens of meV. The standard deviation of raw total energies $\operatorname{std}_m(E^{(m)})$ can therefore indicate uncertainty even when the potential-energy surfaces have identical shapes.

Use the baseline-centered energy standard deviation.
1. For each run, choose an early stable interval such as equilibration or `step <= BASELINE_MAX_STEP`, with several hundred to a few thousand samples. Find the median offset of each model from the committee mean.
   $$\mathbf{b} = \operatorname{median}_{t \in \text{phase1}} \Bigl(\mathbf{E}_t - \overline{E}_t\Bigr)$$
2. At each step, subtract the baseline offsets and calculate the centered energy standard deviation.
   $$\sigma_{E,\text{cent}}(t) = \operatorname{std}_{m}\Bigl((E_t^{(m)} - \overline{E}_t) - b^{(m)}\Bigr)$$

## 3. Uncertainty Thresholds, Quarantine, and Time Separation

Apply four filters to identify useful DFT candidates and isolate structural failures.

1. **Lower trigger bounds**. Use any of these example thresholds.
   - $\sigma_{F,\max}^{\text{mobile}} \ge 0.30\ \text{eV/\AA}$, $\sigma_{F,\text{rms}}^{\text{mobile}} \ge 0.060\ \text{eV/\AA}$, or $\sigma_{E,\text{cent}} \ge 0.070\ \text{eV}$.
   - Calibrate these values against validation errors for the system and atom-count range.
2. **Upper limits for structural failures**. Send failures to `quarantine/`.
   - Very high disagreement, such as $\sigma_{F,\max}^{\text{mobile}} > 1.50\ \text{eV/\AA}$, or atomic collisions such as `min_mic_dist < 0.75 Å` indicate severe extrapolation or an unphysical structure.
   - Log these frames in `quarantine/quarantine.csv` and `quarantine.extxyz` for diagnosis and continue screening. Reserve DFT for other candidates because failed geometries commonly cause SCF problems and have little training value.
3. **Minimum time separation (`MIN_COOLDOWN_FS`)**. Space selections from one trajectory by at least the chosen interval, for example `150 fs`, to avoid repeatedly sampling the same local configuration during a several-picosecond event.
4. **Global geometry deduplication and frame checks**. Match steps and times in `trajectory.extxyz` and `uncertainty.csv`. Read only complete newline-terminated frames to avoid concurrent write issues. Verify total and fixed atom counts, and deduplicate aligned geometries against collected frames using SHA-256 fingerprints.

## 4. SOAP Pruning Under a Labeling Budget (`soap_prune`)

When exploration produces too many candidates, such as `unclaimed_pending > SOAP_PRUNE_TRIGGER` or near `MAX_TOTAL_AL_FRAMES`, prune by FPS with the same role-resolved SOAP descriptors as stage 2.

1. **Reference set**. Use frames already accepted or claimed for DFT in the current round as `ref_feats`. Include the initial dataset if useful.
2. **Cosine-distance FPS**. For each unclaimed candidate in `cand_feats`, compute its nearest distance to `ref_feats`. Iteratively retain farthest points until reaching the target fraction, for example 50%. This preserves uncertain configurations farthest from already covered space.
3. **Non-destructive pruning**. Coordinate DFT workers with `claim.lock` and a shared state lock. Write `pruned.json` to withdraw candidates and free budget while preserving structures and metadata. Keep original allocation order until the pruning threshold is reached.

After screening and optional pruning, prepare unlabeled `input.extxyz`, element-sorted `POSCAR`, `meta.json` with `order` and a `science` summary, and `manifest.csv` under `frames/<al_index>/`. Continue to DFT labeling and merging in stages 3 and 6.
