---
myst:
  html_meta:
    description: >-
      The skewness of aggregated trend-following returns under white noise: the pairing identity
      for third moments, the closed-form skewness of the T-day return of the single-filter European
      system, its master curve and peak horizon near half the span, the long-short extension, and
      the empirical profile on 84 futures, as implemented in trendfollowing.
---

# Skewness of aggregated returns

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Implemented in [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

The returns of a trend-following system are positively skewed over horizons longer than a day,
even when the market has no drift and no autocorrelation and the system has no expected return.
The daily return multiplies the lagged signal by the current return, so the return aggregated
over $T$ days loads on the realised autocovariance of the returns: a convex payoff on the realised
trend. Under white noise the skewness of the $T$-day return has a closed form, which is zero at
one day, positive at every longer horizon, and largest near half the filter span. This chapter
derives it and states its master curve, its long-short extension and its empirical counterpart.

## Overview

Daily trend-following returns look nearly symmetric, while monthly and quarterly returns are
right skewed. The closed form explains the horizon profile and shows that the right tail is
structural: it requires no forecasting skill, because it holds exactly where the expected return
is zero. The chapter answers three questions:

1. What is the third moment of the aggregated return of a linear trend signal under white noise?
2. How does the skewness depend on the horizon and on the span, and where does it peak?
3. How robust is the profile to heavy tails, autocorrelation and the long-short filter?

## Inputs, notation, and assumptions

| Convention | This article |
|---|---|
| Return basis | Volatility-normalised daily returns $z_t$, independent standard normal in the closed form |
| Normalisation | Unit variance; the loading and the volatility target cancel in the skewness |
| Signal filter | A unit-variance linear signal $S_{t-1}=\sum_{j\ge 1}\beta_jz_{t-j}$; the single filter in closed form |
| Moment basis | Population third moment under white noise; standardised sample skewness in the data |
| Annualisation | None: skewness is dimensionless; horizons $T$ in trading days |
| Timing | $f_t=S_{t-1}z_t$ and $F_T=\sum_{t=1}^{T}f_t$ |
| Costs | Gross; costs shift the mean and leave the skewness almost unchanged |
| trendfollowing default | `skewness_white_noise(horizon, span)` |

| Symbol or input | Meaning | Units and convention |
|---|---|---|
| $\beta_j$ | Signal weight on $z_{t-j}$, $j\ge 1$ | $\sum_j\beta_j^2=1$; $\sqrt{1-\nu^2}\nu^{j-1}$ for the single filter |
| $\rho_S(h)$ | Autocorrelation of the signal, $\sum_j\beta_j\beta_{j+h}$ | $\nu^h$ for the single filter |
| $x$, $u(x)$ | Scaled horizon $(1-\nu^2)T$ and the master curve | Dimensionless |
| $x^{\ast}$, $T^{\ast}$ | Peak of the master curve and the horizon of maximal skewness | $T^{\ast}=x^{\ast}/(1-\nu^2)$ days |
| $\gamma_3$ | Third moment of non-Gaussian innovations | Dimensionless |

## Methodology

### The pairing identity

**Lemma (Sepp and Lucic, 2026, Appendix D).** For independent standard normal $z_t$ and
$h\ge 1$, $\mathbb{E}[f_t^2f_{t-h}]=2\beta_h\rho_S(h)$. All other third-order moments vanish:
$\mathbb{E}[f_t^3]=0$, $\mathbb{E}[f_t^2f_{t+h}]=0$ and $\mathbb{E}[f_tf_sf_u]=0$ for distinct $t$, $s$, $u$.

**Proof.** $z_t$ is independent of all signals and returns up to $t$. In
$\mathbb{E}[f_t^3]=\mathbb{E}[S_{t-1}^3]\mathbb{E}[z_t^3]$ both factors vanish. In
$\mathbb{E}[f_t^2f_{t+h}]$ and $\mathbb{E}[f_tf_sf_u]$ the return with the largest time index enters
once and has mean zero. For the surviving moment, independence of $z_t$ gives
$\mathbb{E}[f_t^2f_{t-h}]=\mathbb{E}[S_{t-1}^2S_{t-h-1}z_{t-h}]$. Write $S_{t-1}=\beta_hz_{t-h}+R_h$
with $R_h$ independent of $z_{t-h}$. Terms with an odd power of $z_{t-h}$ vanish, and the cross term
gives $2\beta_h\mathbb{E}[z_{t-h}^2]\mathbb{E}[R_hS_{t-h-1}]=2\beta_h\rho_S(h)$, since
$S_{t-h-1}$ contains no $z_{t-h}$. $\square$

### The skewness of the aggregated return

**Proposition (Sepp and Lucic, 2026, Appendix D).** With $F_T=\sum_{t=1}^{T}f_t$,
$\operatorname{Var}[F_T]=T$ and

$$
\mathbb{E}[F_T^3]=6\sum_{h=1}^{T-1}(T-h)\beta_h\rho_S(h).
$$

For the single filter the skewness $\varsigma(T)=\mathbb{E}[F_T^3]/T^{3/2}$ is

$$
\varsigma(T)=\frac{6\nu\left(T(1-\nu^2)-1+\nu^{2T}\right)}{(1-\nu^2)^{3/2}T^{3/2}},
$$

with $\varsigma(1)=0$ and $\varsigma(T)\gt 0$ for every $T\ge 2$.

**Proof.** Covariances $\mathbb{E}[f_tf_s]$ vanish for $t\ne s$ by the largest-index argument, and
$\operatorname{Var}[f_t]=1$, so $\operatorname{Var}[F_T]=T$. In the expansion of $F_T^3$ the lemma
leaves only the paired terms with the later index squared:
$\mathbb{E}[F_T^3]=3\sum_{t\gt s}\mathbb{E}[f_t^2f_s]=6\sum_{h=1}^{T-1}(T-h)\beta_h\rho_S(h)$. For the
single filter $\beta_h\rho_S(h)=\sqrt{1-\nu^2}\nu^{2h-1}$, and
$\sum_{h=1}^{T-1}(T-h)y^h=y(T(1-y)-1+y^T)/(1-y)^2$ with $y=\nu^2$ gives the closed form. The
function $g(y)=T(1-y)-1+y^T$ has $g(1)=0$ and $g'(y)=-T(1-y^{T-1})\lt 0$ on $(0,1)$, so
$g(\nu^2)\gt 0$ for $T\ge 2$, while $g$ vanishes identically at $T=1$. $\square$

The skewness depends neither on the filter loading nor on the volatility target, which scale
$f_t$ linearly. Strategy returns are serially uncorrelated under white noise, so the variance of
the $T$-day return is exactly $T$ times the daily variance while its third moment accumulates.

> **Insight.** The positive skewness requires no autocorrelation, no drift and no alpha: it
> holds exactly under white noise, where the expected return is zero. A trend-following system
> sells many small losses in trendless markets and buys a convex payoff on realised trends.

### The master curve and the peak horizon

For long spans, $\nu^{2T}\approx e^{-x}$ with $x=(1-\nu^2)T$, and the skewness collapses onto one
curve for all spans,

$$
\varsigma(T)\approx 6\nu u(x),
\qquad
u(x)=\frac{x-1+e^{-x}}{x^{3/2}} .
$$

**Proposition (peak).** $u$ attains its maximum at the root $x^{\ast}\approx 2.1491$ of
$2x(1-e^{-x})=3(x-1+e^{-x})$, where $6u(x^{\ast})\approx 2.410$. The skewness therefore peaks at the
horizon $T^{\ast}=x^{\ast}/(1-\nu^2)\approx 0.54(N+1)$ days, near half the filter span, at a value
just below $2.41\nu$.

**Proof.** $u'(x)=0$ is equivalent to $x(1-e^{-x})=\frac{3}{2}(x-1+e^{-x})$; with
$1-\nu^2=4N/(N+1)^2$, $T^{\ast}=x^{\ast}(N+1)^2/(4N)\approx x^{\ast}(N+1)/4$. $\square$

### Robustness and extensions

- **Non-Gaussian innovations.** For independent innovations with zero mean, unit variance and zero
  third moment, every surviving pairing uses only second moments, so the closed form holds without
  Gaussianity and without a finite-kurtosis condition. A third moment $\gamma_3$ adds
  $T\gamma_3^2\sum_{j\ge 1}\beta_j^3$ to $\mathbb{E}[F_T^3]$, a term that decays in the skewness as
  $T^{-1/2}$ (Sepp and Lucic, 2026, Section 7.4).
- **Long-short filter.** The lemma holds with the long-short weights $\beta_j=q(\nu_1^{j-1}-\nu_2^{j-1})$
  and their autocorrelation, so the general third moment applies. The long-short filter shifts the
  profile towards longer horizons: at the quarterly horizon of 63 days, LS(250,20) has a
  white-noise skewness of 1.69, against 2.17 for a single 250-day filter.
- **Autocorrelation.** Under a general autocorrelation function additional pairings of the order of
  the autocorrelations enter, so the white-noise profile is the leading order for weakly
  autocorrelated returns. In simulation, positive autocorrelation and long memory raise the profile
  at horizons short relative to the span, mean reversion lowers it, and all processes converge to
  the closed form at long horizons.

![Panel A: closed-form skewness against the horizon for spans 5, 20, 63 and 250 with Monte Carlo markers; panel B: Monte Carlo skewness at span 100 under white noise, AR(1) and ARFIMA against the closed form; panel C: the cross-sectional median and interquartile range of the empirical skewness of 84 futures at span 100, tracking the closed form and positive at every horizon](../papers/tf_systems/paper/figures/aggregated_skewness.PNG)

Figure 7.5 of Sepp and Lucic (2026). Panel (A) confirms the closed form at every span and horizon.
Panel (B) shows that the process changes the profile at short horizons only. Panel (C) applies the
gross single-filter European system with a span of 100 days to the 84 futures contracts of the
packaged dataset: the cross-sectional median of the standardised sample skewness of overlapping
$T$-day sums attains 2.33 at 55 days against the closed-form 2.35, and the interquartile range is
positive at every horizon. The figure is produced by
`papers/tf_systems/replication/aggregated_skewness_fig.py`.

## Worked example

The block checks the closed form against the general third-moment formula, the master curve and
the peak horizon, the long-short extension, and the closed form by Monte Carlo under Gaussian and
Student-t innovations.

```python
import numpy as np
from scipy.optimize import brentq
from scipy.signal import lfilter
from scipy.stats import skew
import trendfollowing as tf

# zero at one day, positive from two days on
assert tf.skewness_white_noise(horizon=1, span=63) == 0.0
np.testing.assert_allclose(tf.skewness_white_noise(horizon=2, span=63), 0.5097, atol=5e-5)

# the closed form equals the general third moment with single-filter weights and autocorrelation
span, horizon = 63, 30
nu = tf.span_to_nu(span)
j = np.arange(1, 501)
weights = np.sqrt(1.0 - nu ** 2) * nu ** (j - 1)
signal_acf = nu ** j
third_moment = tf.aggregated_third_moment_white_noise(signal_weights=weights, signal_acf=signal_acf,
                                                      horizon=horizon)
np.testing.assert_allclose(third_moment / horizon ** 1.5,
                           tf.skewness_white_noise(horizon=horizon, span=span), rtol=1e-12)

# the master curve peaks at x* = 2.1491 with ceiling 6 u(x*) = 2.410
x_star = brentq(lambda x: 2.0 * x * (1.0 - np.exp(-x)) - 3.0 * (x - 1.0 + np.exp(-x)), 1.0, 4.0)
np.testing.assert_allclose([x_star, 6.0 * tf.skewness_master_curve(x_star)], [2.1491, 2.4104],
                           atol=5e-5)

# the peak horizon is near half the span: 54.8 days at span 100, with skewness 2.35 at 55 days
np.testing.assert_allclose(tf.skewness_peak_horizon(span=100), 54.81, atol=5e-3)
profile = tf.skewness_white_noise(horizon=np.arange(1, 400), span=100)
assert np.argmax(profile) + 1 == 56
np.testing.assert_allclose(tf.skewness_white_noise(horizon=55, span=100), 2.3536, atol=5e-5)

# LS(250,20) at the quarterly horizon: 1.69, against 2.17 for a single 250-day filter
nu1, nu2 = tf.span_to_nu(250), tf.span_to_nu(20)
q = tf.compute_ewm_long_short_weights(long_span=250, short_span=20)[0] * (1.0 - nu1)
ls_weights = q * (nu1 ** (np.arange(1, 6001) - 1) - nu2 ** (np.arange(1, 6001) - 1))
np.testing.assert_allclose(np.sum(ls_weights ** 2), 1.0)
ls_acf = np.array([np.sum(ls_weights[:-h] * ls_weights[h:]) for h in range(1, 400)])
ls_skew = tf.aggregated_third_moment_white_noise(signal_weights=ls_weights[:399], signal_acf=ls_acf,
                                                 horizon=63) / 63 ** 1.5
np.testing.assert_allclose([ls_skew, tf.skewness_white_noise(horizon=63, span=250)], [1.689, 2.172],
                           atol=5e-4)

# Monte Carlo at span 5 and horizon 5: Gaussian and unit-variance Student-t(10) innovations
rng = np.random.default_rng(20261001)
span, horizon, burn_in, n_paths = 5, 5, 60, 400_000
nu = tf.span_to_nu(span)
closed_form = tf.skewness_white_noise(horizon=horizon, span=span)
np.testing.assert_allclose(closed_form, 1.5510, atol=5e-5)
for innovations in (rng.standard_normal((n_paths, burn_in + horizon)),
                    rng.standard_t(10, (n_paths, burn_in + horizon)) * np.sqrt(0.8)):
    signal = np.sqrt(span) * lfilter([1.0 - nu], [1.0, -nu], innovations, axis=1)
    f = signal[:, burn_in - 1:burn_in + horizon - 1] * innovations[:, burn_in:]
    aggregated = f.sum(axis=1)
    np.testing.assert_allclose(aggregated.var(), horizon, rtol=0.01)
    assert abs(skew(aggregated) - closed_form) < 0.06
```

At a 100-day span the skewness peaks at 2.35 near 55 days, the closed-form value the empirical
median of the 84 contracts reaches. The long-short filter LS(250,20) is less skewed at a quarter
(1.69) than a single 250-day filter (2.17), because its profile peaks later. Heavy-tailed
innovations with zero third moment leave the profile unchanged.

## Implementation in trendfollowing

| Quantity | Formula | trendfollowing entry point |
|---|---|---|
| Third moment of $F_T$ for any unit-variance linear signal | $6\sum_{h=1}^{T-1}(T-h)\beta_h\rho_S(h)$ | `trendfollowing.aggregated_third_moment_white_noise(signal_weights, signal_acf, horizon)` |
| Skewness of the single filter | closed form, scalar or array horizon | `trendfollowing.skewness_white_noise(horizon, span)` |
| Master curve | $u(x)=(x-1+e^{-x})/x^{3/2}$ | `trendfollowing.skewness_master_curve(x)` |
| Peak horizon | $x^{\ast}/(1-\nu^2)$ | `trendfollowing.skewness_peak_horizon(span)` |

The functions live in
[skewness.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/analytics/skewness.py).
API reference: {py:func}`trendfollowing.aggregated_third_moment_white_noise`,
{py:func}`trendfollowing.skewness_white_noise`, {py:func}`trendfollowing.skewness_master_curve` and
{py:func}`trendfollowing.skewness_peak_horizon`.

Contract details:

- `aggregated_third_moment_white_noise` takes `signal_weights` $=(\beta_1,\beta_2,\dots)$ and
  `signal_acf` $=(\rho_S(1),\rho_S(2),\dots)$ of equal length and uses the first $T-1$ entries;
  it returns zero for $T=1$ and raises `ValueError` for $T\lt 1$ or unequal lengths. The weights
  must have unit sum of squares for the result to be a standardised third moment.
- `skewness_white_noise` accepts an integer or an array of horizons and returns a float or an
  array.
- `skewness_master_curve` raises `ValueError` for non-positive $x$.

> **Pitfall.** The ceiling of the master curve is $6u(x^{\ast})\approx 2.410$. The module docstring
> of `skewness.py` quotes 2.4143; the functions themselves compute the correct value.

## Interpretation and limitations

- The closed form is exact under white noise. It is the leading order for weakly autocorrelated
  returns; closed forms under AR(1) and ARFIMA exist but are left to a follow-up paper.
- Portfolio aggregation preserves the skewness through the common trend component, while
  portfolio-level volatility targeting reduces it. The paper's three systems, which do not target
  portfolio volatility, have a positive quarterly skewness of 0.5 after 2000 against 1.8 over the
  full history of the same portfolio (Sepp and Lucic, 2026, Section 7.4).
- Sample skewness is a noisy estimator, dominated by a few large observations; quarterly skewness
  over two decades rests on about 80 observations.
- Skewness is not a risk measure by itself: positive skewness coexists with long drawdowns in
  trendless regimes.

## See also

- [EWMA filters and variance-preserving signals](ewma_filters.md)
- [The P&L decomposition: autocorrelation and drift channels](pnl_decomposition.md)
- [The futures evidence of Sepp and Lucic (2026)](case_study_futures_evidence.md)
- [Bibliography](bibliography.md)

## References

1. Sepp, A., and Lucic, V. (2026). The Science and Practice of Trend-Following Systems. Working paper. [arXiv:2607.19497](https://arxiv.org/abs/2607.19497); [SSRN 3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787). Section 7.4 and Appendix D derive the skewness and test it on futures.
2. Martin, R. J. (2023). Design and Analysis of Momentum Trading Strategies. Working paper. [arXiv:2101.01006](https://arxiv.org/abs/2101.01006). The term structure of the skewness of momentum returns.
3. Potters, M., and Bouchaud, J.-P. (2006). Trend Followers Lose More Often Than They Gain. *Wilmott Magazine*, 26, 58–63. Positive skewness of an exponential-average trend system on a random walk.
4. Dao, T.-L., Nguyen, T.-T., Deremble, C., Lempérière, Y., Bouchaud, J.-P., and Potters, M. (2017). Tail Protection for Long Investors: Convexity at Work. *Journal of Investment Strategies*, 7(1), 61–84. The convexity of trend-following portfolios.
5. Sepp, A., and Lucic, V. trendfollowing: Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python. [Software citation metadata](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).
