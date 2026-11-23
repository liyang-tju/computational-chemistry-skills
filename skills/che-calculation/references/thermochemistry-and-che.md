# Thermochemistry and CHE

## 1. Static Adsorbate Frequencies and Thermochemical Corrections

### Localized VASP Frequencies (`IBRION = 5`)
- **Displace the adsorbate and optionally selected top-layer metal atoms**. Reuse `CONTCAR`, `KPOINTS`, and `POTCAR` from the converged optimization in a separate `freq/` directory.
  ```ini
  IBRION = 5
  POTIM  = 0.015
  NFREE  = 2
  EDIFF  = 1E-7
  ISTART = 0
  ICHARG = 2
  ```
  In `Selective dynamics`, set `T` only for the Cartesian components selected for displacement and `F` for all others. For adsorbate-only frequencies, set all three components of every substrate atom to `F`.
- **Thermochemistry tools**
  - **Adsorbed species**. Use `VASPKIT` task **`501`** or ASE `HarmonicThermo`. Sum only the $3N_{\text{free}}$ vibrational modes and omit ideal-gas translation and rotation.
  - For gas-phase references, use `VASPKIT 502` or ASE `IdealGasThermo` to include translation, rotation, vibration, spin degeneracy, and the $pV$ term. The ideal-gas pressure correction to entropy is $\Delta S_p=-k_B\ln(p/p^\circ)$, giving a free-energy correction of $+k_BT\ln(p/p^\circ)$.
- **Consistent low-frequency cutoff**. Low real frequencies from frustrated translation or rotation, such as those below $50\,\text{cm}^{-1}$, make harmonic $S_{\text{vib}}$ rise sharply. If you raise modes below $50\,\text{cm}^{-1}$ to $50\,\text{cm}^{-1}$ or omit very small imaginary modes, apply the same rule and cutoff to all adsorbates in the reaction network.

## 2. Reaction Free Energies from the Computational Hydrogen Electrode (CHE)

Write the balanced equation for each step involving $\text{H}^+ + e^-$ transfer.

$$\Delta G(U_{\text{RHE}}) = \Delta E_{\text{DFT}} + \Delta E_{\text{solv}} + \Delta G_{\text{corr}} + \Delta G_U$$

Here, $G_{\text{corr}}=\mathrm{ZPE}+\Delta H_{\text{thermal}}-TS$, where $\Delta H_{\text{thermal}}$ is the thermal enthalpy correction excluding ZPE. When the adsorbate $pV$ term is negligible, use a harmonic vibrational free-energy correction.

Reference the proton–electron pair chemical potential at $U_{\text{RHE}} = 0\,\text{V}$ to gas-phase hydrogen.
$$\mu(\text{H}^+ + e^-) = \frac{1}{2} G(\text{H}_2, g, 298.15\,\text{K}, 1\,\text{bar})$$

### Sign of the Potential Term $\Delta G_U$
- **Proton-coupled reduction** consumes $n$ pairs of $\text{H}^+ + e^-$, as in $\text{CO}_2^* + \text{H}^+ + e^- \to \text{COOH}^*$.
  $$\Delta G_U = + n e U_{\text{RHE}}$$
  A positive applied potential $U > 0$ lowers the electron chemical potential and raises the reduction step's $\Delta G$. A negative potential $U < 0$ favors reduction.
- **Proton-coupled oxidation** releases $n$ pairs of $\text{H}^+ + e^-$, as in $\text{H}_2\text{O} + * \to \text{OH}^* + \text{H}^+ + e^-$.
  $$\Delta G_U = - n e U_{\text{RHE}}$$
  A positive applied potential $U > 0$ favors electron removal and lowers the oxidation step's $\Delta G$.

### RHE, SHE, and pH
$$U_{\text{RHE}} = U_{\text{SHE}} + \frac{k_B T \ln 10}{e}\,\text{pH} \quad (\text{approximately }+0.0592\,\text{V/pH at }298.15\,\text{K})$$
- For equal proton and electron transfer, $U_{\text{RHE}}$ includes the pair's Nernst pH term. On the SHE scale, the pair chemical potential is $\frac12G(\mathrm{H}_2)-eU_{\mathrm{SHE}}-k_BT\ln(10)\,\mathrm{pH}$. Handle the activities of other species and the interfacial response according to the model.

## 3. Gas-Phase Reference States and Comparison Scope

- Use `1 bar` as a possible standard pressure for hydrogen. If approximating the chemical potential of pure liquid water with saturated vapor, use approximately `0.0317 bar` at 298.15 K. List the temperature and partial pressure of each gas-phase reference.
- **Empirical functional corrections**. If a published protocol applies corrections for gas-phase errors such as overbinding of $\text{CO}_2$, $\text{CO}$, or $\text{H}_2$ with PBE or RPBE, record the values and sources in `che_summary.json` and retain the raw DFT energies.
- **Comparison scope**. Label static vacuum CHE, implicit-solvent CHE, and explicit-solvent PMFs with their respective model assumptions. They represent relaxation without solvent, continuum response, and finite-temperature ensemble averaging, respectively, and can all be expressed in `eV`.
