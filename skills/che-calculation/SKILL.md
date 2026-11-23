---
name: che-calculation
description: "Calculate static DFT vibrational thermochemistry (ZPE, entropy, VASPKIT/ASE) and Computational Hydrogen Electrode (CHE) reaction free energy diagrams, RHE/SHE shifts, limiting potentials and gas-phase reference corrections. Dynamic enhanced sampling and PMF reconstruction belong to enhanced-sampling."
---
# Computational Hydrogen Electrode (Static Thermodynamics)

Use static DFT results or implicit-solvent and constant-potential single points with localized frequencies to obtain zero-point energy (ZPE) and entropy corrections. Balance proton-coupled electron transfer (PCET) reactions and construct computational hydrogen electrode (CHE) free-energy diagrams and limiting-potential estimates. Use `$enhanced-sampling` for dynamical sampling and PMF reconstruction, and `$constant-potential-calculations` for the electron-reservoir transformation $\Omega(U)$.

## Before Starting

- **Mechanism and species**. List the elementary steps and their initial states (IS), intermediates, transition states (TS), and final states (FS). Balance each step, including the number $n$ of transferred $\text{H}^+ + e^-$ pairs, and record its direction.
- **Thermodynamic conditions and reference scale**. Record $T$, the potential scale (`V vs RHE` or `V vs SHE` with `pH`), and gas-phase partial pressures. To approximate the chemical potential of pure liquid water with saturated vapor, use approximately `0.0317 bar` at 298.15 K.
- **Thermal and solvent corrections**. Choose between localized frequencies with the adsorbate free (VASP `IBRION = 5`) and a rigid approximation. Specify whether to include implicit solvation $\Delta E_{\text{solv}}$, constant-potential $\Omega(U)$, or empirical gas-phase corrections such as those for $\text{CO}_2$/$\text{CO}$ with PBE.

## Workflow

### 1. Prepare and Check Static Frequency Calculations (ZPE and $TS$)

- Start from the converged `CONTCAR` in a separate `freq/` directory with the parent calculation's `KPOINTS`, `POTCAR`, functional, and `ENCUT`. A finite-difference setup can use `IBRION = 5`, `POTIM = 0.015`, `NFREE = 2`, and `EDIFF = 1E-7`. Enable displacements for the adsorbate and selected surface atoms. Fix the remaining degrees of freedom.
- **Imaginary frequencies**
  - Require minima (IS, intermediates, FS) to be free of significant imaginary frequencies. If small imaginary modes arise, such as frustrated adsorbate translations or rotations below $50\,\text{cm}^{-1}$, apply and document one consistent rule across all species, such as a `50 cm⁻¹` cutoff or replacement.
  - Require exactly **one** significant imaginary frequency for a TS, along the reaction coordinate. Exclude that mode from vibrational entropy and ZPE.

### 2. Extract Thermal Free-Energy Corrections

Use `VASPKIT 501` or ASE `HarmonicThermo` for adsorbates. The latter gives a Helmholtz free-energy correction suitable for CHE when the adsorbate $pV$ term is negligible. Use `VASPKIT 502` or ASE `IdealGasThermo` for gas-phase species to include vibrational, translational, rotational, and $pV$ contributions to enthalpy and evaluate entropy at the specified partial pressure. Express the total as $G_{\text{corr}}=\mathrm{ZPE}+\Delta H_{\text{thermal}}-TS$, with $\Delta H_{\text{thermal}}$ defined excluding ZPE.
- Record the total $G_{\text{corr}}(T)$ and the individual $\text{ZPE}$ and $-TS$ terms separately. `E + G_corr` already includes ZPE.
- Verify the rotational symmetry number (`symmetrynumber`), electronic spin degeneracy, and reference pressure of each gas-phase reference ($\text{H}_2$, $\text{CO}$, $\text{CO}_2$, $\text{H}_2\text{O}$).

### 3. Balance CHE Stoichiometry and Verify the Sign of $eU$

Use $\text{H}^+ + e^- \rightleftharpoons \frac{1}{2}\text{H}_2(g)$ to construct the free-energy change of each step. See [Thermochemistry and CHE](references/thermochemistry-and-che.md).
$$\Delta G(U_{\text{RHE}}) = \Delta E_{\text{DFT}} + \Delta E_{\text{solv}} + \Delta G_{\text{corr}} + \Delta G_U$$
- **Check the potential term for each reaction direction**
  - Reduction consuming $n(\text{H}^+ + e^-)$ gives $\Delta G_U = + n e U_{\text{RHE}}$. Negative potentials lower the free-energy change.
  - Oxidation releasing $n(\text{H}^+ + e^-)$ gives $\Delta G_U = - n e U_{\text{RHE}}$. Positive potentials lower the free-energy change.
- For equal proton and electron transfer, $U_{\text{RHE}}$ includes the Nernst pH term for the pair. Account for other species' activities and pH dependence according to the balanced reaction.

### 4. Apply a Consistent Energy Convention

- Standard static CHE applies a linear potential shift of $n e U$ and neglects changes in double-layer capacitance with adsorbate configuration.
- When using $\Omega(U)$ from `$constant-potential-calculations`, which includes capacitive coupling and work-function changes, use transformed energies consistently across states. Apply the electron-reservoir correction only once per electron transfer.

### 5. Report Free-Energy Profiles and Electrocatalytic Metrics

Include all intermediates and elementary steps in the output table.
- Report each $\Delta G$ at $U = 0\,\text{V}_{\text{RHE}}$ and at the target operating potential.
- Let $n_i>0$ denote the number of transferred proton–electron pairs in each electrochemical step. For linear static CHE, $U_L=\min_i[-\Delta G_i(0)/(n_i e)]$ for reduction and $U_L=\max_i[+\Delta G_i(0)/(n_i e)]$ for oxidation. The step that sets this bound is the potential-determining step (PDS). Flag any step with $n_i=0$ and $\Delta G_i>0$ separately because it remains uphill under a linear CHE potential shift.

## References

- See [Thermochemistry and CHE](references/thermochemistry-and-che.md) for VASP adsorbate frequencies, VASPKIT and ASE thermal corrections, CHE sign conventions, and standard-state parameters.

## Deliverables and Validation

1. **`species_thermochemistry.csv`** with $E_{\text{DFT}}$, $E_{\text{solv}}$, $\text{ZPE}$, $-TS$, $G_{\text{corr}}(T)$, the number of imaginary modes, and the reference pressure for each species, including gas-phase references.
2. **`che_profile.csv`** with elementary step stoichiometry, $\Delta G(0\,\text{V})$, $\Delta G(U)$, cumulative reaction free energies, and PDS and $U_L$.
3. **`che_summary.json` or script** recording temperature, pH, RHE or SHE scale, low-frequency cutoff, empirical gas-phase corrections, and the protocol.
