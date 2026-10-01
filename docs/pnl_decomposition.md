---
myst:
  html_meta:
    description: >-
      The P&L decomposition of the European trend-following system: the exact sample-path
      identity that splits the cumulative return into a realised-autocorrelation channel, a
      squared-drift channel and a boundary term, the expected annual return under any stationary
      autocorrelation function, and its Poisson-kernel spectral reading, as implemented in
      trendfollowing.
---

# The P&L decomposition: autocorrelation and drift channels

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Implemented in [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

The profit of a trend-following system has exactly two sources: the autocorrelation of the
returns it trades at the lags its filter reads, and their squared drift. For the European system
this is an identity on every sample path, not an approximation: the cumulative return over any
period equals a weighted sum of realised autocovariances, plus a squared-mean term, plus a
boundary term that vanishes relative to the others as the period grows. Taking expectations
gives the expected annual return under any stationary autocorrelation function. This chapter
states and proves both results and the spectral reading that follows from them.

## Overview

The chapter answers three questions about the European system with signal
$S_{t-1}=l\mathcal{L}^{(\nu)}(z_{t-1})$:

1. **What did a realised history pay, and why?** The sample-path identity attributes the
   cumulative return of one history to its realised autocorrelation and its realised drift.
2. **What does the system earn on average?** The expected annual return is a linear function of
   the autocorrelation generating function plus a term in the squared drift.
3. **Which frequencies does a span read?** The expected return is a Poisson-kernel average of
   the spectrum of the normalised returns: alpha is excess spectral mass at low frequencies.

The expected return needs only the first two moments of the normalised returns. The variance of
the strategy, and so the Sharpe ratio, needs fourth moments; it is the subject of the
[next chapter](sharpe_ratio_closed_form.md).

## Inputs, notation, and assumptions

| Convention | This article |
|---|---|
| Return basis | Volatility-normalised daily returns $z_t$; simple returns of continuous futures |
| Normalisation | $z_t=r_t/\sigma_{t-1}$; the population results set $\vartheta=1$ |
| Signal filter | Single filter with loading $l$, or LS($N_1$,$N_2$) with loadings $l_1$, $l_2$ |
| Moment basis | Sample moments for the sample-path identity; population moments for the expected return |
| Annualisation | Annual return over $T=\mathrm{af}=260$ days; drift $\mu_{\mathrm{an}}=\sqrt{\mathrm{af}}\mu$ |
| Timing | $f_t=w_{t-1}r_t$; the filter at $t-1$ uses $z$ up to $t-1$ |
| Costs | Gross |
| trendfollowing default | `expected_annual_return(rho, long_span=250, short_span=None, sr_underlying=0.0, vol_target=0.15, af=260.0)` |

| Symbol or input | Meaning | Units and convention |
|---|---|---|
| $\xi_t$ | Scaled daily return $\nu z_t\mathcal{L}^{(\nu)}(z_{t-1})$ | Units of $z^2$ |
| $E(T)$ | Sum of $\xi_t$ over $t=1,\dots,T$ | Units of $z^2$ |
| $\bar z_T$ | Sample mean of $z_1,\dots,z_T$ | Per day |
| $\hat\gamma_T(m)$ | Identity-specific lag product $\frac{1}{T}\sum_{t=1}^{T}(z_t-\bar z_T)(z_{t-m}-\bar z_T)$ | Uses pre-sample observations |
| $\Delta_m$, $R_T$ | Shifted-window discrepancy and boundary term | Units of $z$ and $z^2$ |
| $\bar F_T$, $\bar F_{1y}$ | Expected cumulative and expected annual return | Decimal return at $\sigma_{\mathrm{target}}$ |
| $h_{1y}$ | Autocorrelation-channel multiplier $l\sigma_{\mathrm{target}}\sqrt{\mathrm{af}}(1-\nu)/\nu$ | Decimal per year |
| $F(\lambda)$, $P_\nu(\lambda)$ | Normalised spectral measure of $z_t$; Poisson kernel | $\lambda\in[-\pi,\pi]$ |

The cumulative return $F_T=\sum_t f_t$ is the arithmetic P&L, not the compounded wealth return.

## Methodology

### The daily return as a product

By the [system-return identity](volatility_normalisation.md), with a signal
$S_{t-1}=l\mathcal{L}^{(\nu)}(z_{t-1})$ the daily return is

$$
f_t=\frac{\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}}S_{t-1}z_t=\frac{l\sigma_{\mathrm{target}}}{\nu\sqrt{\mathrm{af}}}\xi_t,
\qquad
\xi_t=\nu z_t\mathcal{L}^{(\nu)}(z_{t-1}),
$$

