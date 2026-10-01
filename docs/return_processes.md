---
myst:
  html_meta:
    description: >-
      The return-generating processes of the trendfollowing handbook: white noise with drift,
      AR(1), MA(1), ARFIMA(0,d,0) and ARFIMA(1,d,0), with their autocorrelation functions,
      moving-average weights, the hypergeometric generating function of long memory, and the
      Monte Carlo path engine.
---

# Return-generating processes

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Implemented in [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

A return-generating process specifies the joint law of a sequence of returns. For trend following
the relevant features are the drift and the autocorrelation function: positive autocorrelation
at the lags a filter reads is the source of trend-following profits at zero drift. This chapter
defines the processes that the handbook's closed forms are evaluated under (white noise with drift,
AR(1), MA(1) and the fractional ARFIMA family), gives their autocorrelation functions and
moving-average representations, and documents the simulation engine that verifies the closed
forms by Monte Carlo.

## Overview

The closed forms of Part II hold at two levels of generality (Sepp and Lucic, 2026, Section 1).
The expected return requires only a stationary mean, variance and autocorrelation function. The
Sharpe ratio additionally requires a causal linear process with independent innovations, which
fixes the fourth moments. Any process with an autocorrelation function can therefore be fed to
the expected-return formula, and any linear process to the Sharpe formula, including an
empirical autocorrelation function estimated from data.

The named processes isolate three features:

| Process | Feature | Trend-following content |
|---|---|---|
| White noise with drift | Drift only | Profits only from the squared drift, growing with the span |
| AR(1) | Short memory, geometric decay | Profits at short spans if $\phi\gt 0$, losses if $\phi\lt 0$ |
| MA(1) | One lag of dependence | The shortest possible memory |
| ARFIMA(0,d,0) | Long memory, hyperbolic decay | Profits at every span if $d\gt 0$ |
| ARFIMA(1,d,0) | Short and long memory together | Profits at slow spans despite short-term mean reversion |

## Inputs, notation, and assumptions

| Convention | This article |
|---|---|
| Return basis | Daily returns $r_t=\mu+x_t$ of a model process; the closed forms apply them as $z_t$ |
| Normalisation | Innovation variance $1/\mathrm{af}$ in the paper's simulations; unit variance in the autocorrelation formulas |
| Signal filter | Not applicable; the processes are inputs to every filter |
| Moment basis | Population moments; Monte Carlo sample moments in the verification |
| Annualisation | $\mu=\mu_{\mathrm{an}}/\mathrm{af}$ for the raw drift; normalised drift $\mu_{\mathrm{an}}$ as defined below |
| Timing | Causal: $x_t$ depends on innovations up to $t$ |
| Costs | Not applicable |
| trendfollowing default | `population_acf(n_lags=250, phi=0.0, d=0.0)`; the closed forms use 1000 to 2000 lags |

| Symbol or input | Meaning | Units and convention |
|---|---|---|
| $x_t$ | Zero-mean part of the return | Per day |
| $\theta$ | MA(1) coefficient | The `phi` argument of `expected_pnl_ma1` |
| $\tilde r_t$ | ARFIMA(0,d,0) process with unit innovations | Dimensionless |
| $\gamma(m)$ | Autocovariance at lag $m$ | Units of variance |
| $V_{\phi,d}$ | Variance of the unscaled ARFIMA(1,d,0) process | Dimensionless |
| $F(a,b,c;y)$ | Gauss hypergeometric function | Written 2F1 in SciPy as `hyp2f1` |
| $\Gamma$ | Gamma function | |

## Methodology

### Stationary moments and linear processes

**Definition (population moments).** A process satisfies the moment assumption of Sepp and
Lucic (2026, Section 4.5) when $z_t$ has constant mean $\mu$, constant variance $\vartheta\gt 0$ and
autocorrelation $\rho(m)$ depending only on the lag.

**Definition (linear process).** The normalised returns admit a Wold representation

$$
z_t=\mu+\sqrt{\vartheta}\sum_{s=0}^{\infty}\psi_s\epsilon_{t-s},
\qquad
\sum_{s=0}^{\infty}\psi_s^2=1,
$$

with independent identically distributed innovations of zero mean, unit variance, zero third
moment and finite excess kurtosis $\kappa=\mathbb{E}[\epsilon_t^4]-3$ (Hamilton, 1994, Chapter 4).

**Identity (autocorrelation from weights).** $\rho(m)=\sum_{s\ge 0}\psi_s\psi_{s+m}$.

