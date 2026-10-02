---
myst:
  html_meta:
    description: >-
      Volatility estimation and volatility-normalised returns in trendfollowing: the lagged EWMA
      variance of daily returns, the volatility-target weight, the identity that turns the system
      return into a signal times a normalised return, what normalisation does to heavy tails and
      autocorrelation, and the link to Kelly sizing.
---

# Volatility normalisation and position sizing

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Implemented in [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

A volatility-normalised return is a daily return divided by an estimate of its volatility made
one day earlier. Trend-following systems use it twice: as the input of the trend filter, so that
signals are comparable across contracts and volatility regimes, and as the unit of position
sizing, so that each contract contributes a similar risk. This chapter defines the estimator,
proves the identity that writes the daily return of the European system as a signal times a
normalised return, and states what normalisation does to heavy tails and to autocorrelation.

## Overview

Futures volatilities range from about 2% a year for short rates to above 30% for most
commodities, and each contract's volatility moves through regimes. A filter applied to raw
returns would be dominated by the most volatile contracts and the most volatile periods.
Dividing by a lagged volatility estimate removes both effects. Every closed form of the handbook
is then a statement about the normalised returns $z_t$, which is the process the systems trade.

The chapter covers:

1. the EWMA variance estimator and the lag that makes $z_t$ point in time;
2. the volatility-target weight and the identity $f_t=(\sigma_{\mathrm{target}}/\sqrt{\mathrm{af}})S_{t-1}z_t$;
3. what normalisation does to heavy tails, volatility clustering and autocorrelation;
4. the reading of the weight as a fractional Kelly rule.

## Inputs, notation, and assumptions

| Convention | This article |
|---|---|
| Return basis | Simple daily returns $r_t$ of a continuous futures contract, excess returns |
| Normalisation | $z_t=r_t/\sigma_{t-1}$; $\sigma_t^2$ an EWMA of $r_t^2$ without mean adjustment, span 33 days |
| Signal filter | Any signal $S_t$ built from $z$ up to day $t$ |
| Moment basis | Population moments for the dampening identity; sample moments in the examples |
| Annualisation | $\sqrt{\mathrm{af}}\sigma_t$ annualises the daily volatility, $\mathrm{af}=260$ |
| Timing | $\sigma_t$ uses returns up to $t$; $z_t$ divides by $\sigma_{t-1}$; the weight $w_t$ uses $\sigma_t$ and earns $r_{t+1}$ |
| Costs | Not applicable |
| trendfollowing default | `compute_vol_norm_returns(returns, vol_span=31.0)`; the system runners pass `vol_span=33` |

| Symbol or input | Meaning | Units and convention |
|---|---|---|
| $\nu_\sigma$ | Smoothing parameter of the variance estimator | $1-2/(N_\sigma+1)$ with volatility span $N_\sigma$ |
| $w_t^{\mathrm{vt}}$ | Volatility-target weight | Exposure per unit of capital |
| $x_t$ | Standardised return in the dampening identity | Unit variance, independent of the volatility |
| $\rho_r(m)$, $\rho_x(m)$ | Autocorrelations of $r_t$ and of $x_t$ | Dimensionless |
| $d_t$ | Price change $s_t-s_{t-1}$ | Price units |

## Methodology

### The EWMA variance estimator

**Definition.** The daily variance estimate is the EWMA of squared returns, without mean
adjustment,

$$
\sigma_t^2=\mathcal{L}^{(\nu_\sigma)}(r_t^2)=(1-\nu_\sigma)r_t^2+\nu_\sigma\sigma_{t-1}^2 .
$$

Omitting the mean is deliberate: the daily mean of a futures return is two orders of magnitude
smaller than its standard deviation, and subtracting an estimated mean adds noise. The
alternative estimator on price changes, $\sqrt{\mathcal{L}^{(\nu_\sigma)}(d_t^2)}$, is in price units;
the American system uses a price-unit range of that kind (see the
[American system chapter](american_system.md)).

**Definition.** The volatility-normalised return divides by the estimate of the previous day:

$$
z_t=\frac{r_t}{\sigma_{t-1}} .
$$

The return of day $t$ enters $\sigma_t$ but not $\sigma_{t-1}$, so it never scales itself. Under
a correctly specified conditional variance, $z_t$ has unit variance; empirically, for S&P 500
futures the EWMA volatility averages 17% and $z_t$ has a standard deviation of 0.96 (Sepp and
Lucic, 2026, Section 2.2).

### The volatility-target weight and the system return

**Definition.** The European system sizes the position on day $t$ as the signal times the
volatility-target weight,

$$
w_t=S_t w_t^{\mathrm{vt}},
\qquad
w_t^{\mathrm{vt}}=\frac{\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}\sigma_t},
$$