so $F_T=\frac{l\sigma_{\mathrm{target}}}{\nu\sqrt{\mathrm{af}}}E(T)$ with $E(T)=\sum_{t=1}^{T}\xi_t$.
The loading is $l=1$ for the raw filter, $l=\sqrt{N}$ for the variance-preserving filter, and the
long-short filter follows by linearity.

### The sample-path identity

**Proposition (cumulative return; Sepp and Lucic, 2026, Section 4.2).** If the EWMA series
converges absolutely, which finite second moments ensure, then

$$
\begin{aligned}
E(T)={}&(1-\nu)\sum_{m=0}^{\infty}\nu^m\sum_{t=1}^{T}(z_t-\bar z_T)(z_{t-m}-\bar z_T)\\
&{}-(1-\nu)\sum_{t=1}^{T}(z_t-\bar z_T)^2+\nu T\bar z_T^2+R_T,
\end{aligned}
$$

with the boundary term

$$
R_T=\bar z_T(1-\nu)\sum_{m=1}^{\infty}\nu^m\Delta_m,
\qquad
\Delta_m=\sum_{t=1}^{T}z_{t-m}-T\bar z_T .
$$

**Proof.** Expanding the filter, $\xi_t=(1-\nu)\sum_{m\ge 0}\nu^m z_tz_{t-m}-(1-\nu)z_t^2$, where
the $m=0$ term is added and subtracted. Absolute convergence allows the sums over $t$ and $m$ to be
exchanged. Writing $z=(z-\bar z_T)+\bar z_T$ in each product gives
$\sum_t z_tz_{t-m}=\sum_t(z_t-\bar z_T)(z_{t-m}-\bar z_T)+\bar z_T\Delta_m+T\bar z_T^2$, because
$\sum_t(z_t-\bar z_T)=0$ while the lagged window leaves $\Delta_m$, with $\Delta_0=0$. The geometric
weights of the first sum add to one, so its squared means contribute $T\bar z_T^2$, the
subtracted variance term contributes $-(1-\nu)T\bar z_T^2$, and the net coefficient is $\nu$.
Collecting the $\Delta_m$ terms gives $R_T$. $\square$

The four terms are the realised autocovariance weighted by $\nu^m$, the realised variance, the
squared realised mean and the boundary. With the identity-specific lag product
$\hat\gamma_T(m)$ and $\hat\rho_T(m)=\hat\gamma_T(m)/\hat\gamma_T(0)$, the identity reads

$$
\hat F_T=\frac{l\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}}\frac{1-\nu}{\nu}T\hat\gamma_T(0)\left(\left[\sum_{m=0}^{\infty}\nu^m\hat\rho_T(m)-1\right]+\frac{\nu}{1-\nu}\frac{\bar z_T^2}{\hat\gamma_T(0)}\right)+\frac{l\sigma_{\mathrm{target}}}{\nu\sqrt{\mathrm{af}}}R_T .
$$

Three conventions make it exact. The filter uses observations before the sample start, so the
data extend backwards by the memory of the filter. $\hat\gamma_T(m)$ sums over $t=1,\dots,T$
with those pre-sample observations, so $\hat\rho_T(m)$ is a lag product specific to the identity
and need not lie in $[-1,1]$. And the boundary term collects the cross products of the sample mean
with the shifted windows; it vanishes when $\bar z_T=0$ and is of order $N/T$ relative to $E(T)$.

> **Insight.** At zero realised drift, a trend-following system makes money over a period if and
> only if the $\nu$-weighted sum of the realised autocorrelations at positive lags is positive.
> The realised variance enters only as a scale, and for normalised returns it is close to one.

### The expected return

**Proposition (expected cumulative return; Sepp and Lucic, 2026, Section 4.5).** Under the
population moments $\mu$, $\vartheta$, $\rho(m)$,