**Proof.** $\operatorname{Cov}[z_t,z_{t-m}]=\vartheta\sum_{s,u}\psi_s\psi_u\mathbb{E}[\epsilon_{t-s}\epsilon_{t-m-u}]$,
and the expectation is one exactly when $s=u+m$. Divide by $\vartheta$. $\square$

A stationary Gaussian process is a linear process with Gaussian innovations, $\kappa=0$.

### White noise with drift

$r_t=\mu+\epsilon_t$ with independent innovations: $\rho(m)=\delta_{m0}$, $\psi_0=1$. All
trend-following profit comes from the drift.

### AR(1)

**Definition.** $r_t=\mu+x_t$ with $x_t=\phi x_{t-1}+\epsilon_t$ and $\lvert\phi\rvert\lt 1$. The
drift sits outside the autoregression, so it carries no amplification $1/(1-\phi)$.

**Identity.** $\rho(m)=\phi^m$ and $\psi_s=\sqrt{1-\phi^2}\phi^s$.

**Proof.** The stationary solution is $x_t=\sum_{s\ge 0}\phi^s\epsilon_{t-s}$ with variance
$1/(1-\phi^2)$ per unit innovation variance; normalising the weights to unit sum of squares gives
$\psi_s$, and the identity above gives $\sum_s(1-\phi^2)\phi^{2s+m}=\phi^m$. $\square$

**Proposition (aggregated variance).** The variance of the $T$-day sum of an AR(1) process
relative to $T$ times the daily variance converges to $(1+\phi)/(1-\phi)$.

**Proof.** The ratio equals $1+2\sum_{h=1}^{T-1}(1-h/T)\phi^h$, which tends to
$1+2\phi/(1-\phi)=(1+\phi)/(1-\phi)$. $\square$

With $\phi\gt 0$ markets are divergent: the volatility of aggregated returns settles above the
square-root-of-time benchmark by $\sqrt{(1+\phi)/(1-\phi)}$. With $\phi\lt 0$ they are mean
reverting and it settles below. When the innovations have variance $1/\mathrm{af}$, the stationary
variance of $x_t$ is $1/(\mathrm{af}(1-\phi^2))$, so a raw annual drift $\mu_{\mathrm{an}}^{\mathrm{raw}}$
is a normalised drift $\mu_{\mathrm{an}}=\mu_{\mathrm{an}}^{\mathrm{raw}}\sqrt{1-\phi^2}$, a 0.1%
effect at $\lvert\phi\rvert=0.05$.

### MA(1)

$x_t=\epsilon_t+\theta\epsilon_{t-1}$ has $\rho(1)=\theta/(1+\theta^2)$ and $\rho(m)=0$ for
$m\ge 2$. It is the process of `expected_pnl_ma1`, whose argument named `phi` is $\theta$.

### Long memory: ARFIMA(0,d,0)

**Definition (Granger and Joyeux, 1980; Hosking, 1981).** For $-1/2\lt d\lt 1/2$, the fractionally
integrated process has the moving-average representation

$$
\tilde r_t=\sum_{j=0}^{\infty}\frac{\Gamma(j+d)}{\Gamma(j+1)\Gamma(d)}\epsilon_{t-j},
$$

with variance and autocorrelation

$$
\gamma(0)=\frac{\Gamma(1-2d)}{\Gamma(1-d)^2},
\qquad
\rho(m)=\frac{\Gamma(1-d)\Gamma(m+d)}{\Gamma(d)\Gamma(m-d+1)} .
$$

At $d=0$ the process is white noise. The autocorrelation satisfies the stable recursion
$\rho(m)=\rho(m-1)(m-1+d)/(m-d)$, so $\rho(1)=d/(1-d)$, and it decays hyperbolically,
$\rho(m)\approx\Gamma(1-d)m^{2d-1}/\Gamma(d)$, with the sign of $d$. For $d\gt 0$ the
autocorrelations are not summable, which is long memory.

**Identity (generating function; Sepp and Lucic, 2026, Section 6.3).** For $0\lt\nu\lt 1$,

$$
\Phi_\nu=\sum_{m=0}^{\infty}\nu^m\rho(m)=F(d,1,1-d;\nu).
$$

**Proof.** The Gauss series is $F(d,1,1-d;\nu)=\sum_{m\ge 0}\frac{p_m(d)p_m(1)}{p_m(1-d)m!}\nu^m$
with rising factorials $p_m(a)=\Gamma(a+m)/\Gamma(a)$. Since $p_m(1)=m!$, the coefficient is
$p_m(d)/p_m(1-d)=\Gamma(m+d)\Gamma(1-d)/(\Gamma(d)\Gamma(m+1-d))=\rho(m)$. $\square$

