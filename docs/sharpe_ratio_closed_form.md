---
myst:
  html_meta:
    description: >-
      The closed-form Sharpe ratio of the European trend-following system under a stationary
      linear process: the Isserlis-type variance of a product with an excess-kurtosis term, the
      autocorrelation loadings A and B and the kurtosis loading K, the long-short extension, and
      the independence of the Sharpe ratio from the volatility target, as implemented in
      trendfollowing.
---

# The closed-form Sharpe ratio

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Implemented in [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

The Sharpe ratio of the European trend-following system has a closed form in the autocorrelation
function, the drift and the excess kurtosis of the volatility-normalised returns. The daily
strategy return is a product of the current normalised return and a filter of past ones, both
linear in common innovations, and the variance of such a product follows from an extension of the
Isserlis theorem. The result reduces the design of a single-filter system to the choice of a span,
evaluated from the autocorrelation structure of the returns, and it ranks filters by risk-adjusted
return where the [expected return](pnl_decomposition.md) alone cannot.

## Overview

The expected return grows with the volatility target and with the filter loading, so it cannot
compare spans: a slow filter has a larger mean gain on a drift and a different risk. The Sharpe
ratio divides by the strategy volatility, which requires fourth moments of the returns and so a
distributional assumption. Under a causal linear process with independent innovations, the
fourth-moment structure is fixed by the moving-average weights and one parameter, the excess
kurtosis $\kappa$ of the innovations.

The chapter derives:

1. the variance of a product of two linear processes, with the kurtosis term;
2. the mean and variance of the daily return through three loadings $A_\nu$, $B_\nu$ and $K_\nu$;
3. the annualised Sharpe ratio, its independence from $\sigma_{\mathrm{target}}$ and $l$, and the
   long-short extension.

The [next chapter](sharpe_under_processes.md) evaluates the result under named processes, and the
[turnover chapter](turnover_and_net_sharpe.md) adds costs.

## Inputs, notation, and assumptions

| Convention | This article |
|---|---|
| Return basis | Volatility-normalised daily returns $z_t$ of a causal linear process |
| Normalisation | $\vartheta=1$ in the Sharpe ratio; general $\vartheta$ in the daily moments |
| Signal filter | Single filter with loading $l$; LS($N_1$,$N_2$) by linearity |
| Moment basis | Population moments under the linear-process assumption, innovations with zero third moment |
| Annualisation | $\mathrm{SR}=\sqrt{\mathrm{af}}\mathbb{E}[f_t]/\sqrt{\operatorname{Var}[f_t]}$, $\mathrm{af}=260$ |
| Timing | $f_t=(\sigma_{\mathrm{target}}/\sqrt{\mathrm{af}})S_{t-1}z_t$ |
| Costs | Gross; the net ratio is in the [turnover chapter](turnover_and_net_sharpe.md) |
| trendfollowing default | `compute_annualised_sharpe(rho, long_span=250, short_span=None, sr_underlying=0.0, variance=1.0, kappa=0.0, ma_weights=None, af=260.0)` |

| Symbol or input | Meaning | Units and convention |
|---|---|---|
| $X$, $Y$ | Variables linear in common innovations | $X=\mu_X+\sum_s a_s\epsilon_{t-s}$, $Y=\mu_Y+\sum_s b_s\epsilon_{t-s}$ |
| $\sigma_X^2$, $\sigma_Y^2$, $\sigma_{XY}$ | Their variances and covariance | |
| $\Lambda_{t-1}$ | Raw filter $\mathcal{L}^{(\nu)}(z_{t-1})$ | Units of $z$ |
| $g_u$ | Loading of $\Lambda_{t-1}$ on the innovation $\epsilon_{t-1-u}$ | $(1-\nu)\sum_{m=0}^{u}\nu^m\psi_{u-m}$ |
| $(s_{\mathrm{mean}},s_{\mathrm{var}},s_{\mathrm{cov}})$ | Moments of the signal relative to $z$ | Fields of `SignalMoments` |

## Methodology

### The variance of a product

**Lemma (Isserlis with kurtosis; Sepp and Lucic, 2026, Section 5.2).** For $X$ and $Y$ linear in
independent innovations with zero third moment and excess kurtosis $\kappa$,

$$
\operatorname{Var}[XY]=\sigma_X^2\sigma_Y^2+\sigma_{XY}^2+\mu_X^2\sigma_Y^2+\mu_Y^2\sigma_X^2+2\mu_X\mu_Y\sigma_{XY}+\kappa\sum_{s=0}^{\infty}a_s^2b_s^2 .
$$

**Proof.** Write $X=\mu_X+x$ and $Y=\mu_Y+y$. The third-order moments $\mathbb{E}[x^2y]$ and
$\mathbb{E}[xy^2]$ are proportional to the third moment of the innovations and vanish. Cumulants
are multilinear over independent innovations, so $\operatorname{cum}(x,x,y,y)=\kappa\sum_s a_s^2b_s^2$, and
$\mathbb{E}[x^2y^2]=\sigma_X^2\sigma_Y^2+2\sigma_{XY}^2+\operatorname{cum}(x,x,y,y)$. Expand
$\mathbb{E}[(XY)^2]$ and subtract $(\sigma_{XY}+\mu_X\mu_Y)^2$. $\square$

For $\kappa=0$ the lemma is the Isserlis (1918) theorem for jointly Gaussian variables.

### Mean and variance of the daily return

Apply the lemma to $X=z_t$ and $Y=\Lambda_{t-1}$, with $f_t=(l\sigma_{\mathrm{target}}/\sqrt{\mathrm{af}})z_t\Lambda_{t-1}$.

**Proposition (daily moments; Sepp and Lucic, 2026, Section 5.2).** Under the linear-process
assumption,

$$
\mathbb{E}[f_t]=\frac{l\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}}\left(\vartheta A_\nu+\mu^2\right),
$$