$$
\bar F_T=\mathbb{E}[F_T]=\frac{l\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}}\frac{1-\nu}{\nu}\vartheta T\Psi_\nu+\frac{l\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}}T\mu^2,
\qquad
\Psi_\nu=\sum_{m=1}^{\infty}\nu^m\rho(m).
$$

**Proof.** $\mathbb{E}[z_t\mathcal{L}^{(\nu)}(z_{t-1})]=\operatorname{Cov}[z_t,\mathcal{L}^{(\nu)}(z_{t-1})]+\mu^2$
because the filter has unit mass, and
$\operatorname{Cov}[z_t,\mathcal{L}^{(\nu)}(z_{t-1})]=(1-\nu)\sum_{k\ge 0}\nu^k\vartheta\rho(k+1)=\vartheta(1-\nu)\Psi_\nu/\nu$.
Multiply by $T$ and the prefactor of $f_t$. $\square$

The result needs no distributional assumption beyond a stationary mean, variance and
autocorrelation function. With $T=\mathrm{af}$ and $\vartheta=1$ it gives the expected annual return

$$
\bar F_{1y}=h_{1y}\Psi_\nu+\frac{l\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}}\mu_{\mathrm{an}}^2,
\qquad
h_{1y}=l\sigma_{\mathrm{target}}\sqrt{\mathrm{af}}\frac{1-\nu}{\nu}.
$$

The first term is the **autocorrelation channel** and the second the **drift channel**. For the
long-short filter, linearity gives

$$
\bar F_{1y}=\sigma_{\mathrm{target}}\sqrt{\mathrm{af}}\left(l_1\frac{1-\nu_1}{\nu_1}\Psi_{\nu_1}-l_2\frac{1-\nu_2}{\nu_2}\Psi_{\nu_2}\right)+\frac{\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}}\mu_{\mathrm{an}}^2(l_1-l_2).
$$

**Corollary (named processes).** The autocorrelation channel is zero under white noise,
$h_{1y}\nu\phi/(1-\nu\phi)$ under AR(1), $l\sigma_{\mathrm{target}}\sqrt{\mathrm{af}}(1-\nu)\theta/(1+\theta^2)$ under MA(1), and
$h_{1y}(F(d,1,1-d;\nu)-1)$ under ARFIMA(0,d,0).

**Proof.** Substitute $\rho(m)=\delta_{m0}$, $\phi^m$, the MA(1) autocorrelation and the
hypergeometric generating function of the [processes chapter](return_processes.md) into
$\Psi_\nu$. $\square$

Two conclusions follow (Sepp and Lucic, 2026, Section 6). Under white noise the system profits
only from drift, of either sign, and the drift channel grows with $l=\sqrt{N}$. Under AR(1) the
system profits at zero drift if $\phi\gt 0$ and loses if $\phi\lt 0$, and the autocorrelation
channel is largest at short spans. Under long memory it is positive at every span.

> **Insight.** The long-short filter LS(250,20) nearly cancels a short-memory AR(1) alpha: its
> two legs carry the same loading on the first lag, so its autocorrelation channel is of second
> order in $\phi$. A short-memory alpha needs a fast single filter; a long-memory alpha survives
> in slow long-short filters.

### The spectral reading

**Proposition (Poisson-kernel representation; Sepp and Lucic, 2026, Section 5.1).** Let $F$ be the
normalised spectral measure of $z_t$, so that $\rho(m)=\int_{-\pi}^{\pi}e^{im\lambda}dF(\lambda)$.
Then

$$
2\Phi_\nu-1=\int_{-\pi}^{\pi}P_\nu(\lambda)dF(\lambda),
\qquad
P_\nu(\lambda)=\frac{1-\nu^2}{1-2\nu\cos\lambda+\nu^2}.
$$

**Proof.** The autocorrelation is even, so
$2\Phi_\nu-1=\sum_{m\in\mathbb{Z}}\nu^{\lvert m\rvert}\rho(m)=\int\sum_{m\in\mathbb{Z}}\nu^{\lvert m\rvert}e^{im\lambda}dF(\lambda)$,
where the exchange is justified by absolute convergence. The bracket is the Poisson kernel. The
representation of $\rho$ needs only positive definiteness (the Herglotz theorem). $\square$

White noise has the uniform spectrum and $\int P_\nu dF=1$. The system therefore profits at zero
drift if and only if the kernel-weighted spectral mass exceeds one: **trend-following alpha is
excess spectral mass at low frequencies**. The span sets the bandwidth of the kernel; short spans
read the whole spectrum, long spans the mass near frequency zero, where long memory resides.

