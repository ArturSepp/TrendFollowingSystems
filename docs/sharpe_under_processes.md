---
myst:
  html_meta:
    description: >-
      Gross Sharpe ratios of the European trend-following system under white noise with drift,
      AR(1) and ARFIMA long memory: exact closed forms, leading-order rules, the trade-off
      between drift and short-memory alpha across spans, and the Monte Carlo verification of the
      paper, as implemented in trendfollowing.
---

# Sharpe ratios under white noise, AR(1) and ARFIMA

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Implemented in [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

Evaluated under named processes, the [closed-form Sharpe ratio](sharpe_ratio_closed_form.md)
becomes a set of explicit rules for span selection. Under white noise with drift the Sharpe ratio
grows with the square root of the span and approaches the squared Sharpe ratio of the instrument
at a one-year span. Under AR(1) it decays with the square root of the span and takes the sign of
the autocorrelation. Under long memory it is positive at every span and can peak at an interior
span when short-term mean reversion is present. This chapter states the closed forms and their
leading-order approximations, and reports the Monte Carlo verification of Sepp and Lucic (2026).

## Overview

Each process isolates one source of trend-following performance:

| Process | Gross Sharpe ratio | Span dependence |
|---|---|---|
| White noise with drift $\mu_{\mathrm{an}}$ | $\approx\mu_{\mathrm{an}}^2\sqrt{N/\mathrm{af}}$ | Grows with $\sqrt{N}$ |
| AR(1), zero drift | $\approx 2\phi\sqrt{\mathrm{af}/N}$ | Decays with $1/\sqrt{N}$, sign of $\phi$ |
| ARFIMA(0,d,0), zero drift | Closed form through $F(d,1,1-d;\nu)$ | Positive, decays slowly for $d\gt 0$ |
| ARFIMA(1,d,0) with $\phi\lt 0\lt d$ | Numerical, from the autocorrelation | Negative at short spans, interior maximum |

A short filter monetises short-term autocorrelation and a long filter monetises drift. For a
process with both features, the Sharpe ratio turns span selection into an explicit function of the
process parameters.

## Inputs, notation, and assumptions

| Convention | This article |
|---|---|
| Return basis | Volatility-normalised daily returns $z_t$ with unit variance |
| Normalisation | $\vartheta=1$; drift as $\mu_{\mathrm{an}}=\sqrt{\mathrm{af}}\mu$ |
| Signal filter | Single filter of span $N$ unless stated; LS(250,20) in the verification table |
| Moment basis | Population moments; Gaussian innovations ($\kappa=0$) unless stated |
| Annualisation | $\mathrm{af}=260$ |
| Timing | $f_t=(\sigma_{\mathrm{target}}/\sqrt{\mathrm{af}})S_{t-1}z_t$ |
| Costs | Gross; the net ratios of the paper's figures are in the [turnover chapter](turnover_and_net_sharpe.md) |
| trendfollowing default | `sharpe_white_noise(long_span=250, sr_underlying=0.5)`; `sharpe_ar1(phi, long_span=250, n_lags=1000)`; `sharpe_arfima(d, phi=0.0, long_span=250, n_lags=2000)` |

| Symbol or input | Meaning | Units and convention |
|---|---|---|
| $\mu_{\mathrm{an}}$ | Annualised drift of $z_t$ | Sharpe ratio of the instrument |
| $\phi$, $d$ | AR(1) coefficient and fractional order | $\lvert\phi\rvert\lt 1$, $\lvert d\rvert\lt 0.5$ |

## Methodology

### White noise with drift

Under white noise $\Psi_\nu=0$, so $A_\nu=0$ and $B_\nu=(1-\nu)/(1+\nu)=1/N$.

**Proposition (Sepp and Lucic, 2026, Section 6.1).**

$$
\mathrm{SR}=\frac{\mu_{\mathrm{an}}^2\sqrt{N/\mathrm{af}}}{\sqrt{1+(\mu_{\mathrm{an}}^2/\mathrm{af})(N+1)}}\approx\mu_{\mathrm{an}}^2\sqrt{\frac{N}{\mathrm{af}}} .
$$

**Proof.** Substitute $A_\nu=0$ and $B_\nu=1/N$ into the corollary of the
[Sharpe ratio chapter](sharpe_ratio_closed_form.md): the numerator is $\mu_{\mathrm{an}}^2/\sqrt{\mathrm{af}}$
and the denominator $\sqrt{1/N+(\mu_{\mathrm{an}}^2/\mathrm{af})(1+1/N)}$. Multiply both by
$\sqrt{N}$. The approximation drops the term of order $\mu_{\mathrm{an}}^2/\mathrm{af}$. $\square$

The result needs no distributional assumption beyond serial independence and a finite second
moment: $z_t$ is independent of a signal built from earlier returns, so the variance of the product
factorises. At zero drift the Sharpe ratio is zero at every span; any drift, of either sign,
produces a positive one.

> **Insight.** At a one-year span, $N=\mathrm{af}$, the Sharpe ratio of the trend-following system
> is approximately the *square* of the Sharpe ratio of the instrument, and slightly less because
> the exact denominator exceeds one. A contract with a Sharpe ratio of 0.5 supports a trend
> Sharpe ratio of about 0.22 at one year from its drift alone.

### AR(1)

**Proposition (Sepp and Lucic, 2026, Section 6.2).** Under a zero-drift AR(1) with Gaussian
innovations,

$$
A_\nu=\frac{(1-\nu)\phi}{1-\nu\phi},
\qquad
B_\nu=\frac{(1-\nu)(1+\nu\phi)}{(1+\nu)(1-\nu\phi)},
\qquad
\mathrm{SR}=\frac{\sqrt{\mathrm{af}}A_\nu}{\sqrt{B_\nu+A_\nu^2}},
$$

and to first order in $\phi$,

$$
\mathrm{SR}\approx\phi\sqrt{\mathrm{af}(1-\nu^2)}=\frac{2\phi\sqrt{\mathrm{af}}\sqrt{N}}{N+1}\approx 2\phi\sqrt{\frac{\mathrm{af}}{N}} .
$$

**Proof.** $\Psi_\nu=\nu\phi/(1-\nu\phi)$ gives the loadings. To first order in $\phi$,
$A_\nu\approx(1-\nu)\phi$ and $B_\nu+A_\nu^2\approx(1-\nu)/(1+\nu)$, so
$\mathrm{SR}\approx\sqrt{\mathrm{af}}\phi\sqrt{(1-\nu)(1+\nu)}$, and $1-\nu^2=4N/(N+1)^2$. $\square$

The Sharpe ratio is positive for $\phi\gt 0$, when markets diverge, negative for $\phi\lt 0$, when
they mean revert, and it declines with the span. The approximation is accurate for the
coefficients that matter empirically: at $\phi=0.05$ the exact and approximate values agree to
three decimals from 5 to 250 days.

### ARFIMA long memory

Under ARFIMA(0,d,0) the generating function is $\Phi_\nu=F(d,1,1-d;\nu)$, so the Sharpe ratio is
closed-form: substitute $\Psi_\nu=F(d,1,1-d;\nu)-1$ into $A_\nu$ and $B_\nu$. For $d\gt 0$ every
autocorrelation is positive and the Sharpe ratio is positive at every span; it declines slowly,
because the long-memory tail keeps paying at slow spans. Under ARFIMA(1,d,0) with $\phi\lt 0\lt d$,
short-term mean reversion makes fast filters lose while long memory makes slow filters win, and the
Sharpe ratio has an interior maximum.

**Proposition (span trade-off).** The drift contribution grows with $\sqrt{N}$ and the
short-memory contribution decays with $1/\sqrt{N}$ (Sepp and Lucic, 2026, Section 6.2).

**Proof.** Read the leading orders of the white-noise and AR(1) propositions. $\square$

![Expected annual return, gross Sharpe ratio and net Sharpe ratio of the European system under ARFIMA with d equal to 0.02 and AR coefficients minus 0.05, 0 and 0.05 across spans from one week to two years, with analytic lines inside the Monte Carlo confidence intervals](../papers/tf_systems/paper/figures/expected_return_arfima1.PNG)

Figure 6.3 of Sepp and Lucic (2026) shows the expected annual return (A), the gross Sharpe ratio
(B) and the net Sharpe ratio at 20bp (C) under ARFIMA with $d=0.02$ and
$\phi\in\lbrace -0.05,0,0.05\rbrace$, with the closed forms as lines and Monte Carlo means of 1000 paths of 50
years as markers with 95% confidence intervals. Long memory alone makes the system profitable at
every span, and it stays profitable under short-term mean reversion beyond one month. The figure
is produced by `papers/tf_systems/replication/mc_net_sharpe_paper_figs.py` from the frozen caches
in `papers/tf_systems/replication/data/reference/`; Figures 6.1 and 6.2 show white noise and AR(1)
in the same layout.

### Verification within the full pipeline

The closed forms assume population moments of $z_t$. The Monte Carlo of the paper runs the full
pipeline instead: it simulates raw returns, estimates the 33-day EWMA volatility, normalises,
filters and trades. For LS(250,20), Table 6.1 of Sepp and Lucic (2026) reports analytic gross
Sharpe ratios of 0.062 and 0.227 under white noise with drifts 0.25 and 0.50, against simulated
0.065 and 0.234; 0.696 against 0.670 under ARFIMA with $d=0.1$; and 0.809 against 0.781 with a
drift. The analytic values track the simulations within 0.05 across all processes. The gap comes
from the lagged volatility estimator, which dampens the first-lag autocorrelation of $z_t$ from
0.050 to 0.046 under the AR(1) calibration and attenuates the Sharpe ratio by 2% to 8%. Student-t
innovations with six degrees of freedom lower the simulated gross Sharpe ratios by at most 0.009.

## Worked example

The block evaluates the closed forms and their approximations, locates the interior maximum under
ARFIMA(1,d,0), and checks the AR(1) closed form by simulation with an oracle normalisation, which
isolates the formula from the volatility-estimation effect.

```python
import numpy as np
import qis
from scipy.optimize import minimize_scalar
from scipy.signal import lfilter
from scipy.special import hyp2f1
import trendfollowing as tf

af = 260.0

# white noise with drift 0.5: exact and leading-order Sharpe ratios
for span in (21, 63, 250, 500):
    exact = tf.sharpe_white_noise(long_span=span, sr_underlying=0.5)
    closed = 0.25 * np.sqrt(span / af) / np.sqrt(1.0 + 0.25 / af * (span + 1.0))
    np.testing.assert_allclose(exact, closed, rtol=1e-10)
    assert exact < tf.sharpe_white_noise_approx(long_span=span, sr_underlying=0.5)
np.testing.assert_allclose(tf.sharpe_white_noise(long_span=260, sr_underlying=0.5), 0.2235,
                           atol=5e-5)
assert tf.sharpe_white_noise(long_span=63, sr_underlying=0.0) == 0.0

# AR(1): exact against the first-order rule 2 phi sqrt(af N) / (N + 1)
for span in (5, 21, 63, 250):
    exact = tf.sharpe_ar1(phi=0.05, long_span=span)
    np.testing.assert_allclose(exact, tf.sharpe_ar1_approx(phi=0.05, long_span=span), atol=5e-4)
    np.testing.assert_allclose(tf.sharpe_ar1(phi=-0.05, long_span=span), -exact, rtol=1e-12)
np.testing.assert_allclose([tf.sharpe_ar1(phi=0.05, long_span=span) for span in (5, 21, 63, 250)],
                           [0.6008, 0.3361, 0.2002, 0.1017], atol=5e-5)

# ARFIMA(0,d,0): the hypergeometric closed form equals the truncated sum
d, span = 0.02, 63
nu = tf.span_to_nu(span)
psi_nu = hyp2f1(d, 1.0, 1.0 - d, nu) - 1.0
A = (1.0 - nu) * psi_nu / nu
B = (1.0 - nu) * (1.0 + 2.0 * psi_nu) / (1.0 + nu)
np.testing.assert_allclose(tf.sharpe_arfima(d=d, long_span=span), np.sqrt(af) * A / np.sqrt(B + A ** 2),
                           rtol=1e-9)
np.testing.assert_allclose([tf.sharpe_arfima(d=d, long_span=s) for s in (5, 21, 63, 250, 500)],
                           [0.4021, 0.3583, 0.2888, 0.1995, 0.1609], atol=5e-5)

# ARFIMA(1,d,0) with phi = -0.05: losses at fast spans, an interior maximum near 146 days
rho_mixed = tf.population_acf(n_lags=2000, phi=-0.05, d=0.02)
assert tf.compute_annualised_sharpe(rho=rho_mixed, long_span=5) < 0.0
best = minimize_scalar(lambda s: -tf.compute_annualised_sharpe(rho=rho_mixed, long_span=s),
                       bounds=(5.0, 1500.0), method='bounded')
np.testing.assert_allclose(best.x, 146.0, atol=1.0)
np.testing.assert_allclose(-best.fun, 0.1024, atol=5e-5)

# Monte Carlo with oracle normalisation: unit-variance AR(1) z, phi = 0.05
rng = np.random.default_rng(20261001)
z = lfilter([1.0], [1.0, -0.05], rng.standard_normal(2_000_000)) * np.sqrt(1.0 - 0.05 ** 2)
for span in (21, 63):
    signal = qis.compute_ewm_long_short(a=z, init_value=0.0, long_span=span, short_span=None)
    f = signal[:-1] * z[1:]
    simulated = np.sqrt(af) * f[2000:].mean() / f[2000:].std()
    standard_error = np.sqrt(af / f[2000:].size)
    assert abs(simulated - tf.sharpe_ar1(phi=0.05, long_span=span)) < 3.0 * standard_error
```

Under white noise with $\mu_{\mathrm{an}}=0.5$ the one-year Sharpe ratio is 0.224, below the
leading-order 0.25. Under AR(1) with $\phi=0.05$ it falls from 0.60 at one week to 0.10 at one year,
and the first-order rule matches to three decimals. Under ARFIMA(1,d,0) with $\phi=-0.05$ and
$d=0.02$, fast filters lose and the gross Sharpe ratio peaks at 0.102 near 146 days.

## Implementation in trendfollowing

| Quantity | Formula | trendfollowing entry point |
|---|---|---|
| White noise with drift, exact | the proposition, any filter | `trendfollowing.sharpe_white_noise(long_span=250, short_span=None, sr_underlying=0.5, af=260.0)` |
| White noise, leading order | $\mu_{\mathrm{an}}^2\sqrt{N/\mathrm{af}}$ | `trendfollowing.sharpe_white_noise_approx(long_span=250, sr_underlying=0.5, af=260.0)` |
| AR(1), exact | through `population_acf(n_lags, phi)` | `trendfollowing.sharpe_ar1(phi, long_span=250, short_span=None, sr_underlying=0.0, af=260.0, n_lags=1000)` |
| AR(1), leading order | $2\phi\sqrt{\mathrm{af}N}/(N+1)$, zero drift | `trendfollowing.sharpe_ar1_approx(phi, long_span=250, af=260.0)` |
| ARFIMA(1,d,0), exact | through the Sowell autocorrelation, truncated | `trendfollowing.sharpe_arfima(d, phi=0.0, long_span=250, short_span=None, sr_underlying=0.0, af=260.0, n_lags=2000)` |
| Any autocorrelation | the general corollary | `trendfollowing.compute_annualised_sharpe(rho, ...)` |

The process functions are thin wrappers of `compute_annualised_sharpe` in
[sharpe.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/analytics/sharpe.py)
with Gaussian innovations; pass `kappa` and `ma_weights` to the general function for heavy tails.
API reference: {py:func}`trendfollowing.sharpe_white_noise`,
{py:func}`trendfollowing.sharpe_white_noise_approx`, {py:func}`trendfollowing.sharpe_ar1`,
{py:func}`trendfollowing.sharpe_ar1_approx` and {py:func}`trendfollowing.sharpe_arfima`.

> **Pitfall.** The `_approx` functions are leading-order terms for intuition, not aliases of the
> exact functions: `sharpe_white_noise_approx` overstates the exact ratio at long spans (0.347
> against 0.285 at 500 days with $\mu_{\mathrm{an}}=0.5$), and `sharpe_ar1_approx` ignores drift.

## Interpretation and limitations

- The rules are population statements under stationary parameters. The empirical first-lag
  autocorrelation of normalised futures returns is small, about 0.01 to 0.04, so the AR(1) channel
  is economically small at slow spans and decisive only at fast spans, where costs dominate.
- Long memory is the process feature that lets slow filters earn from autocorrelation; its
  calibration $d$ is uncertain, and the paper's process figures use $d=0.02$.
- The verification shows that the full pipeline attenuates the Sharpe ratio by a few percent;
  population closed forms slightly overstate what a system with an estimated volatility earns.
- The squared-drift channel rewards any persistent drift. Over a sample, the realised drift of a
  contract is a noisy estimate of its population drift; see the
  [attribution guide](predict_sharpe_from_acf.md).

## See also

- [The closed-form Sharpe ratio](sharpe_ratio_closed_form.md)
- [Return-generating processes](return_processes.md)
- [Turnover, trading costs and the net Sharpe ratio](turnover_and_net_sharpe.md)
- [Closed-form analytics and span selection](closed_form_analytics.md)
- [Bibliography](bibliography.md)

## References

1. Sepp, A., and Lucic, V. (2026). The Science and Practice of Trend-Following Systems. Working paper. [arXiv:2607.19497](https://arxiv.org/abs/2607.19497); [SSRN 3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787). Section 6 evaluates the closed forms under named processes and verifies them in Table 6.1 and Figures 6.1 to 6.3.
2. Hosking, J. R. M. (1981). Fractional Differencing. *Biometrika*, 68(1), 165–176. [DOI: 10.1093/biomet/68.1.165](https://doi.org/10.1093/biomet/68.1.165). The ARFIMA(0,d,0) autocorrelation function.
3. Grebenkov, D. S., and Serror, J. (2014). Following a Trend with an Exponential Moving Average: Analytical Results for a Gaussian Model. *Physica A*, 394, 288–303. [DOI: 10.1016/j.physa.2013.10.007](https://doi.org/10.1016/j.physa.2013.10.007). EWMA trend following under Gaussian dynamics.
4. Sepp, A., and Lucic, V. trendfollowing: Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python. [Software citation metadata](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).