$$
\operatorname{Var}[f_t]=\left(\frac{l\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}}\right)^2\vartheta\left(\vartheta\left(B_\nu+A_\nu^2+\kappa K_\nu\right)+\mu^2\left(1+B_\nu+2A_\nu\right)\right),
$$

with the autocorrelation loadings and the kurtosis loading

$$
A_\nu=\frac{1-\nu}{\nu}\Psi_\nu,
\qquad
B_\nu=\frac{1-\nu}{1+\nu}\left(1+2\Psi_\nu\right),
\qquad
K_\nu=\sum_{s=1}^{\infty}\psi_s^2g_{s-1}^2 .
$$

**Proof.** The filter has unit mass, so $\mathbb{E}[\Lambda_{t-1}]=\mu$. Summing autocovariances,
$\operatorname{Cov}[z_t,\Lambda_{t-1}]=(1-\nu)\sum_{k\ge 0}\nu^k\vartheta\rho(k+1)=\vartheta A_\nu$.
Splitting the double sum $\operatorname{Var}[\Lambda_{t-1}]=(1-\nu)^2\vartheta\sum_{j,k}\nu^{j+k}\rho(\lvert j-k\rvert)$
into its diagonal and the two off-diagonal parts gives $(1-\nu)^2\vartheta(1+2\Psi_\nu)/(1-\nu^2)=\vartheta B_\nu$.
The innovation $\epsilon_{t-s}$ loads on $z_t$ with $\sqrt\vartheta\psi_s$ and on $\Lambda_{t-1}$
with $\sqrt\vartheta g_{s-1}$ for $s\ge 1$, so the kurtosis term of the lemma is
$\kappa\vartheta^2K_\nu$. Substitute $\sigma_X^2=\vartheta$, $\sigma_Y^2=\vartheta B_\nu$,
$\sigma_{XY}=\vartheta A_\nu$ and $\mu_X=\mu_Y=\mu$. $\square$

Only innovations that enter both the return and the lagged filter contribute to $K_\nu$, so the
kurtosis correction requires serial dependence: under white noise $K_\nu=0$. Positive excess
kurtosis always increases the variance and so shrinks the absolute Sharpe ratio; the expected
return is unaffected.

### The annualised Sharpe ratio