where $\sigma_{\mathrm{target}}$ is the annualised volatility target.

**Identity (system return).** The daily return of the position is a signal times a normalised
return:

$$
f_t=w_{t-1}r_t=\frac{\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}}S_{t-1}z_t .
$$

**Proof.** Substitute $w_{t-1}=S_{t-1}\sigma_{\mathrm{target}}/(\sqrt{\mathrm{af}}\sigma_{t-1})$ and
$r_t/\sigma_{t-1}=z_t$. $\square$

The identity is the foundation of the closed forms: once the weight is written this way, every
moment of the strategy return is a moment of a product of two linear functions of the normalised
returns, and the raw volatility drops out. With a signal of unit variance and serially
independent $z_t$ of unit variance, the daily strategy variance is $\sigma_{\mathrm{target}}^2/\mathrm{af}$
and the strategy runs at its target volatility. With an estimated volatility the variance of $z_t$
deviates from one, so the invariance is approximate.

> **Insight.** The goal of volatility targeting here is not risk management. It produces the
> normalised returns from which the signal is built and on which the performance of each
> instrument is measured; portfolio-level risk control is a separate, optional layer of the
> runners.

### What normalisation does to the return distribution

Volatility clustering makes raw returns heavy tailed even when their standardised innovations
are Gaussian. Normalisation by a well-calibrated lagged estimator approximately recovers the
innovations: in a GARCH(1,1) simulation, the excess kurtosis falls from about 10 for the raw
returns to below 0.1 for $z_t$, and the autocorrelation of squared returns, the signature of
clustering, falls by an order of magnitude. This is why the linear-process assumption of the
[Sharpe ratio chapter](sharpe_ratio_closed_form.md) is mild in practice.

**Proposition (dampening of autocorrelation).** Let $r_t=\sigma_{t-1}x_t$, where $x_t$ is a
stationary standardised process with autocorrelation $\rho_x(m)$, independent of a stationary
predictable volatility $\sigma_{t-1}$. Then

$$
\rho_r(m)=\rho_x(m)\frac{\mathbb{E}[\sigma_t\sigma_{t-m}]}{\mathbb{E}[\sigma_t^2]} .
$$

**Proof.** Independence gives $\operatorname{Cov}[r_t,r_{t-m}]=\mathbb{E}[\sigma_{t-1}\sigma_{t-1-m}]\rho_x(m)$
when $x_t$ has mean zero and unit variance, and $\operatorname{Var}[r_t]=\mathbb{E}[\sigma_t^2]$
by stationarity. $\square$

By the Cauchy–Schwarz inequality the ratio is at most one, so time-varying volatility dampens
the autocorrelation of raw returns, and dividing by the true $\sigma_{t-1}$ recovers $\rho_x(m)$.
An estimated volatility recovers it only in part: under an AR(1) calibration with $\phi=0.05$,
the lagged EWMA estimator lowers the first-lag autocorrelation of $z_t$ from 0.050 to about
0.046 (Sepp and Lucic, 2026, Section 6.4), which attenuates the realised Sharpe ratio of the
system by 2% to 8% relative to the population closed form.

### Volatility targeting as fractional Kelly sizing

For excess returns with drift $\tilde\mu$ and volatility $\sigma$, the growth-optimal (Kelly)
weight of Merton (1969) is $w^{\ast}=\tilde\mu/\sigma^2=(\tilde\mu/\sigma)(1/\sigma)$: a Sharpe
ratio times an inverse volatility. The European weight has this form with rolling estimates:
the raw filter of normalised returns $\mathcal{L}^{(\nu)}(z_t)$ estimates the daily Sharpe ratio,
and the variance-preserving loading $l=\sqrt{N}$ makes the weight a span-dependent multiple of the
Kelly fraction (Sepp and Lucic, 2026, Section 4.1). Unlike the Kelly rule, the filter is applied to
serially dependent returns, and its expected return under white noise with drift is proportional
to the squared Sharpe ratio, in line with the growth rate of one-half the squared Sharpe ratio of
the continuous-time Merton solution.

## Worked example

The block checks the estimator against a direct recursion, the volatility-target weight and the
system-return identity, then measures the effect of normalisation on a GARCH(1,1) path and the
dampening of autocorrelation under stochastic volatility.