The identity makes every closed form of Part II exact in closed form under the pure fractional
process, because they depend on the process only through $\Phi_\nu$ at the filter spans.

### Short and long memory: ARFIMA(1,d,0)

**Definition.** $r_t=\mu+x_t$ with $x_t=\phi x_{t-1}+\tilde r_t/\sqrt{\mathrm{af}}$. The
autocorrelation is the closed form of Sowell (1992),

$$
\rho(m)=\rho_{\tilde r}(m)\frac{F(1,d+m,1-d+m;\phi)+F(1,d-m,1-d-m;\phi)-1}{(1-\phi)F(1,1+d,1-d;\phi)},
$$

where $\rho_{\tilde r}$ is the ARFIMA(0,d,0) autocorrelation, and the unscaled process
$\tilde x_t=\phi\tilde x_{t-1}+\tilde r_t$ has variance $V_{\phi,d}=\gamma(0)F(1,1+d,1-d;\phi)/(1+\phi)$.
The normalised drift is $\mu_{\mathrm{an}}=\mu_{\mathrm{an}}^{\mathrm{raw}}/\sqrt{V_{\phi,d}}$: at
$(\phi,d)=(0,0.1)$, $V=\Gamma(0.8)/\Gamma(0.9)^2\approx 1.019$ turns a raw drift of 0.50 into 0.495.

The AR part acts at short lags and the fractional part at long lags. With $\phi=-0.05$ and
$d=0.02$, the first-lag autocorrelation is negative while the tail is positive: short-term mean
reversion with long-term trend persistence, the configuration under which trend following stays
profitable at slow spans (see the [Sharpe ratio under processes](sharpe_under_processes.md)).

### Truncation

The closed forms evaluate $\Psi_\nu=\sum_{m\ge 1}\nu^m\rho(m)$ on a truncated autocorrelation
array. The weights $\nu^m$ bound the remainder: with 2000 lags, the remainder relative to
$\Psi_\nu$ is below $10^{-4}$ at the span of 520 days for $d\le 0.1$ (Sepp and Lucic, 2026,
Section 5.1; `verify_garch_and_truncation.py` in the replication folder).

### Simulation

The path engine generates paths of each process with a common interface. White noise, AR(p) and
MA(q) are Numba recursions; ARFIMA uses the fast fractional-differencing algorithm of Jensen and
Nielsen (2014) on a FFT grid, with $2^{16}$ warmup observations to approximate the stationary
start. The paper's verification design simulates 1000 paths of 50 years of daily returns with
time step $1/\mathrm{af}$, normalises them with the 33-day EWMA volatility and runs the European
system at $\sigma_{\mathrm{target}}=15\%$ (Sepp and Lucic, 2026, Section 6).

## Worked example

The block checks the autocorrelation functions against their closed forms, the hypergeometric
generating function, the moving-average weights and the aggregated-variance limit, then estimates
the first-lag autocorrelation from simulated AR(1) and ARFIMA paths.

