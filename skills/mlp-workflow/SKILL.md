---
name: mlp-workflow
description: "End-to-end active-learning MLP workflow: (1) foundational-MLP pre-sampling with free MD and reaction-coordinate umbrella windows across compositions and cell sizes, (2) topology filtering, cooldown/hash deduplication, role-pooled SOAP/QUESTS/FPS selection and multivariate coverage auditing, (3) pilot-benchmarked DFT single-point labeling with POSCAR order provenance, raw forces and SCF review, (4) single or committee MACE/CP-MACE training and validation, and (5-6) committee uncertainty active learning (mobile-atom force disagreement, baseline-centered energy std, quarantine, SOAP pruning) feeding back to DFT relabeling and merged dataset updates."
---
# Active Learning for Machine-Learning Potentials

Use a six-stage active-learning cycle for machine-learning potentials (MLPs). Presample with a foundation model, select and audit configurations, pilot and label with DFT, train and test a single model or committee, collect and prune uncertain frames, then label and merge those frames. Start at any stage. Preserve provenance with `dataset_index`, input hashes, and atom-order mappings.

> **Electronic states in constant-potential models**. For standard fixed-electron or neutral DFT, use the time separation and geometry deduplication already applied during selection. For variable-charge or constant-potential models such as `FermiMACE`, use `$constant-potential-calculations` to distinguish identical geometries with different `NELECT` or `potential` values.

## 1. Workflow Stages and Starting Inputs

| Stage | Main tasks | Inputs and outputs | Reference |
|---|---|---|---|
| **1. Initial structures and presampling** | Use a foundation model such as `mace-mp` or `mace-mh` for unbiased MD across temperatures, compositions, and sizes, and for reaction-coordinate umbrella windows | Initial structures and `manifest.csv` $\rightarrow$ candidate `trajectory.extxyz` | [sampling-and-selection.md](references/sampling-and-selection.md) |
| **2. Selection and coverage audit** | Filter topology, enforce time separation, remove duplicates, calculate role-resolved SOAP or QUESTS, and prioritize states in FPS. Audit multivariate coverage. | Candidate pool $\rightarrow$ `selected.extxyz`, `frames.csv`, `coverage.csv` | [sampling-and-selection.md](references/sampling-and-selection.md) |
| **3. DFT labeling and validation** | Run a small `pilot` across node and memory configurations. Sort `POSCAR` by element, record `order`, restore the source order, and verify raw forces and SCF. | `selected.extxyz` $\rightarrow$ `labeled.extxyz`, `review.csv`, `verification.json` | [dft-labeling.md](references/dft-labeling.md) |
| **4. Training and validation** | Clean and merge labels, fix `E0s`, and train independent seeds for a `MACE` committee. Evaluate exported `.model` files and run short NVE and NVT tests. | `labeled.extxyz` $\rightarrow$ per-seed `.model`, accuracy and MD checks | [training-and-validation.md](references/training-and-validation.md) |
| **5. Committee uncertainty sampling** | Run MD or OPES with `AverageForceCalculator`. Track mobile-atom force disagreement and centered energy disagreement `dE_cent`. Quarantine failed structures and prune excess candidates with SOAP. | Production trajectory and `uncertainty.csv` $\rightarrow$ `frames/` and `quarantine/` | [active-learning.md](references/active-learning.md) |
| **6. Relabeling and merging** | Repeat stage 3 under the established protocol. Verify settings and label compatibility and restore the source order before merging. | `al_labeled.extxyz` and initial `labeled.extxyz` $\rightarrow$ `merged_labeled.extxyz` | [dft-labeling.md](references/dft-labeling.md) |

Confirm two items before starting.
1. **Current stage and resources**. Identify input paths and the target model or engine, such as the MACE version and VASP configuration. Confirm submission authorization when using a cluster.
2. **Scientific protocol**. Specify energy and force conventions (such as `TOTEN` with `apply_constraint=False` for raw DFT forces on fixed atoms), elements shared across system sizes, and whether a separate generalization test set is needed.

## 2. Requirements Across Stages

- **Clear stale labels**. In copies for selection, MD initialization, or relabeling, clear the calculator and use `write_results=False` as needed. Remove old energy, force, and stress keys from `atoms.info` and `atoms.arrays`, including the applicable `REF_*` or custom keys. Keep provenance, electronic-state metadata, and constraints. Preserve reference labels in validation data.
- **Preserve atom order**. Stable-sort by element for DFT when needed, such as to match `POSCAR` to `POTCAR`. Record the `order` mapping per frame and invert the permutation to restore `REF_forces` to the original `input.extxyz` order.
- **Protocol compatibility**. Check functional, pseudopotentials, dispersion, grids, smearing, electronic state, and energy and force conventions using actual inputs and logs. Version incompatible labels separately. Treat `science` hashes as provenance and report mismatches for information only.
- **Screen structural failures**. Set lower uncertainty thresholds and upper plausibility limits, including minimum interatomic distances. Send severely distorted structures to `quarantine/` for diagnosis and reserve DFT for plausible candidates.

## 3. References and Upstream Repositories

- **Stages 1–2** for presampling, role-resolved selection, and coverage auditing. [Sampling and Selection](references/sampling-and-selection.md)
- **Stages 3 and 6** for `pilot` runs, DFT queues, atom-order restoration, and merge validation. [DFT Labeling](references/dft-labeling.md)
- **Stage 4** for MACE committees, evaluation of exported models, and MD and generalization tests. [Training and Validation](references/training-and-validation.md)
- **Stage 5** for committee `dE_cent` and force disagreement, quarantine, and SOAP pruning. [Active Learning](references/active-learning.md)

Useful upstream projects are listed below.

| Tool or method | GitHub repository |
|---|---|
| MACE for equivariant force-field training, evaluation, and committee inference | [ACEsuit/mace](https://github.com/ACEsuit/mace) |
| DScribe for local descriptors such as role-resolved SOAP | [SINGROUP/dscribe](https://github.com/SINGROUP/dscribe) |
| QUESTS for model-free local-environment coverage and MSC compression | [dskoda/quests](https://github.com/dskoda/quests) |
| CP-MACE / FermiMACE for constant-potential or variable-electron models | [yuanyue-liu-group/CP-MACE](https://github.com/yuanyue-liu-group/CP-MACE) |
