# Stages 3 and 6. DFT Labeling, Pilot Runs, and Dataset Merging

## 1. Benchmark a Small `pilot` Before Production

Run a `pilot` on different node types and parallel settings such as `KPAR`, `NCORE`, and `NSIM` before labeling thousands of frames. Select a small representative set, typically 6–8 frames, covering the largest system and the main compositions and reaction states.
- **Memory headroom**. Read peak memory from the scheduler's `cgroup`. The estimate in a single `OUTCAR` covers one MPI rank and can substantially underestimate node use. Verify sufficient headroom, typically `memory.peak / limit_bytes` `< 85%`, and check for OOM events.
- **Numerical agreement**. Compare the same frame across node configurations.
  - Total-energy difference $|\Delta E| \le 1\ \text{meV}$
  - Maximum atomic force-vector difference $\max \|\Delta \mathbf{F}_i\| \le 0.01\ \text{eV/\AA}$
- **Throughput**. Calculate frames per node-hour from measured wall time, estimate overall cost, and build the production queue.

## 2. Record the Scientific Protocol and `POSCAR` Atom Order

- **Record the `science` protocol**. Save scientific `INCAR` settings, the `KPOINTS` mesh, VASP version, and `POTCAR` identifiers. Record SHA-256 for provenance as needed. Determine compatibility from actual settings and label definitions and version incompatible results separately.
- **Stable sorting and inverse mapping**
  - Stable-sort each frame by element before writing `POSCAR` to reuse consistent `POTCAR` orders. Verify the expected total valence count `nelect = sum(ZVAL)`.
  - Save the exact `order` indices, `poscar_sha256`, and `potcar_sha256` in `queue.json` for initial labeling or `meta.json` for stage 6.
  - Invert the permutation to restore `REF_forces` to the original `input.extxyz` atom order. Check positions, `cell`, `pbc`, and `move_mask` against that file, using a tolerance of about `5e-9`.

## 3. Concurrent Queues and Separate Retry Directories

- **Separate attempts**. Use `primary/` and a separate `retry_v2/` for retries after failure or timeout under each frame directory, for example `frames/0001/`. Keep a self-contained set of `POSCAR`, `POTCAR`, `KPOINTS`, `INCAR`, and logs in each attempt. Preserve original runs.
- **Claim locks**. Use a shared `flock` lock for concurrent workers and skip frames with an accepted `accepted.json`. Preserve logs from failed attempts and retry separately with predefined robust settings, such as `ALGO = Normal` or `All`, smaller `AMIN` or `BMIX`, or larger `NELM`.

## 4. Validate Each Frame, Raw Forces, and SCF

Check the following for every frame, in addition to exit code `0`.
1. **Convergence and finite values**. Require normal completion, final electronic iteration count `< NELM`, `REF_forces` shape `(N, 3)`, and finite energies and forces with no `NaN` or `Inf`.
2. **Energy and raw force conventions**
   - For Gaussian smearing (such as `ISMEAR = 0` and `SIGMA = 0.05`) in metallic or electrochemical systems, VASP analytical forces correspond to the free energy (`TOTEN`). Use the matching energy for `REF_energy` with `REF_forces`. Record the zero-smearing `energy(sigma->0)` separately as `energy_sigma0_eV` if needed.
   - When reading an `OUTCAR` with `Selective dynamics` in ASE, request `apply_constraint=False` to retain raw DFT forces for all atoms, including fixed substrate atoms such as Cu. `FixAtoms` would otherwise zero their forces.
3. **Quality review queue (`review.csv`)**. Flag high-risk frames for review even when SCF ends within `NELM`.
   - High iteration count, for example `scf_steps >= 250`.
   - Late SCF energy jumps, for example an increase above `0.10 eV` in one iteration after iteration 20.

## 5. Verify Exported Frames and Merge Stage 6 Labels

- Write a temporary output, read it back, and verify `dataset_index`, atom count, positions, `move_mask`, `REF_energy`, and `REF_forces` frame by frame. Then atomically replace `labeled.extxyz` and write `verification.json` with frame hashes and review flags.
- **Stage 6 relabeling**. Apply the original scientific protocol and validate `al_labeled.extxyz` and `al_results.csv` separately. Compare actual settings, electronic states, and label definitions before writing compatible data to `merged_labeled.extxyz`. Use hash differences for provenance only. Submission, startup, restart, and merging proceed based on the underlying checks.