```python
import numpy as np
from scipy.special import gamma, hyp2f1
import trendfollowing as tf
from trendfollowing.analytics.autocorrelation import ma_weights, power_autocorr
from trendfollowing.processes.path_engine import ProcessType, generate_paths, set_seed

# AR(1): rho(m) = phi^m and psi_s = sqrt(1 - phi^2) phi^s
phi = 0.05
np.testing.assert_allclose(tf.population_acf(n_lags=4, phi=phi), phi ** np.arange(5))
psi_ar = ma_weights(phi=phi, d=0.0, n_lags=2000)
np.testing.assert_allclose(psi_ar[:3], np.sqrt(1.0 - phi ** 2) * phi ** np.arange(3))

# aggregated variance ratio of AR(1) tends to (1 + phi) / (1 - phi)
horizon = 20_000
h = np.arange(1, horizon)
ratio = 1.0 + 2.0 * np.sum((1.0 - h / horizon) * phi ** h)
np.testing.assert_allclose(ratio, (1.0 + phi) / (1.0 - phi), rtol=1e-4)

# ARFIMA(0,d,0): Gamma-function closed form, rho(1) = d / (1 - d)
d = 0.02
lags = np.arange(51)
rho_d = tf.population_acf(n_lags=50, d=d)
closed_form = gamma(1.0 - d) * gamma(lags + d) / (gamma(d) * gamma(lags - d + 1.0))
np.testing.assert_allclose(rho_d, closed_form, rtol=1e-12)
np.testing.assert_allclose(rho_d[1], d / (1.0 - d))

# the generating function is the hypergeometric function F(d, 1, 1 - d; nu)
rho_long = tf.population_acf(n_lags=2000, d=d)
for span in (5, 63, 250):
    nu = tf.span_to_nu(span)
    np.testing.assert_allclose(1.0 + tf.compute_psi_nu(rho_long, nu), hyp2f1(d, 1.0, 1.0 - d, nu),
                               rtol=1e-9)

# ARFIMA(1,d,0): short-term mean reversion with a long-memory tail
rho_mixed = tf.population_acf(n_lags=5, phi=-0.05, d=0.02)
np.testing.assert_allclose(rho_mixed[1], -0.030111, atol=5e-7)
assert np.all(rho_mixed[2:] > 0.0)

# moving-average weights reproduce the autocorrelation: rho(m) = sum psi_s psi_{s+m}
psi_frac = ma_weights(phi=0.0, d=0.1)  # 8000 lags, normalised to unit sum of squares
implied = [np.sum(psi_frac[:-m] * psi_frac[m:]) for m in (1, 2, 3)]
np.testing.assert_allclose(implied, tf.population_acf(n_lags=3, d=0.1)[1:], atol=2e-4)

# power_autocorr returns autocovariances with lag 0 set to zero, not autocorrelations
gamma0 = gamma(1.0 - 2.0 * d) / gamma(1.0 - d) ** 2
np.testing.assert_allclose(power_autocorr(delta=d, n=3), [0.0, gamma0 * rho_d[1], gamma0 * rho_d[2]])

# drift normalisation of the paper's ARFIMA rows: V = Gamma(0.8) / Gamma(0.9)^2
variance_scale = gamma(0.8) / gamma(0.9) ** 2
np.testing.assert_allclose([variance_scale, 0.5 / np.sqrt(variance_scale)], [1.019, 0.495], atol=5e-4)


def lag_one_autocorrelation(paths):
    x = paths - paths.mean(axis=0)
    return np.sum(x[1:] * x[:-1]) / np.sum(x * x)


# Monte Carlo: the Numba engine draws from Numba's generator, ARFIMA from NumPy's
set_seed(20261001)
ar_paths = generate_paths(process_type=ProcessType.AR_P, phi=np.array([phi]), n_path=100,
                          m_times=10_000)
np.testing.assert_allclose(lag_one_autocorrelation(ar_paths[100:]), phi, atol=0.004)

np.random.seed(20261001)
arfima_paths = generate_paths(process_type=ProcessType.ARFIMA, ar_params=[0.0], delta=0.1,
                              n_path=4, m_times=20_000)
np.testing.assert_allclose(lag_one_autocorrelation(arfima_paths), 0.1 / 0.9, atol=0.015)
np.testing.assert_allclose(arfima_paths.var(), gamma(0.8) / gamma(0.9) ** 2, atol=0.05)
```

## Implementation in trendfollowing

| Quantity | Formula | trendfollowing entry point |
|---|---|---|
| Autocorrelation function | $\rho(m)$, $m=0,\dots,$ `n_lags`, for white noise, AR(1), ARFIMA(0,d,0) and ARFIMA(1,d,0) | `trendfollowing.population_acf(n_lags=250, phi=0.0, d=0.0)` |
| Autocovariance, ARFIMA convention | $\gamma(m)$ with lag 0 set to zero; $\phi^m$ on the AR branch | `trendfollowing.power_autocorr(delta, phi=0.0, n=100)` |
| Moving-average weights | $\psi_s$ of ARFIMA(1,d,0), unit sum of squares | `trendfollowing.analytics.autocorrelation.ma_weights(phi=0.0, d=0.0, n_lags=8000)` |
| Process selector | white noise, AR(p), MA(q), ARFIMA | `trendfollowing.processes.path_engine.ProcessType` |
| Path simulation | array of shape `(m_times, n_path)` | `trendfollowing.processes.path_engine.generate_paths(process_type, phi, ar_params, delta, n_path, m_times, mean, noise_std, dt)` |
| ARFIMA series | fractional differencing by FFT | `trendfollowing.processes.arfima.arfima(ar_params, d, ma_params, n_points, noise_std=1, noise_alpha=2.0, warmup=0)` |

The autocorrelation functions live in
[autocorrelation.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/analytics/autocorrelation.py),
and the simulation in
[path_engine.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/processes/path_engine.py)
and [arfima.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/processes/arfima.py),
which adapts the ARFIMA generator of Kononovicius.
API reference: {py:func}`trendfollowing.population_acf`, {py:func}`trendfollowing.power_autocorr`,
{py:func}`trendfollowing.analytics.autocorrelation.ma_weights` and
{py:func}`trendfollowing.processes.path_engine.generate_paths`.