## Worked example

The block verifies the sample-path identity on one simulated history to machine precision, then
the expected-return formulas against each other, the Poisson-kernel representation by quadrature,
and the expected return by Monte Carlo.

```python
import numpy as np
import qis
from scipy.integrate import quad
from scipy.signal import lfilter
import trendfollowing as tf
from trendfollowing.analytics.expected_return import (expected_pnl_ar1, expected_pnl_arfima,
                                                      expected_pnl_ma1, expected_pnl_white_noise)

rng = np.random.default_rng(20261001)

# one history of an AR(1) with drift: 3000 pre-sample days for the filter memory, T = 2000
nu, phi, pre, T = tf.span_to_nu(63), 0.05, 3000, 2000
z_all = 0.03 + lfilter([1.0], [1.0, -phi], rng.standard_normal(pre + T)) * np.sqrt(1.0 - phi ** 2)
sample = np.arange(pre, pre + T)
z = z_all[sample]
z_bar = z.mean()

# E(T) computed directly from the filter of the previous day, truncated at the pre-sample start
memory = np.arange(pre)
filter_weights = (1.0 - nu) * nu ** memory
lagged_filter = np.array([np.dot(filter_weights, z_all[t - 1 - memory]) for t in sample])
E_direct = np.sum(nu * z * lagged_filter)

# E(T) from the identity: autocovariance, variance, squared mean and boundary terms
lag_products = np.array([np.sum((z - z_bar) * (z_all[sample - m] - z_bar)) for m in range(pre + 1)])
windows = np.array([np.sum(z_all[sample - m]) - T * z_bar for m in range(pre + 1)])
weights = nu ** np.arange(pre + 1)
autocovariance_term = (1.0 - nu) * np.sum(weights * lag_products)
variance_term = -(1.0 - nu) * np.sum((z - z_bar) ** 2)
mean_term = nu * T * z_bar ** 2
boundary = z_bar * (1.0 - nu) * np.sum(weights[1:] * windows[1:])
E_identity = autocovariance_term + variance_term + mean_term + boundary
np.testing.assert_allclose(E_identity, E_direct, rtol=1e-10)
np.testing.assert_allclose([autocovariance_term, variance_term, mean_term, boundary],
                           [57.866, -62.779, 3.461, 0.406], atol=5e-4)
assert abs(boundary) < 0.01 * abs(autocovariance_term)

# expected annual return at sigma_target = 15%: generic formula against the AR(1) corollary
rho_ar = tf.population_acf(n_lags=1000, phi=phi)
generic = tf.expected_annual_return(rho=rho_ar, long_span=63, vol_target=0.15)
l = np.sqrt(63.0)
h_1y = l * 0.15 * np.sqrt(260.0) * (1.0 - nu) / nu
np.testing.assert_allclose(generic, h_1y * nu * phi / (1.0 - nu * phi), rtol=1e-12)
np.testing.assert_allclose([generic, expected_pnl_ar1(phi=phi, long_span=63)], [0.031523, 0.031523],
                           atol=5e-7)

# drift channel (l sigma_target / sqrt(af)) * mu_an^2, the same for drifts of either sign
drift = tf.expected_annual_return(rho=rho_ar, long_span=63, vol_target=0.15, sr_underlying=0.5)
np.testing.assert_allclose(drift - generic, l * 0.15 / np.sqrt(260.0) * 0.25)
np.testing.assert_allclose(expected_pnl_white_noise(long_span=63, mean=0.5), drift - generic)
negative = tf.expected_annual_return(rho=rho_ar, long_span=63, vol_target=0.15, sr_underlying=-0.5)
np.testing.assert_allclose(negative, drift)

# MA(1) with theta = 0.3: rho(1) = theta / (1 + theta^2)
rho_ma = np.array([1.0, 0.3 / 1.09])
np.testing.assert_allclose(tf.expected_annual_return(rho=rho_ma, long_span=21),
                           expected_pnl_ma1(phi=0.3, long_span=21), rtol=1e-12)

# LS(250,20) cancels the first-order AR(1) channel that the single 250-day filter keeps
single = tf.expected_annual_return(rho=rho_ar, long_span=250)
long_short = tf.expected_annual_return(rho=rho_ar, long_span=250, short_span=20)
np.testing.assert_allclose([single, long_short], [0.016031, 0.000083], atol=5e-7)

# expected_pnl_arfima evaluates autocovariances truncated at 150 lags (see the pitfall below)
rho_frac = tf.population_acf(n_lags=2000, d=0.02)
truncated = expected_pnl_arfima(delta=0.02, long_span=500)
np.testing.assert_allclose(truncated / tf.expected_annual_return(rho=rho_frac, long_span=500),
                           0.9067, atol=5e-5)

# Poisson-kernel reading of the AR(1) spectrum: 2 Phi - 1 by quadrature
def ar1_spectral_density(lam):
    return (1.0 - phi ** 2) / (2.0 * np.pi * (1.0 - 2.0 * phi * np.cos(lam) + phi ** 2))


def poisson_kernel(lam):
    return (1.0 - nu ** 2) / (1.0 - 2.0 * nu * np.cos(lam) + nu ** 2)


reading, _ = quad(lambda lam: poisson_kernel(lam) * ar1_spectral_density(lam), -np.pi, np.pi,
                  limit=200)
np.testing.assert_allclose(reading, 2.0 * (1.0 + tf.compute_psi_nu(rho_ar, nu)) - 1.0, rtol=1e-8)

# Monte Carlo: annual mean of f_t = (sigma_target / sqrt(af)) S_{t-1} z_t on a long AR(1) path
z_path = lfilter([1.0], [1.0, -phi], rng.standard_normal(1_300_000)) * np.sqrt(1.0 - phi ** 2)
signal = qis.compute_ewm_long_short(a=z_path, init_value=0.0, long_span=63, short_span=None)
f = 0.15 / np.sqrt(260.0) * signal[:-1] * z_path[1:]
annual = 260.0 * f[1000:].mean()
standard_error = 260.0 * f[1000:].std() / np.sqrt(f[1000:].size)
assert abs(annual - generic) < 3.0 * standard_error
```

