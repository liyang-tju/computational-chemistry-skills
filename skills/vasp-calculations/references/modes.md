# Calculation Modes

## 1. Single Point

Add these settings to the shared electronic settings for energy and force labels or electronic properties at a fixed geometry.

```ini
SYSTEM = single_point
PREC   = Normal
IBRION = -1
NSW    = 0
```

- **Energy conventions in `OUTCAR`**
  - `free  energy   TOTEN` is the electronic free energy $F = E - T_{\text{el}}S_{\text{el}}$, consistent with the atomic forces.
  - `energy(sigma->0)` is the zero-smearing extrapolation $E(\sigma\to0)$ for static comparisons using that convention. For joint energy and force labeling at finite smearing, use `TOTEN` to pair with analytical forces. Record the zero-smearing value separately if needed.
- Select outputs for the task. Energy and force calculations can use `LWAVE = .FALSE.` and `LCHARG = .FALSE.`. Enable `LWAVE` to reuse wavefunctions and `LCHARG` to write `CHGCAR`.
- Use the relevant static outputs for [Bader charges](#8-bader-charges) and [work functions](#9-work-functions).

## 2. Geometry Optimization

Add these settings to the shared settings. This example is the final fixed-cell relaxation stage for a Cu(100) slab in vacuum.

```ini
SYSTEM = geo_opt
PREC   = Accurate
EDIFFG = -0.02
IBRION = 2
ISIF   = 2
NSW    = 400
POTIM  = 0.2
```

- `IBRION = 2` uses conjugate gradients and `ISIF = 2` holds the cell fixed. `EDIFFG = -0.02` sets a force tolerance of `0.02 eV/Å`. `NSW` limits ionic steps. [VASP ionic updates](https://vasp.at/wiki/IBRION) · [Force convergence](https://vasp.at/wiki/EDIFFG)
- For staged optimization, record precision and stopping criteria for each stage. Transfer positions from a complete `CONTCAR` and check `Selective dynamics`. Save wavefunctions or charge densities according to the intended electronic restart.
- Check `reached required accuracy` in `OUTCAR`, final ionic-step SCF convergence, and maximum force on mobile degrees of freedom. A run can reach `NSW` before satisfying the force criterion.

## 3. Ab Initio Molecular Dynamics (AIMD)

Add these settings to the shared electronic settings. A typical setup uses a Γ-centered `1 × 1 × 1` mesh and the Γ-only VASP build for acceleration.

```ini
SYSTEM = aimd_nvt
PREC   = Normal
IBRION = 0
ISIF   = 2
NSW    = 25000
POTIM  = 1.0
TEBEG  = 300
TEEND  = 300
MDALGO = 2
SMASS  = 0
NBLOCK = 1
LDIPOL = .TRUE.
IDIPOL = 3
LCHARG = .FALSE.
LWAVE  = .FALSE.
LVHAR  = .FALSE.
```

- `MDALGO = 2` uses Nosé–Hoover NVT. With `SMASS = 0`, VASP chooses the Nosé mass. `POTIM = 1.0` is in fs, so 25,000 steps correspond to 25 ps. `NBLOCK = 1` writes one `XDATCAR` frame per step. Report actual duration from completed steps and valid frames. [MDALGO](https://vasp.at/wiki/MDALGO) · [NBLOCK](https://vasp.at/wiki/NBLOCK)
- Preserve fixed-layer constraints and chosen atomic masses in `POSCAR`. When setting random seeds explicitly, record one per independent replica. The reference GPU settings are `KPAR = 1`, `NCORE = 1`, and `NSIM = 32`. Verify them with the intended build and resources.
- For a continuous restart, transfer coordinates, velocities, and applicable predictor-corrector state from a healthy, complete `CONTCAR`. To read `WAVECAR`, enable `LWAVE` in the previous segment and choose a compatible `ISTART` for the continuation. For an ensemble change or velocity reset, handle velocity and predictor-corrector blocks according to the VASP format and record the change of state. [CONTCAR](https://vasp.at/wiki/CONTCAR)
- For charged, implicit-solvent, or constant-potential AIMD, set the electron count, solvent response, and potential reference explicitly. See `$constant-potential-calculations` for patches and outputs. Verify actual settings in `OUTCAR`, final step and SCF in `OSZICAR`, trajectory completeness, and temperature and energy throughout.

## 4. Constrained Dynamics and Slow Growth (Blue Moon)

- With native VASP `ICONST` and `INCAR` (such as `MDALGO = 2`) or a patched interface such as PLUMED or a constraint module, check the following.
  - Specify the coordinate type in `ICONST`, such as bond length `R`, coordination `S`, or angle `A`, and its status. Use `0` for a SHAKE constraint and extract the constraint forces or Lagrange multipliers from `REPORT`.
  - Verify the installed build's `REPORT` format, force sign convention, and required Blue Moon metric corrections. Map columns explicitly if outputs come from different versions.
  - Allow enough equilibration and sampling at each CV window. Use separate window directories and define the equilibrated interval for integration.

## 5. NEB and CI-NEB

- Optimize IS and FS with the same cell and electronic protocol. Check elements, atom order, and fixed degrees of freedom. Align periodic images before interpolation and inspect minimum-image distances, connectivity, and constraints. Use subdirectories `00`, `01`, and so on with one `POSCAR` per image. `IMAGES` counts only intermediate images, so `IMAGES = 5` uses `00` through `06`. Share `INCAR`, `POTCAR`, and `KPOINTS` from the parent.
- This template starts a fixed-cell NEB with native VASP and uses the same electronic parameters and precision as the endpoints. A negative `SPRING` enables nudging. Use `IBRION = 3` and `SMASS = 2` for initial convergence, then tune the optimizer and `POTIM` for path stability. [VASP NEB](https://vasp.at/wiki/Nudged_elastic_bands)

```ini
IMAGES = 5
SPRING = -5
ISIF   = 2
IBRION = 3
SMASS  = 2
POTIM  = 0.1
NSW    = 200
EDIFFG = -0.02
```

- With a verified VTST build, set `POTIM` to `0`, omit `SMASS`, and set `ICHAIN = 0` and `IOPT = 3`. Start with `LCLIMB = .FALSE.` for standard NEB. Once the path stabilizes, use a separate `LCLIMB = .TRUE.` stage to converge the climbing image. With equal MPI groups, the total rank count must be divisible by `IMAGES`. Verify per-group `KPAR` and inspect the logs. [VTST NEB](https://henkelmangroup.github.io/vtsttools/neb.html) · [VTST optimizers](https://henkelmangroup.github.io/vtsttools/optimizers.html)
- Check electronic convergence and final path forces for each image. Inspect image spacing, continuity, and the highest-energy region. Obtain endpoint energies separately under the path protocol and report relative energies and forward and reverse barriers. Refine candidate transition states with Dimer or check them with localized frequencies.

## 6. Dimer Transition-State Search

Start from an aligned high-energy NEB image or another plausible candidate. Build the initial direction from an NEB tangent, a known imaginary mode, or a defined reaction displacement. Check atom order, periodic images, coordinate representation, and fixed components. Use the same electronic protocol as the IS and FS.

For the **native VASP improved dimer**, add a blank line after the `POSCAR` coordinates, followed by three direction components per atom. When starting from a frequency mode, remove mass weighting to obtain displacements. [VASP improved dimer](https://vasp.at/wiki/Improved_dimer_method)

```ini
IBRION = 44
ISIF   = 2
NSW    = 200
EDIFFG = -0.02
```

For **VTST Dimer**, put the initial direction in `MODECAR` in atom order. `neb2dim.pl` can extract a candidate and direction from a converged NEB. VTST `IOPT = 2` selects conjugate gradients. Run Dimer in a single-structure directory. [VTST Dimer](https://henkelmangroup.github.io/vtsttools/dimer.html)

```ini
ICHAIN = 2
IBRION = 3
POTIM  = 0
IOPT   = 2
ISIF   = 2
NSW    = 200
EDIFFG = -0.02
```

Check SCF convergence, ionic forces, final curvature, and mode. Verify one significant imaginary frequency in the intended reaction direction within the active degrees of freedom. If needed, displace slightly in both directions and relax each structure to confirm connection to the intended IS and FS.

## 7. Finite-Difference Frequencies

Make a separate frequency directory from a converged minimum or candidate transition state. This local template uses `IBRION = 5` and `Selective dynamics` to choose Cartesian displacements. For adsorbate-only frequencies, fix the entire substrate. If including surface vibrations, specify which surface atoms are mobile.

```ini
IBRION = 5
ISIF   = 2
NSW    = 1
NFREE  = 2
POTIM  = 0.015
PREC   = Accurate
EDIFF  = 1E-7
```

- Preserve the source structure's chemical state, functional, pseudopotentials, cell, k points, dispersion, and boundary settings. The example `EDIFF` overrides the shared setting for the finite-difference Hessian. `NFREE = 2` uses central displacements $\pm h$, with magnitude `POTIM` in Å. If soft modes are sensitive, test displacement sizes, tighter SCF, or finer grids in controlled runs and record changes. [VASP finite-difference phonons](https://vasp.at/wiki/Phonons_from_finite_differences)
- Verify SCF for every displacement and complete eigenvalues and eigenvectors in `OUTCAR`. `f/i=` identifies imaginary frequencies. Interpret the modes for the chosen active degrees of freedom, since a localized surface Hessian depends on which atoms move. Check minima for significant imaginary modes and transition states for a unique imaginary reaction mode. Diagnose small imaginary modes using geometry, mode shape, and numerical sensitivity. Use `$che-calculation` for ZPE and entropy corrections.

## 8. Bader Charges

Use the section 1 electronic settings on the target structure with `LAECHG = .TRUE.` and `LCHARG = .TRUE.`. Obtain `CHGCAR`, `AECCAR0`, and `AECCAR2` from the same SCF run and verify the cell, atom order, and fine FFT grid match. If absolute charges or small differences are grid-sensitive, use separate single points to test `NGXF`, `NGYF`, and `NGZF` convergence. [VASP LAECHG](https://vasp.at/wiki/LAECHG)

In a new analysis directory, use the VTST script and Bader program to build the reference density and integrate charges.

```bash
chgsum.pl AECCAR0 AECCAR2
bader CHGCAR -ref CHGCAR_sum
```

- `CHGCAR_sum` defines the partition reference. `CHARGE` in `ACF.dat` gives the valence count $N_i$ integrated from `CHGCAR`. Calculate net charge as $q_i/e=Z_{\mathrm{VAL},i}-N_i$ using each species' `ZVAL` from the actual `POTCAR`. Positive values denote electron depletion relative to the neutral pseudopotential valence count. [Bader program](https://github.com/henkelmangroup/bader) · [VTST scripts](https://henkelmangroup.github.io/vtsttools/scripts.html)
- Map `ACF.dat` rows to structure indices. Check finite results and compare the integrated electron total, including any reported vacuum charge, to `NELECT`. Then aggregate over the requested adsorbate, solvent, or substrate groups. For state differences, report subtraction order and the net-charge convention.

## 9. Work Functions

- For vacuum slabs, use the self-consistent single point in section 1 and enable `LVHAR = .TRUE.` to write the Hartree and ionic electrostatic potential. For asymmetric neutral slabs that require dipole correction, set `LDIPOL` and `IDIPOL` for the actual normal direction and check the plateau.
- From the same calculation, average `LOCPOT` over the two in-plane directions. Choose $V_{\mathrm{vac}}$ on a flat, field-free, charge-free plateau on the target side, away from the surface, dipole discontinuity, and sloped regions. Use the same calculation's `E-fermi` to obtain $\Phi=V_{\mathrm{vac}}-E_F$ in eV. For asymmetric slabs with two resolved plateaus, report each side's normal direction, sampling interval, and work function. [VASP work functions](https://vasp.at/wiki/Computing_the_Workfunction)
- If supported, use `LVACPOTAV` to obtain both vacuum values in `OUTCAR` and cross-check them against the planar-averaged profile. When there is no resolvable vacuum plateau, report the bulk-solvent reference or aligned chemical potential appropriate to the model. For snapshot comparisons, retain per-frame $V_{\mathrm{vac}}$, $E_F$, $\Phi$, and sampling windows. [VASP LVACPOTAV](https://vasp.at/wiki/LVACPOTAV)