Contract details:

- `population_acf` raises `ValueError` unless $\lvert\phi\rvert\lt 1$ and $\lvert d\rvert\lt 0.5$, and
  returns `n_lags + 1` values starting with $\rho(0)=1$. It selects the branch with `np.isclose`, so
  a tiny nonzero $d$ is treated as zero.
- `generate_paths` adds the drift `mean * dt` and the noise `sqrt(dt) * noise_std * eps` to each
  recursion, with time step `dt`. The AR(p) and MA(q) recursions start from zero
  without a burn-in; discard the first observations, as the example does. `phi` must be a NumPy
  array of AR or MA coefficients.
- White noise, AR(p) and MA(q) draw from Numba's generator, seeded with
  `trendfollowing.processes.path_engine.set_seed`; ARFIMA draws through SciPy from NumPy's global
  generator, seeded with `np.random.seed`.

> **Pitfall.** `power_autocorr` has two conventions in one function: its AR branch returns the
> autocorrelations $\phi^h$ with lag zero equal to one, and its ARFIMA branches return
> autocorrelations scaled by $\Gamma(1-2d)/\Gamma(1-d)^2$ for every $\phi$, with lag zero set to
> zero. Its gamma functions overflow, so lags from 171 on are zero or NaN. It is not an
> autocorrelation function; use `population_acf`, which has no length limit.

## Interpretation and limitations

- The processes are stationary with constant parameters. The empirical autocorrelation of
  normalised futures returns drifts across decades: the lag-1 autocorrelation of $z_t$ across the
  paper's universe falls from about 0.04 in the 1990s to about 0.01 after 2010 (Sepp and Lucic,
  2026, Section 7.3).
- The first-lag calibration $\rho(1)=d/(1-d)$ maps the observed range 0.01 to 0.04 into
  $d$ from about 0.01 to 0.04; the paper's process figures use $d=0.02$.
- Long memory is hard to estimate: a small $d$ produces small autocorrelations at every lag, and
  their sum over long lags is what the filter monetises.
- A linear process excludes volatility clustering and leverage; the
  [normalisation chapter](volatility_normalisation.md) explains why normalised returns are
  close to linear in practice.

## See also

- [Notation and conventions](notation_and_conventions.md)
- [The P&L decomposition: autocorrelation and drift channels](pnl_decomposition.md)
- [The closed-form Sharpe ratio](sharpe_ratio_closed_form.md)
- [Sharpe ratios under white noise, AR(1) and ARFIMA](sharpe_under_processes.md)
- [Bibliography](bibliography.md)

## References

1. Sepp, A., and Lucic, V. (2026). The Science and Practice of Trend-Following Systems. Working paper. [arXiv:2607.19497](https://arxiv.org/abs/2607.19497); [SSRN 3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787). Sections 5 and 6 state the linear-process assumption and the processes.
2. Granger, C. W. J., and Joyeux, R. (1980). An Introduction to Long-Memory Time Series Models and Fractional Differencing. *Journal of Time Series Analysis*, 1(1), 15–29. [DOI: 10.1111/j.1467-9892.1980.tb00297.x](https://doi.org/10.1111/j.1467-9892.1980.tb00297.x). The ARFIMA process.
3. Hosking, J. R. M. (1981). Fractional Differencing. *Biometrika*, 68(1), 165–176. [DOI: 10.1093/biomet/68.1.165](https://doi.org/10.1093/biomet/68.1.165). The ARFIMA(0,d,0) autocorrelation function.
4. Sowell, F. (1992). Maximum Likelihood Estimation of Stationary Univariate Fractionally Integrated Time Series Models. *Journal of Econometrics*, 53(1–3), 165–188. [DOI: 10.1016/0304-4076(92)90084-5](https://doi.org/10.1016/0304-4076%2892%2990084-5). The ARFIMA(1,d,0) autocovariance.
5. Hamilton, J. D. (1994). *Time Series Analysis*. Princeton University Press. The Wold representation.
6. Jensen, A. N., and Nielsen, M. Ø. (2014). A Fast Fractional Difference Algorithm. *Journal of Time Series Analysis*, 35(5), 428–436. [DOI: 10.1111/jtsa.12074](https://doi.org/10.1111/jtsa.12074). The FFT fractional differencing behind the ARFIMA simulation.
7. Sepp, A., and Lucic, V. trendfollowing: Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python. [Software citation metadata](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).