On this 2000-day history the autocovariance term (57.9) and the variance term (−62.8) nearly
cancel, the squared drift adds 3.5 and the boundary term 0.4, so $E(T)=-1.05$: a single history
of eight years is dominated by sampling noise in the realised autocorrelation, although its
population counterpart is positive. The boundary term is below 1% of the autocovariance term.
Under AR(1) with $\phi=0.05$, the single 63-day filter at a 15%
volatility target expects 3.15% a year from autocorrelation; a drift of $\mu_{\mathrm{an}}=\pm 0.5$
adds 1.85% for either sign. The single 250-day filter expects 1.60%, while LS(250,20) expects
0.008%: the long-short filter removes the first-order AR(1) channel.

## Implementation in trendfollowing

| Quantity | Formula | trendfollowing entry point |
|---|---|---|
| Centred generating function | $\Psi_\nu=\sum_{m\ge 1}\nu^m\rho(m)$, truncated at the array length | `trendfollowing.compute_psi_nu(rho, nu)` |
| Expected annual return, any autocorrelation | $\bar F_{1y}$, single or long-short, with drift | `trendfollowing.expected_annual_return(rho, long_span=250, short_span=None, sr_underlying=0.0, vol_target=0.15, af=260.0)` |
| White noise | drift channel only | `trendfollowing.expected_pnl_white_noise(long_span, short_span=None, mean=0.0, vol_target=0.15, annualization_factor=260.0)` |
| AR(1) | $h_{1y}\nu\phi/(1-\nu\phi)$ plus drift | `trendfollowing.expected_pnl_ar1(phi, long_span, short_span=None, vol_target=0.15, mean=0.0, annualization_factor=260.0)` |
| MA(1) | $l\sigma_{\mathrm{target}}\sqrt{\mathrm{af}}(1-\nu)\theta/(1+\theta^2)$ plus drift | `trendfollowing.expected_pnl_ma1(phi, long_span, ...)` |
| ARFIMA(1,d,0), paper convention | autocovariance sum truncated at 150 lags | `trendfollowing.expected_pnl_arfima(delta, long_span, short_span=None, phi=0.0, ...)` |

