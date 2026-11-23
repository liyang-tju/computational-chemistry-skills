# Inputs and Runtime

## 1. POTCAR and Element Mapping

- **Species order**. Match the element groups on `POSCAR` line 6 to the `POTCAR` `TITEL` entries in order. For repeated groups such as `Pt O Pt`, preferably regroup the atoms before generating `POTCAR`, or concatenate pseudopotentials in the exact group order.
- **Pseudopotential variants**. Elements can have standard, `_pv`, `_sv`, `_h`, `_s`, or GW variants (for example, `O`, `O_s`, and `O_h`, or `Fe` and `Fe_pv`). Use the same combination within a comparison series and record `TITEL` entries in `protocol_notes.md`.
- **Plane-wave cutoff**. A common starting point is `ENCUT` of at least 1.3 times the largest `ENMAX` in `POTCAR`. Follow the project's agreed protocol when specified, such as `400/450/520 eV`.

## 2. Generate KPOINTS with VASPKIT

Copy the target `POSCAR` into a separate preparation directory and run `vaspkit` there. Enter `102` to generate an SCF mesh. Select `2` for a Γ-centered mesh or `1` when the protocol calls for Monkhorst–Pack. Enter a reciprocal-space resolution such as `0.04`. The command below supplies the same menu inputs. [VASPKIT tutorial](https://vaspkit.com/tutorials.html#generate-kpoints)

```bash
printf '%s\n' 102 2 0.04 | vaspkit
sed -n '1,5p' KPOINTS
```

- The example `0.04` is in $2\pi\,\text{\AA}^{-1}$. Choose the resolution for the cell and observable, then inspect the actual mesh. For Γ-only, enter `2` followed by `0` and verify `1 1 1`.
- Check mesh type, sampling in each direction, and shifts in `KPOINTS`. Use `1` along a slab's vacuum direction, for example `N_x N_y 1` for z vacuum. Preserve the scheme and shifts when reusing a verified mesh. Use the same verified `KPOINTS` within a comparison series or across NEB images.
- Task `102` may also write `POTCAR` depending on version or configuration. Copy only the verified `KPOINTS` to the calculation directory and assemble pseudopotentials as described in section 1.
- VASP samples the mesh from `KPOINTS` when the file exists. When generating a mesh from `INCAR` instead, `KSPACING` uses $\text{\AA}^{-1}$. VASPKIT `0.04` corresponds to a nominal `0.251 Å⁻¹`. Verify the actual mesh before use. [VASP KSPACING](https://vasp.at/wiki/KSPACING) · [VASP KGAMMA](https://vasp.at/wiki/KGAMMA)

## 3. Executable Variants and GPU/MPI Layout

- **Executable selection**
  - `vasp_std` is the general complex-valued build for arbitrary k points.
  - `vasp_gam` is the real-valued Γ-only build. Use a Γ-centered `1 1 1` mesh.
  - `vasp_ncl` supports noncollinear spin and spin–orbit coupling (`LNONCOLLINEAR = .TRUE.` or `LSORBIT = .TRUE.`).
- **Parallel settings (`KPAR`, `NCORE`, and `NPAR`)**
  - Prefer a proven script for the available cluster and VASP build. Verify that settings such as one rank per GPU and the selected `NCORE` suit the actual node and executable.
  - OpenACC GPU builds commonly use one MPI rank per GPU. Set `KPAR` to a divisor of the MPI ranks and distribute irreducible k points evenly. Follow the build's `NCORE` requirements, then check `OUTCAR` for MPI ranks, `distrk`, and GPU binding.
- **Patches and keywords**. Verify that the executable includes any requested VTST (`IOPT`, `ICHAIN`), VASPsol (`LSOL`, `EB_K`), or CP-VASP Fermi-level control features. VASP can silently ignore unrecognized `INCAR` settings.

## 4. Restarts, Stops, and Troubleshooting

- **Restart compatibility**
  - `ISTART = 1` reads a compatible `WAVECAR` and resets the basis if the cell or `ENCUT` changes. To continue the same variable-cell optimization with a constant basis, use `ISTART = 2` as documented by VASP. Verify compatible k points, bands, and spin representation and confirm the read in the log. To reuse `CHGCAR`, also check atom and pseudopotential mapping, cell, grid, and spin-density representation.
  - If SCF failure or scattered atoms distorted the previous structure, recover the last healthy ionic step or a verified initial structure.
- **Controlled stopping (`STOPCAR`)**
  - Write `LSTOP = .TRUE.` for the preferred stop after the current ionic step, allowing complete `CONTCAR` and `WAVECAR` output.
  - Write `LABORT = .TRUE.` for a stop after the current electronic step if a run is stuck. Final forces may be unconverged.
- **Output checks**
```bash
# Check ionic convergence and whether the electronic iteration count reached NELM.
grep "reached required accuracy" OUTCAR
awk '
    /^[[:space:]]*[[:alnum:]_-]+:[[:space:]]+[0-9]+/ {step=$2}
    /^[[:space:]]*[0-9]+[[:space:]]+.*F=/ && step != "" {
        print "last_elec_iter=", step, $0
        step=""
    }
' OSZICAR | tail -n 10
```