```python
import numpy as np
from scipy.signal import lfilter
import trendfollowing as tf
from trendfollowing.systems.backtest_utils import (compute_vol, compute_vol_norm_returns,
                                                   compute_vol_target_weight)

rng = np.random.default_rng(20261001)

# GARCH(1,1) daily returns: omega, alpha, beta as in the paper's verification script
n = 300_000
omega, alpha, beta = 1e-6, 0.09, 0.90
innovations = rng.standard_normal(n)
returns = np.empty(n)
garch_variance = omega / (1.0 - alpha - beta)
for t in range(n):
    returns[t] = np.sqrt(garch_variance) * innovations[t]
    garch_variance = omega + alpha * returns[t] ** 2 + beta * garch_variance

# the estimator: EWMA of squared returns seeded with the sample variance, lagged by one day
z = compute_vol_norm_returns(returns=returns, vol_span=33)
nu_sigma = tf.span_to_nu(33)
variance = np.empty(n)
seed = np.var(returns)  # full-sample seed: an in-sample initialisation
# Older qis versions emit the seed at row zero; current versions update it with r_0^2.
# Check both supported initialisation contracts, then verify every subsequent update.
first_variance = compute_vol(returns=returns, vol_span=33, is_lag1=False)[0] ** 2
if np.isclose(first_variance, seed, rtol=1e-12, atol=0.0):
    variance[0] = seed
else:
    variance[0] = nu_sigma * seed + (1.0 - nu_sigma) * returns[0] ** 2
for t in range(1, n):
    variance[t] = nu_sigma * variance[t - 1] + (1.0 - nu_sigma) * returns[t] ** 2
sigma_lagged = np.sqrt(np.concatenate(([variance[0]], variance[:-1])))
np.testing.assert_allclose(z, returns / sigma_lagged, rtol=1e-12)
np.testing.assert_allclose(compute_vol(returns=returns, vol_span=33, is_lag1=False),
                           np.sqrt(variance), rtol=1e-12)

# the volatility-target weight uses the unlagged estimate, annualised with af = 260
weight_vt, annual_vol = compute_vol_target_weight(returns=returns, vol_span=33, vol_target=0.15,
                                                  annualization_factor=260.0)
np.testing.assert_allclose(annual_vol, np.sqrt(260.0 * variance), rtol=1e-12)
np.testing.assert_allclose(weight_vt, 0.15 / annual_vol, rtol=1e-12)

# identity: w_{t-1} r_t = (sigma_target / sqrt(af)) S_{t-1} z_t for any signal S
signal = rng.standard_normal(n)
strategy = (signal * weight_vt)[:-1] * returns[1:]
np.testing.assert_allclose(strategy, 0.15 / np.sqrt(260.0) * signal[:-1] * z[1:], rtol=1e-10)


def excess_kurtosis(x):
    x = (x - x.mean()) / x.std()
    return np.mean(x ** 4) - 3.0


def lag_one_autocorrelation(x):
    x = x - x.mean()
    return np.sum(x[1:] * x[:-1]) / np.sum(x * x)


# normalisation removes most of the tails and of the volatility clustering
z_used = z[500:]
np.testing.assert_allclose([excess_kurtosis(returns), excess_kurtosis(z_used)], [10.38, 0.072],
                           atol=0.01)
np.testing.assert_allclose(z_used.var(), 1.059, atol=0.001)
clustering_raw = lag_one_autocorrelation(returns ** 2)
clustering_normalised = lag_one_autocorrelation(z_used ** 2)
np.testing.assert_allclose([clustering_raw, clustering_normalised], [0.361, 0.032], atol=0.001)

# dampening: r_t = sigma_{t-1} x_t with lognormal volatility and AR(1) x_t, phi = 0.1
phi, log_vol_std, m = 0.1, 0.5, 400_000
x = lfilter([1.0], [1.0, -phi], rng.standard_normal(m)) * np.sqrt(1.0 - phi ** 2)
volatility = 0.01 * np.exp(log_vol_std * rng.standard_normal(m))
raw = volatility[:-1] * x[1:]
dampening = np.exp(-log_vol_std ** 2)  # E[sigma]^2 / E[sigma^2] for iid lognormal volatility
assert abs(lag_one_autocorrelation(raw) - phi * dampening) < 0.005
np.testing.assert_allclose(lag_one_autocorrelation(raw / volatility[:-1]), phi, atol=0.005)
```

The raw GARCH returns have an excess kurtosis of 10.4; the normalised returns have 0.07, a
variance of 1.06 and almost no clustering left. Under lognormal volatility with a log standard
deviation of 0.5, the first-lag autocorrelation of raw returns is $0.1\times e^{-0.25}=0.078$
rather than 0.1, and division by the true volatility restores it.

## Implementation in trendfollowing

