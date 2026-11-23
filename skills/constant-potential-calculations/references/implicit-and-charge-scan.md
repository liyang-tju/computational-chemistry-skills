# Charge Scans, Implicit Constant Potential, and CPTI

## 1. Fixed-Charge `NELECT` Scans and Grand-Potential Fits

Use `LSOL = .TRUE.` with VASPsol (`ISOL = 1`) or nonlinear VASPsol++ (`ISOL = 2`, `C_MOLAR = 1.0`, `R_ION = 4.0`, `TAU = 0`). The scan needs no dedicated constant-potential patch. [henniggroup/VASPsol](https://github.com/henniggroup/VASPsol) · [VASPsol/VASPsol](https://github.com/VASPsol/VASPsol)

### Procedure
1. Read the `ZVAL` for each element in `POTCAR` and use the `POSCAR` counts to calculate the neutral valence electron total $N_0$.
2. Choose several offsets $\Delta N_e$ symmetrically around neutrality or to cover the target potential range. A typical scan uses 5–9 points, such as `-1.0, -0.5, 0.0, +0.5, +1.0`. Set `NELECT = N_0 + delta_N` with `EFERMI_ref` unset and `LDIPOL` disabled. Use directory labels such as `dm`/`dp` or `n`/`p` and document whether they refer to excess electrons or physical charge.
3. Collect states with converged SCF and ionic optimization. Extract the following quantities.
   - $E(\Delta N_e)$ using one energy convention throughout (`TOTEN` or `energy without entropy` / `sigma->0`).
   - The Fermi level $E_F$ and the `FERMI_SHIFT` from `OUTCAR` or the log.
   - The electron chemical potential $\mu_e = E_F + \text{FERMI\_SHIFT}$.
   - The electrode potential $U_{\text{SHE}}=(E_{F,\text{ref}}^{\text{SHE}}-\mu_e)/e$, or $U_{\text{vs PZC}}=[\mu_e(0)-\mu_e(\Delta N_e)]/e$ relative to the same interface at zero charge. Use aligned chemical potentials for both terms. Compare reaction states and barriers at the same potential on a common scale.
4. Apply the Legendre transform and fit a quadratic.
   $$\Omega(\Delta N_e) = E(\Delta N_e) - \Delta N_e \cdot \mu_e$$
   - Fit $\Omega(U) = a_\Omega U^2 + b_\Omega U + c_\Omega$ directly, or fit $E(\Delta N_e) = a_E \Delta N_e^2 + b_E \Delta N_e + c_E$ and map it analytically with $\mu_e = \partial E/\partial \Delta N_e = 2 a_E \Delta N_e + b_E$. This yields a continuous $\Omega(U)$ curve and differential capacitance $C = 1 / (2 a_E)$ in `e/V`. Divide by interface area and convert to $\mu\text{F/cm}^2$.
   - Check for $a_E > 0$ (positive capacitance), $a_\Omega < 0$ (downward-opening parabola), and high $R^2$. Investigate adsorbate reconstruction, solvent desorption, and unconverged SCF if points depart substantially from the parabola.

### ASE `FCP` Automation
To adjust `NELECT` automatically with `ase.calculators.FCPelectrochem.FCP`, pass `innercalc` with `lsol=True`, the target potential `U`, `work_ref` (a positive absolute SHE work function, such as `4.6`), `NELECT0`, and the initial `NELECT` explicitly. [hellozhaoming/FCP-vasp-ase](https://github.com/hellozhaoming/FCP-vasp-ase)

## 2. Native VASPsol++ Constant Potential (`EFERMI_ref`)

VASPsol++ adjusts screening charge inside SCF to approach the target Fermi level. Use it for single points, relaxation, or CI-NEB and Dimer transition-state searches. [VASPsol/VASPsol](https://github.com/VASPsol/VASPsol)

```ini
LSOL = .TRUE.
ISOL = 2
C_MOLAR = 1.0
R_ION = 4.0
TAU = 0
EFERMI_ref = -4.66    # U_SHE = 0 V. Use -3.16 for a target U_SHE = -1.5 V.
EFERMI_tol = 0.01     # Fermi-level convergence tolerance (eV)
LDIPOL = .FALSE.      # Keep dipole correction disabled and leave NELECT unfixed.
```

- With `EFERMI_ref < 0`, VASPsol++ already includes `-q_sol * EFERMI_ref`. Compute barriers or $\Delta G(U)$ from differences of the reported grand potentials directly. This applies the $\Delta N_e \cdot E_{F,\text{ref}}$ correction once.
- **CI-NEB and Dimer**. Obtain an initial path or transition state with a standard or neutral calculation and converge the imaginary frequency before switching to constant-potential `EFERMI_ref` with `ICHAIN = 2` (Dimer, with `MODECAR`) or CI-NEB. Remove incompatible or irrelevant `NPAR`, `NSIM`, `IMAGES`, `SPRING`, and `LCLIMB` parameters for Dimer.
- **Check for omitted partial-core-density (`DENCOR`) shape forces**
  - The original implementation assumes pseudopotential partial-core density has no overlap with the cavity boundary. Its atomic forces omit the explicit derivative of the partial-core density with respect to the cavity, dielectric, and ionic response potential, $\mathbf{F}_I^{\text{shape}} = -\int v_{\text{shape}}(\mathbf{r}) \nabla_{\mathbf{R}_I} n_{c,I}\,d^3r$.
  - For new elements, pseudopotentials, or force-sensitive tasks such as optimization, TS searches, and AIMD, check surface or adsorbate atoms in representative structures by central finite differences. Keep inputs, cell, and FFT grid fixed and compare multiple small displacements, such as $h = 0.002\text{–}0.005\,\text{\AA}$.
    $$F_{I\alpha}^{\text{FD}} = -\frac{\Omega(\mathbf{R} + h\mathbf{e}_{I\alpha}, \mu) - \Omega(\mathbf{R} - h\mathbf{e}_{I\alpha}, \mu)}{2h}$$
    If analytical and finite-difference forces differ systematically beyond numerical discretization error, include the shape force or use fixed-charge finite differences or another validated route.

## 3. CPTI (Constant-Potential Thermodynamic Integration)

Use CPTI to compute a free-energy curve along a reaction coordinate in explicit solvent when no automatic constant-potential MD engine is available. [Yanggang-Wang-Group/CPTI](https://github.com/Yanggang-Wang-Group/CPTI)
1. At each discrete CV window, run constrained dynamics (slow growth or Blue Moon) at the current fixed `NELECT`.
2. Sample frames at fixed intervals and calculate **Bader charges** for the surface atoms with VASPsol. Convert the excess surface charge density $\sigma$ to instantaneous potential $U = \sigma / C_{\text{EDL}} + U_{\text{PZC}}$.
3. Iteratively adjust `NELECT` in each window using the linear-response slope until every window approaches the target potential, such as $|U - U_{\text{target}}| < 0.05\,\text{V}$.
4. Use trapezoidal integration of the mean force $\langle \partial F/\partial \xi \rangle$ from the final converged sampling segment to obtain the constant-potential free-energy profile.