The functions live in
[expected_return.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/analytics/expected_return.py)
and [sharpe.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/analytics/sharpe.py).
The arguments `sr_underlying` and `mean` are the annualised drift $\mu_{\mathrm{an}}$; `rho` is an
autocorrelation array with `rho[0] == 1`, population or empirical.
API reference: {py:func}`trendfollowing.compute_psi_nu`,
{py:func}`trendfollowing.expected_annual_return`, {py:func}`trendfollowing.expected_pnl_white_noise`,
{py:func}`trendfollowing.expected_pnl_ar1`, {py:func}`trendfollowing.expected_pnl_ma1` and
{py:func}`trendfollowing.expected_pnl_arfima`.

Contract details:

- `compute_psi_nu` raises `ValueError` unless $0\lt\nu\lt 1$ and `rho[0]` equals one.
- `expected_annual_return` computes the drift channel from $\mu_{\mathrm{an}}^2$, so a negative
  drift adds the same expected return as a positive one.
- `expected_pnl_ar1`, `expected_pnl_ma1` and `expected_pnl_arfima` add the drift channel only when
  `mean > 0`; a negative `mean` is ignored. `expected_pnl_white_noise` uses `mean**2` for either
  sign.
- `expected_pnl_arfima` sums $\nu^m\gamma(m)$ over the autocovariances of `power_autocorr`,
  truncated at 150 lags. It is the function behind the analytic expected-return lines of the
  paper's process figures and is kept for their reproduction.

> **Pitfall.** For a long-memory process, `expected_pnl_arfima` differs from
> `expected_annual_return(rho=population_acf(n_lags=2000, phi=phi, d=d), ...)` in two ways: it
> uses autocovariances, which scale the channel by $\gamma(0)$ ($1.9\%$ at $d=0.1$), and its
> 150-lag truncation drops the slowly decaying tail. At $d=0.02$ and a two-year span it reports
> 9% less than the 2000-lag value. Use the generic function with a long autocorrelation array.

## Interpretation and limitations

- The sample-path identity is exact on every history but descriptive: it attributes a realised
  return to realised moments of the same history. It does not say whether those moments persist.
- The expected return holds for any stationary autocorrelation function, including empirical
  ones. It does not depend on the distribution of the returns, and so is unaffected by fat tails;
  the Sharpe ratio is.
- The squared sample drift is an upwardly biased estimate of the squared population drift: with
  independent unit-variance returns, the bias in $\mu_{\mathrm{an}}^2$ is $\mathrm{af}/T$, which is
  0.17 at six years of daily data (Sepp and Lucic, 2026, Section 7.3). A forward-looking use should
  shrink or debias it.
- The results describe one instrument at a time. Portfolio returns add cross-instrument
  covariances of the signals, which the closed forms do not model.

## See also

- [EWMA filters and variance-preserving signals](ewma_filters.md)
- [Return-generating processes](return_processes.md)
- [The closed-form Sharpe ratio](sharpe_ratio_closed_form.md)
- [Predict Sharpe from autocorrelation and drift](predict_sharpe_from_acf.md)
- [Bibliography](bibliography.md)

## References

1. Sepp, A., and Lucic, V. (2026). The Science and Practice of Trend-Following Systems. Working paper. [arXiv:2607.19497](https://arxiv.org/abs/2607.19497); [SSRN 3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787). Sections 4.2, 4.5 and 5.1 give the sample-path identity, the expected return and the spectral representation.
2. Lo, A. W., and MacKinlay, A. C. (1990). When Are Contrarian Profits Due to Stock Market Overreaction? *The Review of Financial Studies*, 3(2), 175–205. [DOI: 10.1093/rfs/3.2.175](https://doi.org/10.1093/rfs/3.2.175). Trading profits as weighted autocovariances plus a squared-mean term.
3. Bruder, B., and Gaussel, N. (2011). Risk-Return Analysis of Dynamic Investment Strategies. Working paper, SSRN. The difference-of-variances decomposition of trend-following returns.
4. Dao, T.-L., Nguyen, T.-T., Deremble, C., Lempérière, Y., Bouchaud, J.-P., and Potters, M. (2017). Tail Protection for Long Investors: Convexity at Work. *Journal of Investment Strategies*, 7(1), 61–84. Trend-following performance as long-term minus short-term variance.
5. Sepp, A., and Lucic, V. trendfollowing: Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python. [Software citation metadata](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).
