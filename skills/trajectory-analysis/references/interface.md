# Interfacial Distributions

## 1. Surface-Relative Coordinates and Reference Plane

Cell origins and thermally fluctuating slab heights can shift across conditions. Define windows relative to the surface instead of using an absolute cutoff such as `z in [12, 15] Å`.
- A common reference is the mean height $z_{\text{surf}}(t)$ of top-layer metal atoms in each frame, identified by `tag` or `role == "slab_top"`.
  $$z_{\text{rel}, i}(t) = \text{wrap}_{z}\!\bigl(z_i(t) - z_{\text{surf}}(t)\bigr)$$
- Define the positive normal direction toward liquid. Track upper and lower interfaces and the vacuum separately so periodic folding does not mix them.

## 2. Planar Density Profiles and Normalization

Use normal bin width $\Delta z$ and cross-sectional area $A_{xy}(t) = |\mathbf{a}(t) \times \mathbf{b}(t)|_z$.
- **Number and mass density**
  $$\rho(z_k) = \frac{\langle N_k(t) \rangle}{A_{xy} \Delta z} \quad \text{or mass density}\;(\text{g/cm}^3) = \rho_{\text{num}}\,(\text{molecules/\AA}^3) \times \frac{M_{\text{mol}}}{N_A \cdot 10^{-24}}$$
  For an NPT trajectory with $N_{\text{frames}}$ frames, specify whether you divide by instantaneous $A_{xy}(t)\Delta z$ before averaging or divide the summed counts by cumulative bin volume.
- **Axis definitions**. Distinguish particle counts $N(z_k)$, mass density ($\text{g/cm}^3$), and probability density $P(z_k)$ with $\sum P(z_k)\Delta z = 1$. Verify that the integrated number density reproduces the expected molecule count in the selected region.
- **Bulk density**. Measure a flat bulk interval at least 10–15 Å from the surface. Report first- and second-layer adsorption peaks separately.

## 3. Water Orientation

- **Reconstruct dipole vectors with PBC**. Use $\mathbf{v}_1 = \text{MIC}(\mathbf{r}_{\text{H}_1} - \mathbf{r}_{\text{O}})$ and $\mathbf{v}_2 = \text{MIC}(\mathbf{r}_{\text{H}_2} - \mathbf{r}_{\text{O}})$ for the same water molecule. The direction is $\hat{\mu} = (\mathbf{v}_1 + \mathbf{v}_2) / \|\mathbf{v}_1 + \mathbf{v}_2\|$, from O to the H–H midpoint. State any opposite direction used in a comparison.
- **Orientation measures**
  - Signed $\langle \cos\theta \rangle$ distinguishes H pointing toward liquid or the surface. $\langle |\cos\theta| \rangle$ measures alignment regardless of sign.
  - $\arccos\langle \cos\theta \rangle \ne \langle \theta \rangle$；
  - Isotropy in 3D gives uniform $P(\cos\theta)$ and $P(\theta) \propto \sin\theta$ because $\mathrm{d}\Omega = 2\pi \sin\theta\,\mathrm{d}\theta$. Compare distributions under the same measure.
- **Orientation-weighted density**. $\rho(z)\langle \cos\theta(z) \rangle$ gives the net directional distribution. Label it as orientation-weighted density when charge and dipole-magnitude factors are absent.

## 4. RDFs and Coordination Numbers (CN)

```python
# Use ASE MIC distances to histogram intergroup pairs and compute cumulative coordination.
from ase.geometry import get_distances
_, dists = get_distances(pos_ref, pos_target, cell=atoms.cell, pbc=atoms.pbc)
```

- Exclude self-pairs ($i = j$) in same-species RDFs, such as `O_w - O_w`. For solute–water coordination, state whether intramolecular atoms are excluded.
- **Confined interfaces**. The homogeneous 3D normalization $4\pi r^2 \rho_0 \Delta r$ assumes an isotropic bulk environment. Near a metal surface, excluded volume can prevent $g(r)$ from approaching `1.0`. State that limitation, correct for accessible volume or define a local reference, or report integrated mean CN within a specified first-shell cutoff $r_{\text{cut}}$.