**Corollary (Sharpe ratio; Sepp and Lucic, 2026, Section 5.3).** With $\vartheta=1$ and
$\mu_{\mathrm{an}}=\sqrt{\mathrm{af}}\mu$,

$$
\mathrm{SR}=\frac{\sqrt{\mathrm{af}}A_\nu+\mu_{\mathrm{an}}^2/\sqrt{\mathrm{af}}}{\sqrt{B_\nu+A_\nu^2+\kappa K_\nu+(\mu_{\mathrm{an}}^2/\mathrm{af})(1+B_\nu+2A_\nu)}} .
$$

**Proof.** Divide $\sqrt{\mathrm{af}}\mathbb{E}[f_t]$ by $\sqrt{\operatorname{Var}[f_t]}$; the factor
$l\sigma_{\mathrm{target}}/\sqrt{\mathrm{af}}$ cancels. $\square$

> **Insight.** The Sharpe ratio depends neither on the volatility target nor on the filter
> loading: both scale the mean and the volatility of $f_t$ equally. For a single filter the
> design problem is the choice of one number, the span, and the formula makes the Sharpe ratio an
> explicit function of it, the autocorrelation function, the drift and the excess kurtosis.

### The long-short extension

**Corollary (long-short moments; Sepp and Lucic, 2026, Section 5.2).** For
$S_{t-1}=l_1\mathcal{L}^{(\nu_1)}(z_{t-1})-l_2\mathcal{L}^{(\nu_2)}(z_{t-1})$,

$$
\mathbb{E}[S_{t-1}]=(l_1-l_2)\mu,
\qquad
\operatorname{Cov}[z_t,S_{t-1}]=\vartheta\left(l_1A_{\nu_1}-l_2A_{\nu_2}\right),
$$

$$
\operatorname{Var}[S_{t-1}]=\vartheta\left(l_1^2B_{\nu_1}+l_2^2B_{\nu_2}-2l_1l_2\frac{(1-\nu_1)(1-\nu_2)(1+\Psi_{\nu_1}+\Psi_{\nu_2})}{1-\nu_1\nu_2}\right),
$$

and the kurtosis loading replaces $g_u$ by $l_1g_u^{(\nu_1)}-l_2g_u^{(\nu_2)}$.

**Proof.** The signal is linear in past returns; the cross-covariance of the two filters follows
from the same double-sum split as $B_\nu$. Substitute into the lemma. $\square$

In code, `compute_signal_moments` returns these moments relative to $z$ as
$s_{\mathrm{mean}}=\mathbb{E}[S]/\mu$, $s_{\mathrm{var}}=\operatorname{Var}[S]/\vartheta$ and
$s_{\mathrm{cov}}=\operatorname{Cov}[z_t,S_{t-1}]/\vartheta$, with the loadings included, so that
$s_{\mathrm{mean}}=l$, $s_{\mathrm{var}}=l^2B_\nu$ and $s_{\mathrm{cov}}=lA_\nu$ for a single filter.
`compute_daily_moments` returns the mean and variance of $S_{t-1}z_t$, which is $f_t$ scaled by
$\sqrt{\mathrm{af}}/\sigma_{\mathrm{target}}$.

### The kurtosis loading under AR(1)

The AR(1) weights $\psi_s=\sqrt{1-\phi^2}\phi^s$ give the unit-loading closed form (Sepp and Lucic,
2026, Section 6.2)

$$
K_\nu=\frac{(1-\nu)^2(1-\phi^2)^2}{(\phi-\nu)^2}\left(\frac{\phi^4}{1-\phi^4}-\frac{2\nu\phi^3}{1-\nu\phi^3}+\frac{\nu^2\phi^2}{1-\nu^2\phi^2}\right),
$$

interpreted by continuity at $\phi=\nu$. At $\phi=0.05$ and $\kappa=3$ the correction lowers the
Sharpe ratio by at most 0.2% across the spans from 5 to 250 days, so the AR(1) exhibits are
evaluated at $\kappa=0$. Under the paper's verification configuration, LS(250,20) with $d=0.1$, the
correction is below 0.001 (Sepp and Lucic, 2026, Table 6.1).

## Worked example

