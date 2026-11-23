# Energy Decomposition and References

## 1. Frozen Energy Decompositions

Let $S$ be the surface, $A$ the adsorbate, $W$ the explicit solvent and ions, and $AWS$ the complete interface.

1. **Frozen solvent effect on adsorption energy (four components)**
   $$\Delta \Delta E_{\text{solv}}^{\text{ads}} = \bigl[E(AWS) - E(WS)\bigr] - \bigl[E(AS) - E(S)\bigr] = E(AWS) - E(WS) - E(AS) + E(S)$$
   - This is the net effect of $W$ on adsorption at the frozen geometry, including $A$–$W$ interactions and nonadditive response involving $S$.
   - With $W$ and $S$ frozen after removal of $A$, the result excludes cavity formation free energy and solvent reorganization entropy, both relevant to equilibrium solvation free energy $\Delta G_{\text{solv}}$.
2. **Include the isolated adsorbate $A$ (five components)**
   - With isolated $E(A)$ at the same frozen geometry, report the frozen vacuum adsorption energy $\Delta E_{\text{ads}}^{\text{vac}} = E(AS) - E(S) - E(A)$ and the solvent modulation $\Delta \Delta E_{\text{solv}}^{\text{ads}}$. For the frozen $A$–$W$ interaction without the substrate, use consistently defined $E(AW)-E(A)-E(W)$.
   - If $E(A)$ uses an independently optimized gas-phase geometry and $E(AS)$ a deformed frozen solution geometry, label the resulting difference as including adsorbate strain energy.

## 2. Electron Counts, Charged Fragments, and Constant Potential

- **Charged periodic fragments**. When $A$ or $W$ contains a net ionic charge, such as $\text{H}_3\text{O}^+$, $\text{K}^+$, or $\text{OH}^-$, the fragment can be charged even when the full interface is neutral. Adjust VASP `NELECT` or CP2K `CHARGE`. A uniform neutralizing background introduces finite-size electrostatic artifacts in 3D periodic cells. Document or correct them when comparing systems or cell lengths.
- **Constant-potential energies**. Align fragment energies with the same electron reference using the electron chemical potential, for example the grand potential $\Omega = E - \mu_e \Delta N_e$. Use this convention consistently when subtracting states with different electron counts.

## 3. Statistics and Result Checks

- Verify SCF convergence of every fragment before merging with the per-frame checks in `$mlp-workflow`. Check complete and finite fragment sets.
  ```python
  # Check that each frame has four finite fragment energies.
  req = ["AWS", "WS", "AS", "S"]
  valid = df.pivot(index="sample_id", columns="fragment", values="energy").dropna(subset=req)
  valid["delta_E_solv_ads"] = valid["AWS"] - valid["WS"] - valid["AS"] + valid["S"]
  ```
- Average each independent trajectory first, then estimate the condition mean and between-replica error. Cumulative means can help identify equilibration. Use block or replica analysis for uncertainty.
