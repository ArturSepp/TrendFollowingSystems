---
myst:
  html_meta:
    description: >-
      The notation and calculation conventions of the trendfollowing handbook: reserved symbols,
      returns of continuous futures, volatility-normalised returns, spans, annualisation with
      260 trading days, the arithmetic Sharpe convention, timing and costs.
---

# Notation and conventions

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Implemented in [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

This chapter fixes the symbols and calculation conventions that every other chapter of the
handbook uses. A trend-following statistic is defined only once its return basis, volatility
normalisation, signal filter, moment basis, annualisation, timing and cost convention are known.
Each methodology chapter therefore opens its inputs section with a convention card of the same
eight rows, and this chapter defines what those rows mean. The notation follows Sepp and Lucic
(2026), with one deliberate change: the annualisation factor is written $\mathrm{af}$, as in the
[qis](https://quantinveststrats.readthedocs.io/) and
[optimalportfolios](https://optimalportfolios.readthedocs.io/) handbooks, where the paper writes $a$.

## Overview

The chapter settles four questions before any formula:

1. **What does a symbol mean?** A reserved set of symbols has one meaning in the whole book. A
   chapter may introduce further symbols, and declares them in its own notation table.
2. **Which return is traded?** The systems trade continuous futures, whose relative returns are
   excess returns, and all closed forms are statements about volatility-normalised returns.
3. **How are daily quantities annualised, and which Sharpe ratio is reported?** Daily moments are
   annualised with 260 trading days, and every Sharpe ratio is the arithmetic ratio of daily
   moments.
4. **When is information available, and what do costs act on?** A weight decided at the close of
   day $t$ earns the return of day $t+1$; costs are charged on the change of the weight.

Prose uses British spelling (normalised, annualised). Python names keep the American spelling in
which they were published, for example `annualization_factor` and `compute_realized_sharpe`.

## Inputs, notation, and assumptions

| Convention | This article |
|---|---|
| Return basis | Simple daily returns of continuous futures, which are excess returns; defined here |
| Normalisation | $z_t=r_t/\sigma_{t-1}$ with an EWMA volatility of span 33 days, defined here |
| Signal filter | Spans $N$ in observations with $\nu=1-2/(N+1)$; LS($N_1$,$N_2$) denotes a long-short filter |
| Moment basis | Population moments for the closed forms; sample moments state their degrees-of-freedom convention |
| Annualisation | $\mathrm{af}=260$ trading days: $\mathrm{af}$ for means, $\sqrt{\mathrm{af}}$ for volatilities and Sharpe ratios |
| Timing | A weight decided at the close of day $t$ earns the return of day $t+1$ |
| Costs | Gross unless stated; analytic costs per unit of volatility-normalised turnover, backtest costs per unit of notional turnover |
| trendfollowing default | `AF_DAILY = 260.0`; `compute_realized_sharpe(af=260.0, ddof=1)` |

The table defines each convention-card row:

| Row | What it states |
|---|---|
| Return basis | Simple or log returns, of which instrument, and whether they are excess returns |
| Normalisation | How returns are divided by a volatility estimate before the signal is formed |
| Signal filter | The filter, its spans and loadings, or the signal construction of a non-EWMA system |
| Moment basis | Population moments under a stated process, or sample moments with their estimator |
| Annualisation | The factor $\mathrm{af}$ and how it is applied |
| Timing | Which information a quantity dated $t$ may use, and when a weight is applied |
| Costs | Gross or net, and the turnover measure a cost rate multiplies |
| trendfollowing default | The default arguments of the principal entry points |

### Reserved symbols

These symbols have one meaning in every chapter. Hats denote sample estimators and a bar denotes
a sample mean.

| Symbol | Meaning |
|---|---|
| $t$, $T$ | Observation date (a trading day); number of observations in a sample, or an aggregation horizon in days |
| $m$, $h$ | Lag of an autocorrelation; lag between two strategy returns |
| $s_t$ | Price of a continuous futures contract |
| $r_t$ | Simple daily return $s_t/s_{t-1}-1$, an excess return |
| $\sigma_t$ | Daily, non-annualised volatility estimate of $r_t$, using returns up to $t$ |
| $z_t$ | Volatility-normalised return $r_t/\sigma_{t-1}$ |
| $\mu$, $\vartheta$ | Population mean and variance of $z_t$, per day |
| $\mu_{\mathrm{an}}$ | Annualised drift $\sqrt{\mathrm{af}}\mu$: the Sharpe ratio of $z_t$ at unit variance |
| $\rho(m)$, $\hat\rho_T(m)$ | Population and sample autocorrelation of $z_t$ at lag $m$, with $\rho(0)=1$ |
| $\mathrm{af}$ | Annualisation factor, 260 trading days per year |
| $N$, $N_1$, $N_2$ | Span of a filter; long and short span of a long-short filter, in observations |
| $\nu$, $\nu_1$, $\nu_2$ | Smoothing parameter $1-2/(N+1)$ of the corresponding span |
| $\mathcal{L}^{(\nu)}$ | EWMA filter with smoothing parameter $\nu$ |
| $l$, $l_1$, $l_2$, $q$ | Filter loadings and the long-short normalisation constant |
| $S_t$ | Trend signal at the close of day $t$ |
| $\sigma_{\mathrm{target}}$ | Annualised volatility target |
| $w_t$ | Position weight: exposure per unit of capital, decided at the close of day $t$ |
| $f_t$, $F_T$ | Daily strategy return $w_{t-1}r_t$; its sum over $T$ days |
| $\Phi_\nu$, $\Psi_\nu$ | Autocorrelation generating function $\sum_{m\ge 0}\nu^m\rho(m)$ and $\Psi_\nu=\Phi_\nu-1$ |
| $A_\nu$, $B_\nu$, $K_\nu$ | Autocorrelation loadings and kurtosis loading of the Sharpe ratio |
| $\psi_s$, $\epsilon_t$, $\kappa$ | Moving-average weights, innovations and their excess kurtosis |
| $\phi$, $d$ | AR(1) coefficient; fractional order of an ARFIMA process |
| $U_t$, $c$ | Volatility-normalised turnover; cost per unit of it |
| $\mathrm{SR}$, $\mathrm{SR}^{\mathrm{net}}$ | Annualised gross and net Sharpe ratio |
| $\varsigma(T)$ | Skewness of the strategy return aggregated over $T$ days |
| $\mathbb{E}$, $\operatorname{Var}$, $\operatorname{Cov}$ | Expectation, variance and covariance under the statistical measure |

$\mathrm{af}$ is set upright and read as one symbol; it is never the product of $a$ and $f$. It is
written as the code writes it: the `af` argument of the Sharpe functions, which the expected-return
and system functions call `annualization_factor`. A chapter that needs a symbol outside this table
declares it locally and does not reuse a reserved one.

## Methodology

### Returns of continuous futures

**Definition.** For a continuous futures price $s_t$, stitched across rolls so that its relative
returns carry no roll jumps, the price change and the simple return of day $t$ are

$$
d_t=s_t-s_{t-1},
\qquad
r_t=\frac{s_t}{s_{t-1}}-1 .
$$

Futures margins are small and funding is embedded in the futures price by arbitrage, so $r_t$ is
an excess return: no cash rate is subtracted anywhere in the handbook. A contract quoted in a
currency X is converted to USD by scaling the local return with the exchange-rate ratio,
$r_t=(s_t^{\ast}/s_{t-1}^{\ast}-1)(x_t/x_{t-1})$, where $s_t^{\ast}$ is the local price and
$x_t$ the USD value of one unit of X (Sepp and Lucic, 2026, Section 2).

The packaged dataset stores prices built from these returns, and each consumer states its return
basis when it converts prices back: the closed forms and the American and TSMOM runners use simple
returns, while the European runner uses log returns $\log(1+r_t)$ both for its signal and for its
P&L. The [European system chapter](european_system.md) quantifies the difference.

### Volatility-normalised returns

**Definition.** With $\sigma_t$ an estimate of the daily volatility of $r_t$ that uses returns up
to day $t$, the volatility-normalised return is

$$
z_t=\frac{r_t}{\sigma_{t-1}} .
$$

The lag makes $z_t$ point in time: the return of day $t$ never scales itself. All closed forms of
the handbook are statements about $z_t$ under the population moments

$$
\mathbb{E}[z_t]=\mu,
\qquad
\operatorname{Var}[z_t]=\vartheta,
\qquad
\rho(m)=\frac{\mathbb{E}[(z_t-\mu)(z_{t-m}-\mu)]}{\vartheta},
$$

which is the population assumption of Section 4.5 of Sepp and Lucic (2026). Because $z_t$ is a normalised return, the
closed forms set $\vartheta=1$, and the annualised drift $\mu_{\mathrm{an}}=\sqrt{\mathrm{af}}\mu$ is
the Sharpe ratio of the instrument at unit variance. The argument `sr_underlying` of the Sharpe and
expected-return functions is $\mu_{\mathrm{an}}$. The
[volatility normalisation chapter](volatility_normalisation.md) defines the estimator.

### Spans and smoothing parameters

**Definition.** A filter span $N$, measured in observations, maps to the smoothing parameter

$$
\nu=1-\frac{2}{N+1},
\qquad
N=\frac{1+\nu}{1-\nu},
$$

computed by `span_to_nu`. The handbook labels spans as in the paper: one week is 5 days, two weeks
10, one month 21, three months 63, six months 125, one year 250 and two years 500. LS($N_1$,$N_2$)
is the long-short filter with long span $N_1$ and short span $N_2\lt N_1$; LS(250,20) is the
filter of the paper's empirical section.

### Annualisation and the Sharpe convention

**Definition.** For a strategy with daily returns $f_t$, the annualised Sharpe ratio is

$$
\mathrm{SR}=\sqrt{\mathrm{af}}\frac{\mathbb{E}[f_t]}{\sqrt{\operatorname{Var}[f_t]}},
\qquad
\mathrm{af}=260 ,
$$

which is equation (5.1) of Sepp and Lucic (2026). Its sample counterpart, computed by
`compute_realized_sharpe`, replaces the moments by the sample mean and the sample standard
deviation with `ddof=1` by default; `ddof=0` reproduces the paper's attribution exhibits.

Three choices are fixed here and used everywhere:

- **260, not 252.** The paper counts weekdays, so `AF_DAILY = 260.0`. qis infers 252 from the
  calendar density of a business-day panel; the papers pass the constant explicitly. The two
  conventions differ by a factor $\sqrt{260/252}\approx 1.0157$ in every annualised volatility
  and Sharpe ratio.
- **Arithmetic, not geometric.** The ratio uses arithmetic means of simple excess returns. It is
  the convention under which the regime contributions of qis add up to the total Sharpe ratio
  exactly (`qis.perfstats.config.SharpeConvention.ARITHMETIC`).
- **Daily moments, not horizon moments.** The ratio annualises daily moments. When $f_t$ is
  serially correlated the horizon-based ratio of Lo (2002), defined on the variance of aggregated
  returns, differs; under zero-drift white noise the two coincide, because the strategy returns
  are then serially uncorrelated (see the [skewness chapter](aggregated_skewness.md)).

Quarterly and monthly statistics annualise with `PPY_QUARTERLY = 4.0` and `PPY_MONTHLY = 12.0`.

### Timing

**Definition.** The weight $w_t$ is computed at the close of day $t$ from information up to and
including day $t$, and it is held over day $t+1$:

$$
f_{t+1}=w_t r_{t+1}.
$$

The European signal $S_t$ uses $z_t$, which uses $\sigma_{t-1}$; the position size uses $\sigma_t$.
Both are known at the close of day $t$. A cost is charged on the day the weight changes. The
backtest runners initialise their volatility and covariance recursions from full-sample moments,
an in-sample choice whose influence the 250-day warmup attenuates but does not remove; the
[European system chapter](european_system.md) states the details.

### Population and sample moments

The closed forms of Parts I and II are population statements: exact under the stated process and
filter, with no estimation error. A sample counterpart replaces $\rho(m)$, $\mu$ and $\vartheta$
by estimates from one history, and the result is then an in-sample description of that history,
not a forecast. The sample autocorrelation used by the sample-path identity of the
[P&L decomposition](pnl_decomposition.md) is a specific lag product that need not lie in
$[-1,1]$; the [attribution guide](predict_sharpe_from_acf.md) uses lag-wise pandas
correlations. Each chapter states which estimator it uses.

### Gross, net and the two cost conventions

The gross Sharpe ratio excludes trading costs. Costs enter in two units:

- the closed forms charge $c$ per unit of the **volatility-normalised turnover**
  $U_t=\sqrt{\mathrm{af}}\sigma_t\lvert w_t-w_{t-1}\rvert$, which is comparable across contracts
  of different volatility;
- the backtest runners charge a one-way **volume cost** per unit of notional turnover
  $\lvert w_t-w_{t-1}\rvert$, following Exhibit B1 of Hurst, Ooi and Pedersen (2017).

A volume cost $k$ on a contract of annualised volatility $\sqrt{\mathrm{af}}\sigma_t$ equals
$c=k/(\sqrt{\mathrm{af}}\sigma_t)$ per unit of $U_t$; the
[turnover chapter](turnover_and_net_sharpe.md) uses this conversion.

> **Pitfall.** A Sharpe ratio, a turnover or a cost quoted without its convention cannot be
> compared with another. Annualising the same daily Sharpe ratio with 252 instead of 260 changes
> it by 1.6%, and a 6bp volume cost on a contract with 16% volatility is a 37.5bp cost per unit of
> volatility-normalised turnover.

## Worked example

The block below checks the conventions on a fixed synthetic NAV: the constants, the annualised
volatility under the paper convention, the realised Sharpe ratio against its definition, the
252/260 conversion and the span map.

```python
import numpy as np
import pandas as pd
import trendfollowing as tf

# the annualisation constants of the papers
assert tf.AF_DAILY == 260.0 and tf.PPY_QUARTERLY == 4.0 and tf.PPY_MONTHLY == 12.0

# a synthetic NAV built from simple daily returns
rng = np.random.default_rng(20261001)
dates = pd.bdate_range('2016-01-01', periods=2600)
returns = pd.Series(0.0004 + 0.01 * rng.standard_normal(2600), index=dates, name='strategy')
nav = (1.0 + returns).cumprod()

# annualised volatility of daily simple returns with af = 260
vol = tf.compute_daily_annualised_vol(nav)
np.testing.assert_allclose(vol, np.sqrt(260.0) * nav.pct_change().std(ddof=1))

# the realised Sharpe ratio is sqrt(af) * mean / std of the periodic simple returns
daily = nav.pct_change().dropna()
np.testing.assert_allclose(daily.to_numpy(), returns.iloc[1:].to_numpy(), atol=1e-12)
sharpe = tf.compute_realized_sharpe(returns=daily, af=tf.AF_DAILY)
np.testing.assert_allclose(sharpe, np.sqrt(260.0) * daily.mean() / daily.std(ddof=1))
population = tf.compute_realized_sharpe(returns=daily.to_numpy(), af=tf.AF_DAILY, ddof=0)
np.testing.assert_allclose(population, np.sqrt(260.0) * daily.mean() / daily.std(ddof=0))
assert population > sharpe  # the ddof=0 denominator is smaller

# a qis-style 252-day annualisation reports a Sharpe ratio 1.6% lower
np.testing.assert_allclose(np.sqrt(260.0 / 252.0), 1.0157, atol=5e-5)

# spans and smoothing parameters
assert tf.span_to_nu(63) == 1.0 - 2.0 / 64.0
nu = tf.span_to_nu(250)
np.testing.assert_allclose((1.0 + nu) / (1.0 - nu), 250.0)

# a 6bp volume cost on a 16%-volatility contract, per unit of volatility-normalised turnover
np.testing.assert_allclose(0.0006 / 0.16, 0.00375)
```

## Implementation in trendfollowing

| Quantity | Formula | trendfollowing entry point |
|---|---|---|
| Annualisation factor | $\mathrm{af}=260$ | `trendfollowing.AF_DAILY` |
| Quarterly and monthly factors | 4 and 12 | `trendfollowing.PPY_QUARTERLY`, `trendfollowing.PPY_MONTHLY` |
| Daily annualised volatility | $\sqrt{\mathrm{af}}$ times the sample standard deviation of daily simple returns | `trendfollowing.compute_daily_annualised_vol(navs)` |
| Realised Sharpe ratio | $\sqrt{\mathrm{af}}$ mean over standard deviation | `trendfollowing.compute_realized_sharpe(returns, af=260.0, ddof=1)` |
| Smoothing parameter | $\nu=1-2/(N+1)$ | `trendfollowing.span_to_nu(span)` |

The conventions live in
[conventions.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/conventions.py),
the single source the papers share. `compute_realized_sharpe` accepts a NumPy array, a Series or a
DataFrame and returns a float or a Series; it equals the arithmetic Sharpe estimator of qis on the
same inputs, which `tests/test_sharpe_shared.py` guards when the installed qis provides it.
API reference: {py:func}`trendfollowing.compute_daily_annualised_vol`,
{py:func}`trendfollowing.compute_realized_sharpe` and {py:func}`trendfollowing.span_to_nu`.

## Interpretation and limitations

- The conventions are those of Sepp and Lucic (2026). A statistic computed by another tool under
  252-day annualisation, log returns or a geometric Sharpe ratio is not comparable without
  conversion.
- The daily-moment Sharpe ratio overstates the horizon-based ratio when strategy returns are
  positively autocorrelated, which persistent signals produce; it is the convention of industry
  reporting for liquid managed futures, not the only defensible one.
- Population closed forms carry no estimation error, while every sample counterpart does; the
  [Sharpe inference chapter](sharpe_inference.md) states the uncertainty of realised ratios.
- Excess returns of futures are not total returns of funded programmes: an index of funded CTA
  programmes includes interest income that the futures returns exclude.

## See also

- [EWMA filters and variance-preserving signals](ewma_filters.md)
- [Volatility normalisation and position sizing](volatility_normalisation.md)
- [Realised Sharpe ratios and their comparison](sharpe_inference.md)
- [Turnover, trading costs and the net Sharpe ratio](turnover_and_net_sharpe.md)
- [Bibliography](bibliography.md)

## References

1. Sepp, A., and Lucic, V. (2026). The Science and Practice of Trend-Following Systems. Working paper. [arXiv:2607.19497](https://arxiv.org/abs/2607.19497); [SSRN 3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787). Sections 2, 4 and 5 fix the return, normalisation and Sharpe conventions.
2. Lo, A. W. (2002). The Statistics of Sharpe Ratios. *Financial Analysts Journal*, 58(4), 36–52. [DOI: 10.2469/faj.v58.n4.2453](https://doi.org/10.2469/faj.v58.n4.2453). The horizon-based Sharpe ratio under serial correlation.
3. Hurst, B., Ooi, Y. H., and Pedersen, L. H. (2017). A Century of Evidence on Trend-Following Investing. *The Journal of Portfolio Management*, 44(1), 15–29. [DOI: 10.3905/jpm.2017.44.1.015](https://doi.org/10.3905/jpm.2017.44.1.015). The volume-based cost schedule.
4. Sepp, A., and Lucic, V. trendfollowing: Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python. [Software citation metadata](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).
5. Sepp, A. qis: Performance analytics, portfolio backtesting, risk analysis, and factsheet reporting in Python. [Software citation metadata](https://github.com/ArturSepp/QuantInvestStrats/blob/main/CITATION.cff).
