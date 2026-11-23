# PMF Estimators, Reweighting, and Uncertainty

Upstream tools include MBAR and `statistical_inefficiency`, Grossfield `wham` and `wham-2d`, PLUMED `sum_hills` and `REWEIGHT_BIAS`, and the i-PI slow-growth extension. [pymbar](https://github.com/choderalab/pymbar) · [wham](https://github.com/agrossfield/wham) · [PLUMED](https://github.com/plumed/plumed2) · [i-PI slow growth](https://github.com/zhangchenyu-USTC/i-pi_slow-growth)

## 1. Constrained MD (Blue Moon) and Slow-Growth Thermodynamic Integration

### Free-Energy Gradient with the Metric Correction

Integrate along constrained coordinate $\xi$ in the Blue Moon ensemble.

$$\frac{dA}{d\xi} = \frac{\left\langle Z^{-1/2}\left(g_{\mathrm{c}} + k_B T\, G\right) \right\rangle_\xi}{\left\langle Z^{-1/2} \right\rangle_\xi}$$

Here $g_{\mathrm{c}}$ is the constraint multiplier converted to a free-energy gradient using the engine's sign convention, $Z=\sum_i m_i^{-1}\|\nabla_i\xi\|^2$ is the mass-weighted metric for one constraint, and $G$ is the geometric correction. For a single distance constraint between two free atoms, $Z=1/m_A+1/m_B$ is constant, the weights cancel, and $G=0$. Check the metric and correction for angles, coordination numbers, difference coordinates, or multiple coupled constraints. Document omissions and their justification.

### Parsing VASP `REPORT` and CP2K Output

- **VASP `REPORT`**：
  - Align the `cc>` CVs with `b_m>` by step and channel. For space-delimited standard `b_m>` lines, `parts[1]` is $\lambda$, `parts[2]` is $|Z|^{-1/2}$, `parts[3]` is $Gk_BT$, and `parts[4]` is $|Z|^{-1/2}(\lambda+Gk_BT)$. For a fixed window, use `mean(parts[4]) / mean(parts[2])` over the equilibrated segment and calculate each constraint channel independently.
  - **Restart segments**. Identify duplicates by checkpoint, global step, and channel. Nearby CV values are a cross-check since small pulling increments also produce nearby points. Once duplicates are resolved, estimate $g_i$ at each $\xi_i$ under the quasistatic approximation and integrate by the trapezoidal rule.
    $$\Delta A(\xi_k) = \sum_{i=1}^{k} \frac{1}{2}(\xi_i - \xi_{i-1})(g_i + g_{i-1})$$
  - **Constrained AIMD**. Equilibrate each fixed window $\xi_k$ independently. Estimate its gradient from the weighted ratio above and recompute both numerator and denominator per block. Integrate window gradients and propagate error using squared integration weights for independent window variances.
  - **Slow-growth hysteresis**. Check rate dependence by halving `INCREM` or comparing forward and reverse curves. Substantial disagreement indicates a departure from the quasistatic limit and calls for constrained AIMD windows or more relaxation and sampling.
- **CP2K**. Read instantaneous constraint forces by channel from `.lagrange_mult`. Average by window or integrate by the trapezoidal rule, converting Hartree/Bohr to eV/Å as needed.

## 2. Umbrella Sampling with WHAM and MBAR

### The $\frac{1}{2}\kappa$ Convention and Tool Selection

- VASP `SPRING_K` with `ICONST status=8` and PLUMED `RESTRAINT KAPPA` both use the following convention.
  $$V_i(\xi) = \frac{1}{2}\kappa_i(\xi - \xi_{0,i})^2$$
  Verify that external tools such as Grossfield `wham` or legacy scripts use the same factor of $1/2$ in $V_i = \frac{1}{2}k(\xi-\xi_0)^2$. A convention mismatch changes the effective spring constant by a factor of two.
- **Tools**
  - `agrossfield/wham` (1D `wham` and 2D `wham-2d`) is lightweight and supports periodic boundaries and bootstrap errors. Supply $T$ and $k$ in consistent units.
  - `pymbar` (`MBAR`) gives binless estimates. Construct the reduced bias matrix $u_{kn} = V_k(\xi_n)/(k_B T)$ across all samples and windows to obtain reweighted free energies and covariances. [pymbar](https://github.com/choderalab/pymbar)

### Window Overlap and the Radial Jacobian

1. **Window overlap**. Plot marginal histograms for all windows and require substantial overlap between neighbors. Fill gaps at high barriers with additional windows or adjusted `KAPPA`. Smoothing and spline interpolation can hide gaps.
2. **Jacobian entropy for 3D radial distances**. A radial CV $r$ between two entities, such as dissociation or adsorption averaged over a spherical shell with unconstrained lateral motion, includes a translational entropy contribution from $4\pi r^2 dr$. Decide whether to apply the following correction based on the reference state.
   $$F_{\text{corr}}(r) = F_{\text{raw}}(r) + (d - 1)\, k_B T \ln\!\left(\frac{r}{r_{\text{ref}}}\right) \quad (\text{in 3D, } d=3 \Rightarrow +2 k_B T \ln r)$$
   Use the radial $2k_B T \ln r$ correction only for the spherical volume measure. A one-dimensional surface-normal projection uses a different measure. Record whether the CV is `DISTANCE` or `ZDIST` or another normal projection.

## 3. Metadynamics, WT-Metadynamics, and OPES Reweighting

### Bias Summation and Trajectory Reweighting

- **Standard metadynamics (VASP `HILLSPOT` or fixed hills)**. Accumulate hills chronologically and take the negative bias $-V_{\text{bias}}(s)$ as an approximation. If early `HILLSPOT` entries are boundary Gaussians from the initial `PENALTYPOT`, decide whether to display or exclude the artificial wall region. Continued fixed-height hill deposition after the first crossing can cause overfilling.
- **PLUMED `sum_hills` for WT-Metadynamics**
  $$F(s) = -\frac{\gamma}{\gamma - 1} V_{\text{bias}}(s) \quad (\gamma \to 1 \text{ is singular, and } \gamma \to \infty \text{ gives standard MetaD})$$
  `plumed sum_hills --hills HILLS` outputs the free-energy estimate by default. Apply $\gamma/(\gamma-1)$ only when `--negbias` returns $-V_{\text{bias}}$. Use trajectory reweighting in the target ensemble to remove additional walls or project onto an unbiased CV.
- **Time-dependent WT-Metadynamics reweighting with Tiwary–Parrinello $c(t)$**
  Enable `CALC_RCT` in `METAD` and assign the following weight to each frame.
  $$w(t) \propto \exp\!\left(\frac{V(s(t), t) - c(t)}{k_B T}\right)$$
  Use the weights to reweight the histogram. `COLVAR` gives the needed difference as `metad.bias - metad.rct`.
- **Quasi-stationary `OPES_METAD` and `OPES_METAD_EXPLORE` reweighting**
  1. Once the bias approaches quasi-stationarity, use the instantaneous bias for umbrella-style reweighting.
     $$w(t) \propto \exp\!\left(\frac{V_{\text{bias}}(s(t))}{k_B T}\right) \quad (V_{\text{bias}} = \text{opes.bias})$$
     PLUMED `REWEIGHT_BIAS TEMP=<T>` and `HISTOGRAM` can also be used. For the fully unbiased ensemble include walls and other active biases in the total bias. For an ensemble retaining walls, remove only the biases excluded by the target ensemble.
  2. The bias often fluctuates more during `OPES_METAD_EXPLORE` exploration. Use `opes.rct`, `opes.zed`, recrossings, and PMF drift together to select a quasi-stationary interval. `opes.neff` measures the effective weighted sample size, and `opes.rct` helps diagnose bias convergence.

### Verify $k_B T$ Units and Convergence

- **Units**
  - For PLUMED `UNITS ENERGY=eV`, use $k_B = 8.617333262 \times 10^{-5}\ \text{eV/K}$, giving $k_B T \approx 0.025852\ \text{eV}$ at $300\ \text{K}$.
  - For PLUMED defaults in `kJ/mol`, use $R = 8.314462618 \times 10^{-3}\ \text{kJ/(mol}\cdot\text{K)}$, giving $RT \approx 2.4943\ \text{kJ/mol}$ at $300\ \text{K}$.
  Mixed units can cause $\exp(V/k_B T)$ to overflow or compress the weight distribution.
- **Convergence checks**
  1. **Recrossings**. Require repeated passages between reactant and product states through the transition region to assess convergence of relative free energies.
  2. **Block PMF drift**. After discarding the transient, divide the later half of sampling into 2–4 contiguous blocks and reweight independently. Check that the barrier and reaction $\Delta F$ stabilize within the uncertainty.
  3. **Bias convergence**. Compare hill decay and segment-wise profiles for WT-MetaD or `opes.rct`, `opes.zed`, and bias shape for OPES. Interpret these alongside coverage and block errors.

## 4. Autocorrelation and Block Averaging

Time series such as AIMD constraint forces `b_m` and closely spaced `COLVAR` samples are autocorrelated. The naive standard error $\sigma/\sqrt{N}$ can substantially underestimate uncertainty. Use $N_{\text{eff}} = N / g$ with `pymbar.timeseries.statistical_inefficiency` or the plateau of the block-averaged error.

```python
import numpy as np


def block_error(x: np.ndarray, n_blocks: int = 5) -> float:
    """Split a 1D equilibrated time series into n_blocks blocks and estimate the standard error of its mean."""
    chunks = np.array_split(x, n_blocks)
    means = np.array([c.mean() for c in chunks if len(c) > 0])
    if len(means) < 2:
        return 0.0
    return float(means.std(ddof=1) / np.sqrt(len(means)))
```

For long gradient series such as one constrained AIMD window, scan block sizes $b \in [1, N/10]$ and plot $\text{SEM}(b)$ or fit a saturating model such as $A\arctan(Bb)$. Report an uncertainty after confirming the plateau. Propagate independent window errors with $\sqrt{\sum_k (w_k\,\text{SEM}_k)^2}$, or use a block `WHAM/MBAR` bootstrap for confidence intervals.
