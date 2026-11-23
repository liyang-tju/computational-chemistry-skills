# Reactive and Voronoi CVs

## 1. Atom Tracking in Proton Transfer

In aqueous or catalytic interfacial reactions such as $\text{H}_3\text{O}^+$/$\text{OH}^-$ migration, a specific H atom can transfer from its original oxygen to a neighboring water. Consider a fixed atom-pair CV, $d(\text{O}_1\text{-H}_1)$.
- When $\text{H}_2$ on another water participates, the original $\text{O}_1\text{-H}_1$ pair no longer tracks the process.
- Decide whether to track coordination or proton count at a fixed site (for example, `COORDINATION` over all transferable H atoms around an active site), or a mobile excess-proton center using continuous Voronoi assignments, weighted centers, or differences in hydration coordination.

## 2. Voronoi and Multi-Atom Coordination CVs

Apply the following checks when designing Voronoi assignments or smooth coordination CVs.
1. **Atom groups**. Identify candidate heavy atoms, such as active-site O/N and all solvent oxygen atoms, and a separate transferable hydrogen group. Verify indices against element identities.
2. **Smooth switches**. Biased CVs must be continuous and differentiable. Use PLUMED `RATIONAL`, `EXP`, or smooth $\text{softmax}$ weights $\exp(-\lambda d_{ij}) / \sum_k \exp(-\lambda d_{ik})$ in place of discontinuous `step()`, `if/else`, or `sign()` expressions.
3. **Reference coordination**. Assign reference hydrogen counts such as 0, 1, or 2 according to the site. Surface oxygen, carboxyl oxygen, and bulk water oxygen can differ.

## 3. Finite-Difference Checks of Analytical Derivatives

After changing a `CUSTOM` or `MATHEVAL` expression or an extended action, test the formula on small configurations.

$$F_k^{\text{num}} = -\frac{V_{\text{bias}}(x_k + \delta) - V_{\text{bias}}(x_k - \delta)}{2\delta} \quad (\delta \approx 10^{-5}\text{–}10^{-4}\,\text{\AA})$$

Compare PLUMED bias forces with central finite differences (typical tolerance $< 10^{-4}$). Check the following conditions as well.
- When several ion pairs coexist, verify that changes in the target reaction site dominate the CV and that unrelated bulk ion-pair fluctuations are small.
- For custom actions, confirm available names and parameters with `plumed info` or the source. Report missing extensions explicitly.