The block checks the loadings against `compute_signal_moments`, the Sharpe ratio against the
corollary, the independence from the volatility target, the long-short covariance, the analytic
column of the paper's Table 6.1, and the kurtosis term by Monte Carlo under Student-t
innovations.

```python
import numpy as np
import qis
from scipy.special import gamma
import trendfollowing as tf
from trendfollowing.analytics.autocorrelation import ma_weights
from trendfollowing.analytics.sharpe import compute_kurtosis_loading, kurtosis_loading_ar1

af = 260.0

# AR(1) with phi = 0.05 and a 63-day filter: the loadings A and B in closed form
phi, span = 0.05, 63
nu, l = tf.span_to_nu(span), np.sqrt(span)
rho = tf.population_acf(n_lags=1000, phi=phi)
psi_nu = tf.compute_psi_nu(rho, nu)
A = (1.0 - nu) * psi_nu / nu
B = (1.0 - nu) * (1.0 + 2.0 * psi_nu) / (1.0 + nu)
np.testing.assert_allclose([A, B], [(1 - nu) * phi / (1 - nu * phi),
                                    (1 - nu) * (1 + nu * phi) / ((1 + nu) * (1 - nu * phi))])

# SignalMoments carry the loading: s_mean = l, s_var = l^2 B, s_cov = l A
moments = tf.compute_signal_moments(rho=rho, long_span=span)
np.testing.assert_allclose([moments.s_mean, moments.s_var, moments.s_cov], [l, l ** 2 * B, l * A])

# the Sharpe ratio of the corollary, with and without drift
sharpe = tf.compute_annualised_sharpe(rho=rho, long_span=span)
np.testing.assert_allclose(sharpe, np.sqrt(af) * A / np.sqrt(B + A ** 2))
np.testing.assert_allclose(sharpe, 0.200195, atol=5e-7)
mu_an = 0.5
with_drift = tf.compute_annualised_sharpe(rho=rho, long_span=span, sr_underlying=mu_an)
expected = ((np.sqrt(af) * A + mu_an ** 2 / np.sqrt(af))
            / np.sqrt(B + A ** 2 + mu_an ** 2 / af * (1.0 + B + 2.0 * A)))
np.testing.assert_allclose(with_drift, expected)

# daily moments are those of S_{t-1} z_t: the volatility target scales the return, not the Sharpe
mean_f, var_f = tf.compute_daily_moments(rho=rho, long_span=span)
np.testing.assert_allclose(np.sqrt(af) * mean_f / np.sqrt(var_f), sharpe)
low = tf.expected_annual_return(rho=rho, long_span=span, vol_target=0.15)
high = tf.expected_annual_return(rho=rho, long_span=span, vol_target=0.30)
np.testing.assert_allclose([low, high / low], [af * 0.15 / np.sqrt(af) * mean_f, 2.0])

# LS(250,20) under AR(1): the covariance is second order in phi
nu1, nu2 = tf.span_to_nu(250), tf.span_to_nu(20)
q = tf.compute_ewm_long_short_weights(long_span=250, short_span=20)[0] * (1.0 - nu1)
ls_moments = tf.compute_signal_moments(rho=tf.population_acf(n_lags=2000, phi=phi),
                                       long_span=250, short_span=20)
np.testing.assert_allclose(ls_moments.s_cov,
                           q * phi ** 2 * (nu1 - nu2) / ((1.0 - nu1 * phi) * (1.0 - nu2 * phi)))

# the analytic Gaussian column of Table 6.1 of the paper, LS(250,20)
white_noise = tf.population_acf(n_lags=1)
rho_frac = tf.population_acf(n_lags=2000, d=0.1)
rho_mixed = tf.population_acf(n_lags=2000, phi=-0.05, d=0.1)
drift_frac = 0.5 / np.sqrt(gamma(0.8) / gamma(0.9) ** 2)  # raw drift 0.50, normalised
table = [tf.compute_annualised_sharpe(rho=white_noise, long_span=250, short_span=20, sr_underlying=0.25),
         tf.compute_annualised_sharpe(rho=white_noise, long_span=250, short_span=20, sr_underlying=0.5),
         tf.compute_annualised_sharpe(rho=rho_frac, long_span=250, short_span=20),
         tf.compute_annualised_sharpe(rho=rho_mixed, long_span=250, short_span=20),
         tf.compute_annualised_sharpe(rho=rho_frac, long_span=250, short_span=20,
                                      sr_underlying=drift_frac)]
np.testing.assert_allclose(table, [0.062, 0.227, 0.696, 0.666, 0.809], atol=5e-4)
heavy = tf.compute_annualised_sharpe(rho=rho_frac, long_span=250, short_span=20, kappa=3.0,
                                     ma_weights=ma_weights(d=0.1))
assert 0.0 < table[2] - heavy < 0.001

# kurtosis loading: generic sum against the AR(1) closed form, scaled by l^2
psi_ar = ma_weights(phi=phi, d=0.0, n_lags=3000)
np.testing.assert_allclose(compute_kurtosis_loading(ma_weights=psi_ar, long_span=span),
                           l ** 2 * kurtosis_loading_ar1(phi=phi, long_span=span), rtol=1e-10)

# Monte Carlo of the kurtosis term: MA(1) with equal weights and a 2-day filter, where it is large
psi_ma = np.array([1.0, 1.0]) / np.sqrt(2.0)
rho_ma = np.array([1.0, 0.5])
gaussian = tf.compute_annualised_sharpe(rho=rho_ma, long_span=2)
student = tf.compute_annualised_sharpe(rho=rho_ma, long_span=2, kappa=3.0, ma_weights=psi_ma)
np.testing.assert_allclose([gaussian, student], [6.0945, 5.0990], atol=5e-5)
rng = np.random.default_rng(20261001)
n = 2_000_000
for innovations, analytic in ((rng.standard_normal(n + 1), gaussian),
                              (rng.standard_t(6, n + 1) * np.sqrt(4.0 / 6.0), student)):
    z = (innovations[1:] + innovations[:-1]) / np.sqrt(2.0)  # Student-t(6): excess kurtosis 3
    signal = qis.compute_ewm_long_short(a=z, init_value=0.0, long_span=2, short_span=None)
    f = signal[:-1] * z[1:]
    simulated = np.sqrt(af) * f[100:].mean() / f[100:].std()
    assert abs(simulated - analytic) < 0.04  # about three standard errors
```

