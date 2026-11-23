# Charges and Topologies

## 1. Verify Quantum Inputs and Wavefunction Exports

- **Consistency across stages.** Verify that the `.fchk`, `.wfx`, or `.molden` used for ESP/RESP fitting corresponds to the converged geometry and requested conformer, charge, and multiplicity.
- Example commands for inspecting frequencies.
  - Gaussian, `grep "Frequencies --" job.log | head -n 5`. Check the complete vibrational spectrum for imaginary modes.
  - ORCA, `grep -A 15 "VIBRATIONAL FREQUENCIES" job.out`. For a nonlinear molecular minimum, check for six near-zero translational and rotational modes and positive frequencies starting with the seventh mode. Inspect the complete spectrum.

## 2. Two-Stage RESP and Multiconformer Fits

Record the details required to reproduce the RESP charges.
1. **ESP level.** For example, HF/6-31G* follows the historical AMBER/GAFF convention, while another protocol might specify B3LYP/def2-TZVP with PCM. Keep the quantum level and surface grid (MK or CHELPG) consistent across comparable fits.
2. **Restraints for classical two-stage RESP.**
   - Stage 1 uses a weak hyperbolic restraint (for example, `qwt = 0.0005` a.u.) and fits all nonequivalent atoms to determine polar-group charges.
   - Stage 2 fixes polar heavy-atom charges, applies a stronger restraint (for example, `qwt = 0.001` a.u.) to nonpolar methyl or methylene groups (`CH3`/`CH2`), and equates symmetry-equivalent hydrogen charges.
3. **Joint multiconformer fitting.** Fit several representative low-energy structures together for flexible molecules or polymers with side chains, and record conformer weights. Averaging independent fits defines a different protocol.
4. **Tools.** For Multiwfn, verify the current menu on one sample before recording `answers.txt`. For AmberTools, use `respgen` and `resp` to check equivalence definitions in `.qin` and the total charge in `.chg`.

## 3. Extract Head, Internal, and Tail Polymer Templates

For a polymer with $N$ repeat units, a common approach is to fit charges on an oligomer such as the capped trimer `Cap-Head-Monomer-Tail-Cap`, then split it into templates.
- **Cap charges and residual adjustments.** Constrain the cap-group total charge during RESP to `0` or a known end-group charge, or distribute residual charge to junction atoms by a documented rule after cap removal. Make the internal unit sum exactly to its intended integer charge (`0.0000` for a neutral chain).
- **Check assembly.** Assemble two or three units and check atom count, total charge, junction bond parameters, torsions crossing the junction, and unique atom numbering.

## 4. Force-Field Conventions

| Force-field family | 1–4 LJ scaling (`fudgeLJ`) | 1–4 electrostatic scaling (`fudgeQQ`) | Nonbonded mixing | Potential forms and units |
|---|---|---|---|---|
| **AMBER / GAFF / GAFF2** | `0.5` | `1/1.2 ≈ 0.8333` | Lorentz–Berthelot (arithmetic $\sigma$, geometric $\epsilon$) | Check the $r_{\min}/2$ and $\sigma$ conventions ($r_{\min}=2^{1/6}\sigma$) |
| **OPLS-AA** | `0.5` | `0.5` | Geometric for $\sigma$ and $\epsilon$ | Torsions commonly use Ryckaert–Bellemans or Fourier forms |
| **CHARMM** | `1.0` (or specific 1–4 LJ parameters) | `1.0` | Lorentz–Berthelot (`arithmetic`) | Includes Urey–Bradley 1–3 terms and CMAP |

- **Controlled sensitivity comparisons.** To study the effect of charge distribution on adsorption, hold other parameters fixed and compare charge models. Label the result as a sensitivity study with a specific protocol.
- **Interface interactions.** Interpret atom-pair LJ interactions alongside conformational changes, competition with solvent hydration, and whole-molecule adsorption geometry.
