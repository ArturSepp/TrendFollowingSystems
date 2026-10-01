---
myst:
  html_meta:
    description: >-
      Realised Sharpe ratios of trend-following backtests and their comparison: the arithmetic
      estimator, its sampling error, the Ledoit-Wolf HAC test for the difference of two Sharpe
      ratios with its delta-method standard error and Newey-West lag rule, and regime-conditional
      Sharpe ratios through qis, as implemented in trendfollowing.
---

# Realised Sharpe ratios and their comparison

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Implemented in [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

A realised Sharpe ratio is an estimate, and two realised Sharpe ratios computed on the same period
are correlated estimates. Deciding whether one trend-following system beats another, or replicates
a benchmark, needs the standard error of their difference, which depends on the correlation of the
two return series and on their serial dependence. This chapter defines the realised estimator of
the handbook, states its sampling error, and documents the robust test of Ledoit and Wolf (2008)
that the paper uses to compare its three systems with the SG Trend Index.

## Overview

The closed forms of Part II give population Sharpe ratios; backtests give realised ones. Three
questions connect them:

1. How is a realised Sharpe ratio computed, and how precise is it?
2. How is the difference of two Sharpe ratios on paired returns tested, allowing for correlation,
   heavy tails and serial dependence?
3. How is a Sharpe ratio conditioned on a market regime?

## Inputs, notation, and assumptions

| Convention | This article |
|---|---|
| Return basis | Periodic simple excess returns of strategies or benchmarks, on a common calendar |
| Normalisation | Not applicable |
| Signal filter | Not applicable |
| Moment basis | Sample moments; the test uses population-variance moments $\hat\gamma_i-\hat\mu_i^2$ |
| Annualisation | $\sqrt{\mathrm{af}}$ with the frequency of the returns: 260 daily, 12 monthly, 4 quarterly |
| Timing | Paired returns joined on the intersection of their dates, missing values dropped |
| Costs | As supplied: the paper tests monthly returns net of costs and 2/20 fees |
| trendfollowing default | `compute_realized_sharpe(returns, af=260.0, ddof=1)`; `sharpe_difference_test(returns1, returns2, n_lags=None, af=12.0)` |

| Symbol or input | Meaning | Units and convention |
|---|---|---|
| $T$ | Number of paired observations | Periods |
| $Y$ | Sample length in years, $T/\mathrm{af}$ | Years |
| $\hat\mu_i$, $\hat\gamma_i$ | Sample mean and second moment of returns $i=1,2$ | Per period |
| $\hat\sigma_i$ | $\sqrt{\hat\gamma_i-\hat\mu_i^2}$ | Per period |
| $\Delta$ | Difference of the per-period Sharpe ratios | Per period |
| $y_t$ | Demeaned moment vector | Four components |
| $\hat\Psi$ | Bartlett-kernel HAC covariance of $y_t$ | |
| $K$ | Number of Bartlett lags | Default $\lfloor 4(T/100)^{2/9}\rfloor$ |

## Methodology

### The realised Sharpe ratio

**Definition.** For periodic simple excess returns $f_1,\dots,f_T$,

$$
\widehat{\mathrm{SR}}=\sqrt{\mathrm{af}}\frac{\bar f}{s(f)},
$$

where $s(f)$ is the sample standard deviation with `ddof` degrees of freedom: 1 by default, 0 to
reproduce the paper's attribution exhibits. It is the sample counterpart of the arithmetic
convention of the [notation chapter](notation_and_conventions.md).

**Proposition (sampling error; Lo, 2002).** For independent Gaussian returns, the annualised
estimator has asymptotic variance

$$
\operatorname{Var}\big[\widehat{\mathrm{SR}}\big]\approx\frac{1+\mathrm{SR}^2/(2\mathrm{af})}{Y}\approx\frac{1}{Y} .
$$

**Proof.** The per-period estimator has asymptotic variance $(1+\mathrm{SR}^2/(2\mathrm{af}))/T$, since the per-period ratio is
$\mathrm{SR}/\sqrt{\mathrm{af}}$ (Lo, 2002); multiply by $\mathrm{af}$ and use
$T=\mathrm{af}Y$. $\square$

> **Insight.** The standard error of an annualised Sharpe ratio is about $1/\sqrt{Y}$ whatever the
> sampling frequency: 0.2 over 25 years, 0.14 over 50. Daily data do not make a Sharpe ratio more
> precise than monthly data of the same span; only a longer history does. Serial correlation of
> the strategy returns, which persistent trend signals create, changes the error further
> (Lo, 2002).

### The Ledoit–Wolf test

For paired returns $(f_{1,t},f_{2,t})$, the hypothesis of equal Sharpe ratios is a
statement about the moment vector $(\mu_1,\mu_2,\gamma_1,\gamma_2)$ with $\gamma_i=\mathbb{E}[f_i^2]$.

**Definition (test statistic; Ledoit and Wolf, 2008).** With $\Delta=\hat\mu_1/\hat\sigma_1-\hat\mu_2/\hat\sigma_2$,
the demeaned moment vector

$$
y_t=\left(f_{1,t}-\hat\mu_1,f_{2,t}-\hat\mu_2,f_{1,t}^2-\hat\gamma_1,f_{2,t}^2-\hat\gamma_2\right),
$$

its Bartlett-kernel HAC covariance

$$
\hat\Psi=\hat\Gamma_0+\sum_{k=1}^{K}\left(1-\frac{k}{K+1}\right)\left(\hat\Gamma_k+\hat\Gamma_k^{\top}\right),
\qquad
\hat\Gamma_k=\frac{1}{T}\sum_{t=k+1}^{T}y_ty_{t-k}^{\top},
$$

and the gradient of $\Delta$ in the moments

$$
\nabla=\left(\frac{\hat\gamma_1}{\hat\sigma_1^3},-\frac{\hat\gamma_2}{\hat\sigma_2^3},-\frac{\hat\mu_1}{2\hat\sigma_1^3},\frac{\hat\mu_2}{2\hat\sigma_2^3}\right),
$$

the standard error is $\mathrm{se}=\sqrt{\nabla^{\top}\hat\Psi\nabla/T}$ and the statistic
$t=\Delta/\mathrm{se}$ is compared with the standard normal, two sided.

**Proof (delta method).** $\Delta$ is a smooth function of the sample moments, whose joint
asymptotic covariance is $\Psi/T$ under stationarity and mixing; $\hat\Psi$ estimates the long-run
covariance consistently with $K$ growing slowly in $T$ (Newey and West, 1987). Differentiating
$\mu/\sqrt{\gamma-\mu^2}$ gives $\gamma/\sigma^3$ in $\mu$ and $-\mu/(2\sigma^3)$ in $\gamma$. $\square$

The statistic is invariant to rescaling both series, because $\Delta$ and $\mathrm{se}$ are
ratios of moments of the same degree. Ledoit and Wolf (2008) also propose a studentised bootstrap
for small samples; the implementation uses the normal limit.

### The paper's comparison with the SG Trend Index

On monthly returns net of transaction costs and 2/20 fees from 31 December 1999 to 30 June 2026,
the European, American and TSMOM systems at matched parameters deliver annualised Sharpe ratios
of 0.47, 0.50 and 0.55, against 0.47 for the SG Trend Index. The differences carry p-values of 0.96,
0.82 and 0.62, so the test does not reject equality for any system (Sepp and Lucic, 2026,
Section 7.2). Failure to reject is consistent with the replication claim but is not evidence of
equivalence: with a standard error of about 0.2 over 26 years, the test cannot distinguish Sharpe
ratios closer than about 0.4.

### Regime-conditional Sharpe ratios

The paper's grid backtests also report a **bear Sharpe ratio**: the Sharpe ratio of a system
conditioned on the 16% worst quarters of the 60/40 benchmark, the one-sigma tail of the normal
distribution. Under the arithmetic convention the bear, normal and bull contributions add up to
the total Sharpe ratio exactly. The calculation is delegated to qis: `trendfollowing.backtests`
defines the classifier `qis.BenchmarkReturnsQuantilesRegime(freq='QE', q=[0, 0.16, 0.84, 1])` and
the performance parameters `PERF_PARAMS` with `qis.perfstats.config.SharpeConvention.ARITHMETIC`,
and calls `qis.compute_bnb_regimes_pa_perf_table`. The
[qis regime chapter](https://quantinveststrats.readthedocs.io/en/latest/regime_conditional_performance.html)
derives the decomposition.

## Worked example

The block computes the realised Sharpe ratios of two correlated monthly series, reproduces the
standard error of the test by hand, checks the default lag rule, the p-value and the scale
invariance, and estimates the size of the test under the null by simulation.

```python
import numpy as np
import pandas as pd
from scipy.stats import norm
import trendfollowing as tf
from trendfollowing.analytics.sharpe_test import sharpe_difference_test

rng = np.random.default_rng(20261001)
months = pd.date_range('2000-01-31', periods=318, freq='ME')  # 26.5 years of monthly returns
shocks = rng.standard_normal((318, 2))
first = pd.Series(0.010 + 0.04 * shocks[:, 0], index=months)
second = pd.Series(0.006 + 0.04 * (0.8 * shocks[:, 0] + 0.6 * shocks[:, 1]), index=months)

result = sharpe_difference_test(returns1=first, returns2=second)
assert result.n_obs == 318 and result.n_lags == int(np.floor(4.0 * (318 / 100.0) ** (2.0 / 9.0))) == 5
np.testing.assert_allclose([result.sr1_an, result.sr2_an, result.t_stat, result.p_value],
                           [0.9214, 0.4748, 3.7554, 0.00017], atol=5e-5)

# the test uses population-variance moments: equal to the realised Sharpe ratio with ddof=0
np.testing.assert_allclose(result.sr1_an, tf.compute_realized_sharpe(first.to_numpy(), af=12.0, ddof=0))
np.testing.assert_allclose(tf.compute_realized_sharpe(first, af=12.0, ddof=1),
                           result.sr1_an * np.sqrt(317.0 / 318.0))

# the delta-method standard error by hand, without HAC lags
x = np.column_stack([first, second])
mu, gamma = x.mean(axis=0), (x ** 2).mean(axis=0)
sigma = np.sqrt(gamma - mu ** 2)
gradient = np.array([gamma[0] / sigma[0] ** 3, -gamma[1] / sigma[1] ** 3,
                     -0.5 * mu[0] / sigma[0] ** 3, 0.5 * mu[1] / sigma[1] ** 3])
moments = np.column_stack([x - mu, x ** 2 - gamma])
psi = moments.T @ moments / 318.0
iid = sharpe_difference_test(returns1=first, returns2=second, n_lags=0)
np.testing.assert_allclose(iid.se_an, np.sqrt(12.0) * np.sqrt(gradient @ psi @ gradient / 318.0))

# two-sided normal p-value and invariance to rescaling both series
np.testing.assert_allclose(result.p_value, 2.0 * (1.0 - norm.cdf(abs(result.t_stat))))
np.testing.assert_allclose(sharpe_difference_test(returns1=2.0 * first, returns2=2.0 * second).t_stat,
                           result.t_stat)

# the standard error of one annualised Sharpe ratio is about 1 / sqrt(years)
np.testing.assert_allclose(np.sqrt((1.0 + 0.5 ** 2 / 24.0) / 26.5), 1.0 / np.sqrt(26.5), rtol=0.01)

# size under the null: equal Sharpe ratios, correlation 0.8, 500 replications
rejections = 0
for _ in range(500):
    e = rng.standard_normal((318, 2))
    a = pd.Series(0.01 + 0.04 * e[:, 0], index=months)
    b = pd.Series(0.01 + 0.04 * (0.8 * e[:, 0] + 0.6 * e[:, 1]), index=months)
    rejections += sharpe_difference_test(returns1=a, returns2=b).p_value < 0.05
assert 0.03 <= rejections / 500 <= 0.09
```

Two series with Sharpe ratios of 0.92 and 0.47 and a correlation of 0.8 differ significantly
over 26.5 years, with a standard error of the difference of 0.12: the correlation of the paired
series makes the difference far more precise than either ratio alone. Under the null the test
rejects at close to its nominal 5% rate.

## Implementation in trendfollowing

| Quantity | Formula | trendfollowing entry point |
|---|---|---|
| Realised Sharpe ratio | $\sqrt{\mathrm{af}}\bar f/s(f)$ | `trendfollowing.compute_realized_sharpe(returns, af=260.0, ddof=1)` |
| Sharpe difference test | Ledoit–Wolf HAC delta method, normal limit | `trendfollowing.analytics.sharpe_test.sharpe_difference_test(returns1, returns2, n_lags=None, af=12.0)` |
| Test result | annualised ratios, difference, standard error, statistic, p-value, sample size, lags | `trendfollowing.analytics.sharpe_test.SharpeDiffTest` |
| Regime-conditional performance | bear, normal and bull Sharpe ratios | `qis.compute_bnb_regimes_pa_perf_table` with `trendfollowing.backtests.regime_classifier` and `trendfollowing.backtests.PERF_PARAMS` |

The estimator lives in
[sharpe.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/analytics/sharpe.py)
and the test in
[sharpe_test.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/analytics/sharpe_test.py);
the paper's comparison runs in `papers/tf_systems/replication/sg_sharpe_test.py`.
API reference: {py:func}`trendfollowing.compute_realized_sharpe`,
{py:func}`trendfollowing.analytics.sharpe_test.sharpe_difference_test` and
{py:class}`trendfollowing.analytics.sharpe_test.SharpeDiffTest`.

Contract details:

- `sharpe_difference_test` requires two `pandas.Series`; it joins them on the intersection of
  their dates and drops missing values. It raises `ValueError` with fewer than 24 joint
  observations or a variance that is degenerate relative to the second moment.
- The reported `sr1_an` and `sr2_an` use population variances ($\hat\gamma-\hat\mu^2$), so they
  equal `compute_realized_sharpe(..., ddof=0)`.
- `af` only annualises the reported levels; the statistic and the p-value do not depend on it.

> **Pitfall.** Comparing a system backtested on futures excess returns with an index of funded
> programmes, such as the SG Trend Index, mixes excess and total returns; the interest income of
> the index favours it. Apply comparable fees and costs as well: the paper applies 2/20 fees to its
> systems before testing.

## Interpretation and limitations

- The test is asymptotic. With fewer than a few hundred observations and heavy tails, the
  studentised bootstrap of Ledoit and Wolf (2008) is more reliable than the normal limit.
- A test on one realised history says nothing about selection: choosing the best of many grid
  configurations and then testing it overstates its significance (Sullivan, Timmermann and White,
  1999).
- Failure to reject equality is not evidence of equality; report the confidence interval of the
  difference as well as the p-value.
- Daily Sharpe ratios of persistent trend signals are positively autocorrelated; the HAC estimator
  allows for it in the test, but the reported annualised levels are daily-moment ratios.

## See also

- [Notation and conventions](notation_and_conventions.md)
- [The closed-form Sharpe ratio](sharpe_ratio_closed_form.md)
- [The futures evidence of Sepp and Lucic (2026)](case_study_futures_evidence.md)
- [Predict Sharpe from autocorrelation and drift](predict_sharpe_from_acf.md)
- [Bibliography](bibliography.md)

## References

1. Ledoit, O., and Wolf, M. (2008). Robust Performance Hypothesis Testing with the Sharpe Ratio. *Journal of Empirical Finance*, 15(5), 850–859. [DOI: 10.1016/j.jempfin.2008.03.002](https://doi.org/10.1016/j.jempfin.2008.03.002). The HAC test for the difference of two Sharpe ratios.
2. Lo, A. W. (2002). The Statistics of Sharpe Ratios. *Financial Analysts Journal*, 58(4), 36–52. [DOI: 10.2469/faj.v58.n4.2453](https://doi.org/10.2469/faj.v58.n4.2453). The sampling error of the Sharpe ratio.
3. Newey, W. K., and West, K. D. (1987). A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix. *Econometrica*, 55(3), 703–708. [DOI: 10.2307/1913610](https://doi.org/10.2307/1913610). The Bartlett-kernel long-run covariance.
4. Sullivan, R., Timmermann, A., and White, H. (1999). Data-Snooping, Technical Trading Rule Performance, and the Bootstrap. *The Journal of Finance*, 54(5), 1647–1691. [DOI: 10.1111/0022-1082.00163](https://doi.org/10.1111/0022-1082.00163). Selection bias in trading-rule backtests.
5. Sepp, A., and Lucic, V. (2026). The Science and Practice of Trend-Following Systems. Working paper. [arXiv:2607.19497](https://arxiv.org/abs/2607.19497); [SSRN 3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787). Section 7.2 tests the three systems against the SG Trend Index.
6. Sepp, A., and Lucic, V. trendfollowing: Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python. [Software citation metadata](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).
7. Sepp, A. qis: Performance analytics, portfolio backtesting, risk analysis, and factsheet reporting in Python. [Software citation metadata](https://github.com/ArturSepp/QuantInvestStrats/blob/main/CITATION.cff).