At $\phi=0.05$ the single 63-day filter has $\mathrm{SR}=0.2002$; doubling the volatility target
doubles the expected return and leaves the Sharpe ratio unchanged. The paper's analytic Gaussian
column for LS(250,20) is reproduced: 0.062 and 0.227 under white noise with drifts 0.25 and 0.5,
0.696 under ARFIMA with $d=0.1$, 0.666 with an added $\phi=-0.05$, and 0.809 with a drift. Under
an MA(1) with $\rho(1)=0.5$ and a 2-day filter, innovations with excess kurtosis 3 lower the Sharpe
ratio from 6.09 to 5.10, and the simulation reproduces both values.

## Implementation in trendfollowing

| Quantity | Formula | trendfollowing entry point |
|---|---|---|
| Signal moments relative to $z$ | $(l,l^2B_\nu,lA_\nu)$, or the long-short moments | `trendfollowing.compute_signal_moments(rho, long_span=250, short_span=None)` returning `trendfollowing.SignalMoments` |
| Daily mean and variance of $S_{t-1}z_t$ | the proposition at given $\mu$, $\vartheta$ | `trendfollowing.compute_daily_moments(rho, long_span=250, short_span=None, mean=0.0, variance=1.0)` |
| Annualised Sharpe ratio | the corollary, with optional kurtosis term | `trendfollowing.compute_annualised_sharpe(rho, long_span, short_span, sr_underlying, variance, kappa, ma_weights, af)` |
| Kurtosis loading | $K$ with the filter loadings included | `trendfollowing.analytics.sharpe.compute_kurtosis_loading(ma_weights, long_span=250, short_span=None)` |
| AR(1) kurtosis loading | $K_\nu$ per unit loading | `trendfollowing.analytics.sharpe.kurtosis_loading_ar1(phi, long_span=250)` |