| Quantity | Formula | trendfollowing entry point |
|---|---|---|
| Daily volatility | $\sigma_t$, or $\sigma_{t-1}$ with `is_lag1=True` | `trendfollowing.systems.backtest_utils.compute_vol(returns, vol_span=31.0, is_lag1=True)` |
| Normalised returns | $z_t=r_t/\sigma_{t-1}$ | `trendfollowing.systems.backtest_utils.compute_vol_norm_returns(returns, vol_span=31.0)` |
| Volatility-target weight | $\sigma_{\mathrm{target}}/(\sqrt{\mathrm{af}}\sigma_t)$ and $\sqrt{\mathrm{af}}\sigma_t$ | `trendfollowing.systems.backtest_utils.compute_vol_target_weight(returns, vol_span=33, vol_target=0.15, annualization_factor=260)` |
| Annualised volatility of a NAV | $\sqrt{\mathrm{af}}$ times the sample standard deviation | `trendfollowing.compute_daily_annualised_vol(navs)` |

The functions live in
[backtest_utils.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/systems/backtest_utils.py)
and are compiled with Numba; they take NumPy arrays of shape $(T,)$ or $(T,n)$ and return arrays
of the same shape. The EWMA recursion is `qis.ewm_recursion`.
API reference: {py:func}`trendfollowing.systems.backtest_utils.compute_vol`,
{py:func}`trendfollowing.systems.backtest_utils.compute_vol_norm_returns` and
{py:func}`trendfollowing.systems.backtest_utils.compute_vol_target_weight`.

Contract details:

- The recursion is seeded with the full-sample variance of each column (`np.nanvar`). Current
  `qis.ewm_recursion` treats this seed as the state before the first observation and updates it
  with the first squared return. Older qis versions instead emit the seed at row zero; the
  independent recursion above checks both contracts so the reviewed lock and the live
  dependency-compatibility run are covered. The seed uses future observations, so the first weeks of $\sigma_t$ are
  not point in time; the runners' 250-day warmup lets the seed decay to $\nu_\sigma^{250}$,
  about $3\times 10^{-7}$ at the 33-day span.
- With `is_lag1=True`, the first row repeats the first computed volatility, so $z_0=r_0/\sigma_0$.
- `compute_vol_norm_returns` has the default `vol_span=31.0`, while every runner and the paper
  use 33 days. Pass the span explicitly.

> **Pitfall.** A volatility estimate that includes the current return, $r_t/\sigma_t$, shrinks the
> large returns that the estimate itself reacts to. It understates tails, biases the
> autocorrelation of the normalised series towards zero and makes the signal non-causal.

## Interpretation and limitations

- Normalisation by an estimated volatility does not by itself enforce stationarity or unit
  variance; the closed forms apply to the normalised process the pipeline actually produces, and
  the [verification tests of the paper](sharpe_under_processes.md) measure the gap.
- The span of the volatility estimator trades responsiveness against noise. A short span tracks
  regimes but adds noise to the weights and to turnover; the 33-day span follows industry
  practice rather than an optimisation.
- Weights become large when realised volatility is unusually low; practitioners cap or floor
  them, which the European runner does with `weight_cap`.
- The dampening identity requires the volatility to be independent of the standardised returns.
  Leverage effects, in which volatility rises after losses, break that independence.

## See also

- [Notation and conventions](notation_and_conventions.md)
- [EWMA filters and variance-preserving signals](ewma_filters.md)
- [Return-generating processes](return_processes.md)
- [The European system](european_system.md)
- [Bibliography](bibliography.md)

## References

1. Sepp, A., and Lucic, V. (2026). The Science and Practice of Trend-Following Systems. Working paper. [arXiv:2607.19497](https://arxiv.org/abs/2607.19497); [SSRN 3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787). Sections 2.2, 3 and 4.1 define the normalisation, the volatility-target weight and its Kelly reading.
2. Merton, R. C. (1969). Lifetime Portfolio Selection under Uncertainty: The Continuous-Time Case. *The Review of Economics and Statistics*, 51(3), 247–257. [DOI: 10.2307/1926560](https://doi.org/10.2307/1926560). The growth-optimal weight.
3. Dao, T.-L., Nguyen, T.-T., Deremble, C., Lempérière, Y., Bouchaud, J.-P., and Potters, M. (2017). Tail Protection for Long Investors: Convexity at Work. *Journal of Investment Strategies*, 7(1), 61–84. The volatility-normalised European trend system.
4. Moreira, A., and Muir, T. (2017). Volatility-Managed Portfolios. *The Journal of Finance*, 72(4), 1611–1644. [DOI: 10.1111/jofi.12513](https://doi.org/10.1111/jofi.12513). Risk scaling of returns by lagged volatility.
5. Sepp, A., and Lucic, V. trendfollowing: Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python. [Software citation metadata](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).
6. Sepp, A. qis: Performance analytics, portfolio backtesting, risk analysis, and factsheet reporting in Python. [Software citation metadata](https://github.com/ArturSepp/QuantInvestStrats/blob/main/CITATION.cff).
