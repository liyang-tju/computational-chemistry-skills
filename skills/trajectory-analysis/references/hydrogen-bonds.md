# Hydrogen Bonds and Coordination

## 1. Hydrogen-Bond Geometry Conventions

These angle definitions use different vertices and can select different hydrogen bonds even with the same distance cutoff. Use the convention in the target literature or software. The thresholds below are examples.

| Criterion | A (vertex at donor D) | B (vertex at hydrogen H, as in MDAnalysis) |
|---|---|---|
| Donor–acceptor distance | $d(\text{D}\cdots\text{A}) \le 3.5\,\text{\AA}$ | $d(\text{D}\cdots\text{A}) \le 3.5\,\text{\AA}$ |
| H–acceptor distance (optional) | Sometimes $d(\text{H}\cdots\text{A}) \le 2.5\,\text{\AA}$ | — |
| **Angle** | **$\angle(\text{H-D}\cdots\text{A}) \le 30^\circ$** (small deviation from collinearity) | **$\angle(\text{D-H}\cdots\text{A}) \ge 150^\circ$** (near $180^\circ$) |

- Report the vertex, atoms defining the two rays, and threshold. Use consistent periodic images for distances and angles in each triangle. The default angle in MDAnalysis `HydrogenBondAnalysis` is `D–H–A > 150°`.
- For organic hydroxyl groups, such as in ethanol or carboxylic acids, and surface hydroxyls, define donor and acceptor candidates. Standard definitions generally exclude C–H donors.

## 2. Dynamic Atom Assignment in Reactive Trajectories

In reactive AIMD or MLP trajectories, bonds can form or break, as in hydrated proton $\text{H}_3\text{O}^+$ migration or $\text{H}_2\text{O}$ dissociation.
- Reassign molecular topology per frame. After proton transfer, a hydrogen can be covalently bound to another water, making the initial topology unsuitable for hydrogen-bond and intramolecular distance calculations.
- Reconstruct identities from instantaneous covalent neighbors before counting hydrogen bonds. For example, assign each H to the nearest O or N within $d < r_{\text{cov,max}} \approx 1.25\text{–}1.35\,\text{\AA}$. Record brief shared-proton events, such as Zundel $\text{H}_5\text{O}_2^+$, separately.

## 3. Contributions and Normalization

- Report solute **donor (HBD)** and **acceptor (HBA)** counts, contributions of individual O or N sites, and counts within each water layer.
- State the normalization, such as per solute, per water, per surface area ($\text{nm}^{-2}$), or total per frame. Document deduplication of bifurcated bonds from one H and repeated atom-pair assignments.
- Mean counts and lengths reflect local density, steric hindrance, and thermal fluctuations. Estimating individual bond energies or reaction barriers requires an energy analysis.