The functions live in
[sharpe.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/analytics/sharpe.py).
API reference: {py:class}`trendfollowing.SignalMoments`,
{py:func}`trendfollowing.compute_signal_moments`, {py:func}`trendfollowing.compute_daily_moments`,
{py:func}`trendfollowing.compute_annualised_sharpe`,
{py:func}`trendfollowing.analytics.sharpe.compute_kurtosis_loading` and
{py:func}`trendfollowing.analytics.sharpe.kurtosis_loading_ar1`.

Contract details:

- `compute_annualised_sharpe` takes the drift as `sr_underlying` $=\mu_{\mathrm{an}}$ and converts it
  to the daily mean $\mu_{\mathrm{an}}\sqrt{\vartheta}/\sqrt{\mathrm{af}}$.
- A nonzero `kappa` requires `ma_weights`, a one-dimensional array with at least two weights and
  unit sum of squares within $10^{-3}$; otherwise it raises `ValueError`. Use
  `trendfollowing.analytics.autocorrelation.ma_weights` for the ARFIMA family.
- `compute_daily_moments` raises `ValueError` for a non-positive variance.

> **Pitfall.** The `rho` and `ma_weights` arguments describe the same process twice: `rho` sets
> $A_\nu$ and $B_\nu$, and `ma_weights` sets $K_\nu$. The function does not check that
> $\rho(m)=\sum_s\psi_s\psi_{s+m}$; inconsistent inputs give a Sharpe ratio of no process.

## Interpretation and limitations

- The gross Sharpe ratio is exact under the linear-process assumption. The full pipeline adds
  estimation effects the formula does not model: the lagged volatility estimator dampens the
  autocorrelation of $z_t$, so simulated Sharpe ratios fall 2% to 8% below the closed form at
  the paper's calibrations (Sepp and Lucic, 2026, Section 6.4).
- The ratio annualises daily moments. A persistent signal makes daily strategy returns positively
  autocorrelated, and the ratio then overstates the horizon-based Sharpe ratio of Lo (2002).
- Zero third moment of the innovations is assumed; skewed innovations add terms of the order of
  the drift times the skewness.
- The formula is per instrument. A portfolio Sharpe ratio requires the cross-correlation of the
  instruments' strategy returns.

## See also

- [The P&L decomposition: autocorrelation and drift channels](pnl_decomposition.md)
- [Sharpe ratios under white noise, AR(1) and ARFIMA](sharpe_under_processes.md)
- [Turnover, trading costs and the net Sharpe ratio](turnover_and_net_sharpe.md)
- [Return-generating processes](return_processes.md)
- [Realised Sharpe ratios and their comparison](sharpe_inference.md)
- [Bibliography](bibliography.md)

## References

1. Sepp, A., and Lucic, V. (2026). The Science and Practice of Trend-Following Systems. Working paper. [arXiv:2607.19497](https://arxiv.org/abs/2607.19497); [SSRN 3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787). Section 5 derives the closed-form Sharpe ratio; Table 6.1 verifies it.
2. Isserlis, L. (1918). On a Formula for the Product-Moment Coefficient of Any Order of a Normal Frequency Distribution in Any Number of Variables. *Biometrika*, 12(1–2), 134–139. [DOI: 10.1093/biomet/12.1-2.134](https://doi.org/10.1093/biomet/12.1-2.134). The fourth moments of Gaussian variables.
3. Hamilton, J. D. (1994). *Time Series Analysis*. Princeton University Press. The Wold representation.
4. Lo, A. W. (2002). The Statistics of Sharpe Ratios. *Financial Analysts Journal*, 58(4), 36–52. [DOI: 10.2469/faj.v58.n4.2453](https://doi.org/10.2469/faj.v58.n4.2453). Daily-moment and horizon-based Sharpe ratios under serial correlation.
5. Martin, R. J. (2023). Design and Analysis of Momentum Trading Strategies. Working paper. [arXiv:2101.01006](https://arxiv.org/abs/2101.01006). Moments of linear momentum strategies.
6. Sepp, A., and Lucic, V. trendfollowing: Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python. [Software citation metadata](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).
