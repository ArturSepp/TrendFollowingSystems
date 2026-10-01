---
myst:
  html_meta:
    description: >-
      The European trend-following system as implemented in trendfollowing: continuous weights
      from a variance-preserving EWMA filter of volatility-normalised returns, signal and weight
      caps, optional portfolio volatility targeting, warmup, the P&L, turnover and cost
      accounting of BacktestOutputs, and the paper's LS(250,20) configuration.
---

# The European system

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Implemented in [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

The European trend-following system holds, in each contract, a continuous position proportional
to a filtered trend signal and inversely proportional to the contract's volatility. It is the
system of large European CTA managers (Dao et al., 2017; Baz et al., 2015) and the one behind
every closed form of this handbook. This chapter defines the system, documents its implementation
in `run_european_tf_system` step by step, and states the accounting of P&L, turnover and costs
that the runner returns.

## Overview

The system has three steps (Sepp and Lucic, 2026, Section 4):

1. **Normalise**: divide each daily return by the volatility estimated the day before.
2. **Filter**: apply a variance-preserving single or long-short EWMA filter to the normalised
   returns to obtain the signal $S_t$.
3. **Size**: hold $w_t=S_tw_t^{\mathrm{vt}}$, the signal times the volatility-target weight.

The position size changes every day with the signal, so the number of contracts fluctuates
continuously, up to the discreteness of contract sizes. The implementation adds caps on the
signal and the weight, an optional portfolio-level volatility target, a warmup, and a volume-based
cost model.

## Inputs, notation, and assumptions

| Convention | This article |
|---|---|
| Return basis | Log returns $\log(s_t/s_{t-1})$ of each price column, used for the signal and for the P&L |
| Normalisation | EWMA volatility of span `vol_span`, lagged one day, seeded with the full-sample variance |
| Signal filter | Variance-preserving single filter or LS(`long_span`,`short_span`), capped at `signal_cap` |
| Moment basis | Sample paths of the supplied prices |
| Annualisation | `annualization_factor=260` for the volatility target and the portfolio covariance |
| Timing | $w_t$ uses data up to $t$ and earns the return of day $t+1$; costs on the day of the change |
| Costs | One-way volume cost `volume_costs` per unit of notional turnover $\lvert w_t-w_{t-1}\rvert$ |
| trendfollowing default | `run_european_tf_system(prices, long_span=31, short_span=None, vol_span=33, vol_target=0.3, portfolio_covar_span=None, portfolio_target_vol=0.15, volume_costs=0.002, warmup_period=250, signal_cap=3.0, weight_cap=5.0)` |

| Symbol or input | Meaning | Units and convention |
|---|---|---|
| $\ell_{i,t}$ | Log return of instrument $i$ | Per day |
| $\Sigma_t$ | EWMA covariance of the log returns with span `portfolio_covar_span` | Per day |
| $\sigma_P$ | Portfolio volatility target `portfolio_target_vol` | Per annum |
| $\lambda_t$ | Portfolio leverage factor | Dimensionless |
| $k_{i,t}$ | Volume cost | Decimal per unit of notional turnover |
| $\bar S$, $\bar w$ | Signal cap and weight cap | Dimensionless |

## Methodology

### Definition

**Definition (European system; Sepp and Lucic, 2026, Section 4).** For each instrument,

$$
z_t=\frac{r_t}{\sigma_{t-1}},
\qquad
S_t=\tilde{\mathcal{L}}^{(\nu)}(z_t)\ \text{or}\ \widetilde{\mathcal{LS}}^{(\nu_1,\nu_2)}(z_t),
\qquad
w_t=S_t\frac{\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}\sigma_t} .
$$

By the [system-return identity](volatility_normalisation.md) the daily return is
$f_t=w_{t-1}r_t=(\sigma_{\mathrm{target}}/\sqrt{\mathrm{af}})S_{t-1}z_t$, a product of a filter of past
normalised returns and the current one: the object of the [P&L decomposition](pnl_decomposition.md)
and of the [closed-form Sharpe ratio](sharpe_ratio_closed_form.md). The meta-parameters are the
span $N$ of a single filter or the pair $(N_1,N_2)$ of a long-short filter.

![Panels A1 and A2: time series and histograms of the fast, medium and slow long-short filters on S&P 500 futures, all with standard deviation close to one; panels B1 and B2: the weights at a 15% volatility target, positive on average; panels C1 and C2: cumulative P&L and daily returns, with realised volatility near the target](../papers/tf_systems/paper/figures/ES1_short_signals.PNG)

Figure 4.1 of Sepp and Lucic (2026) runs the system on S&P 500 futures with long spans of 30, 125
and 250 days and a short span of 20 days. The three signals have standard deviations close to
one (A), the weights are positive on average because of the index's drift and become extreme when
realised volatility is low (B), and the realised volatility of the P&L averages 18% against the
15% target (C). The figure is produced by `papers/tf_systems/replication/illustrate_systems.py`.

### The implementation, step by step

`run_european_tf_system(prices, ...)` performs, for a price panel with one column per instrument:

1. **Returns.** $\ell_t=\log(s_t/s_{t-1})$ through `qis.to_returns(prices, is_log_returns=True)`;
   the first row is missing.
2. **Normalisation.** $z_t=\ell_t/\sigma_{t-1}$ with the lagged EWMA volatility of span
   `vol_span`, seeded with the full-sample variance (`compute_vol_norm_returns`). The first two
   rows of $z$ are missing: the first return, and the first lagged volatility.
3. **Signal.** The variance-preserving filter of $z$ through `qis.compute_ewm_long_short`, started
   at zero, and clipped to $[-\bar S,\bar S]$ when `signal_cap` is set (`compute_tf_signal`).
4. **Weight.** $w_t=S_t\sigma_{\mathrm{target}}/(\sqrt{\mathrm{af}}\sigma_t)$ with the unlagged
   volatility, clipped to $[-\bar w,\bar w]$ when `weight_cap` is set
   (`compute_tf_signal_weight`).
5. **Portfolio volatility target.** When `portfolio_covar_span` is set, every weight is multiplied
   by $\lambda_t=\sigma_P/\sqrt{\mathrm{af}w_t^{\top}\Sigma_tw_t}$, where $\Sigma_t$ is the EWMA
   covariance of the returns up to $t$ seeded with the full-sample covariance
   (`qis.compute_portfolio_var_np`); days with a non-positive portfolio variance get zero leverage.
6. **Warmup.** The first `warmup_period` finite weights of each column are set to missing. With the
   default 250, the first weight falls on row 252 of the panel.
7. **P&L and costs.** `compute_pnl` forms, per instrument, the gross and net daily contributions
   and aggregates them.

### P&L, turnover and cost accounting

**Definition (accounting of `compute_pnl`).** For instrument $i$ on day $t$,

$$
\pi_{i,t}=w_{i,t-1}\ell_{i,t},
\qquad
\pi_{i,t}^{\mathrm{net}}=\pi_{i,t}-k_{i,t}\lvert w_{i,t}-w_{i,t-1}\rvert,
$$

and the portfolio NAV compounds the sum of the contributions, ignoring missing values:

$$
V_t=\prod_{u\le t}\left(1+\sum_i\pi_{i,u}\right).
$$

The turnover fields are the notional turnover $\sum_i\lvert w_{i,t}-w_{i,t-1}\rvert$, the
volatility-normalised turnover $\sum_i\sqrt{\mathrm{af}}\sigma_{i,t}\lvert w_{i,t}-w_{i,t-1}\rvert$,
which is the sum of the $U_t$ of the [turnover chapter](turnover_and_net_sharpe.md), and the cost
$\sum_ik_{i,t}\lvert w_{i,t}-w_{i,t-1}\rvert$.

| Field of `BacktestOutputs` | Meaning and units |
|---|---|
| `weights` | $w_{i,t}$: exposure per unit of capital; not long-only weights, need not sum to one |
| `signals` | $S_{i,t}$ after the cap |
| `instrument_pnl`, `instrument_pnl_net` | $\pi_{i,t}$ and $\pi_{i,t}^{\mathrm{net}}$: daily return contributions |
| `portfolio_pnl`, `portfolio_pnl_net` | Compounded gross and net NAVs, despite the `pnl` names |
| `portfolio_turnover` | Daily notional turnover |
| `portfolio_vol_turnover` | Daily volatility-normalised turnover |
| `portfolio_cost` | Daily cost as a fractional return drag |

> **Pitfall.** The European runner applies its weights to **log** returns, while the American and
> TSMOM runners apply theirs to simple returns. Since $\ell_t\approx r_t-r_t^2/2$, a weight $w$ earns
> about $-w\sigma^2/2$ a day less on log returns: long positions are penalised and short positions
> favoured, by about $1.3\%$ a year per unit of weight at a 16% volatility. Compare systems on a
> common return basis.

### The paper's configuration

The empirical section of Sepp and Lucic (2026, Section 7) runs LS(250,20) with a 33-day volatility
span on the packaged 84-contract universe, with volume-based costs and no portfolio risk limits;
its realised costs are 1.7% a year, in line with a typical CTA. The maintained example
[`examples/backtest_european_system.py`](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/examples/backtest_european_system.py)
adds a 63-day portfolio volatility target of 15% and reports a Sharpe ratio of 1.10 at a realised
volatility of 15.2%, net of costs and gross of fees, over 1960–2026.

## Worked example

The block runs the system on a synthetic four-contract panel whose log returns follow an AR(1)
with $\phi=0.1$ at different volatilities. It checks the warmup, the P&L and NAV accounting, the
signal variance and the realised Sharpe ratio against the closed forms, the turnover proxy, the cost
accounting and the portfolio volatility target.

```python
import numpy as np
import pandas as pd
from scipy.signal import lfilter
import trendfollowing as tf
from trendfollowing.systems.european import run_european_tf_system

# 25 years of four contracts with AR(1) log returns, phi = 0.1, at different volatilities
rng = np.random.default_rng(20261001)
n_days, phi = 260 * 25, 0.1
daily_vols = np.array([0.010, 0.005, 0.015, 0.020])
x = lfilter([1.0], [1.0, -phi], rng.standard_normal((n_days, 4)), axis=0) * np.sqrt(1.0 - phi ** 2)
dates = pd.bdate_range('1990-01-01', periods=n_days)
prices = pd.DataFrame(100.0 * np.exp(np.cumsum(x * daily_vols, axis=0)), index=dates,
                      columns=['A', 'B', 'C', 'D'])

# gross, uncapped, single 21-day filter
gross = run_european_tf_system(prices=prices, long_span=21, short_span=None, vol_span=33,
                               vol_target=0.15, volume_costs=0.0, warmup_period=250,
                               signal_cap=None, weight_cap=None)
weights = gross.weights
assert weights.iloc[:252].isna().all().all() and weights.iloc[252:].notna().all().all()

# P&L accounting: weight of the previous day times the log return; NAV compounds the sum
log_returns = np.log(prices).diff()
np.testing.assert_allclose(gross.instrument_pnl.iloc[253:], (weights.shift(1) * log_returns).iloc[253:],
                           atol=1e-14)
nav = (1.0 + gross.instrument_pnl.fillna(0.0).sum(axis=1)).cumprod()
np.testing.assert_allclose(gross.portfolio_pnl, nav, rtol=1e-12)

# the signal standard deviation is sqrt(1 + 2 Psi) = 1.095 under AR(1), not one
moments = tf.compute_signal_moments(rho=tf.population_acf(n_lags=1000, phi=phi), long_span=21)
np.testing.assert_allclose(np.sqrt(moments.s_var), 1.0954, atol=5e-5)
np.testing.assert_allclose(gross.signals.iloc[252:].std(), np.sqrt(moments.s_var), atol=0.03)

# realised Sharpe ratios against the closed form, within two standard errors of the mean
sharpe = tf.compute_realized_sharpe(gross.instrument_pnl.iloc[253:], af=260.0)
closed_form = tf.sharpe_ar1(phi=phi, long_span=21)
standard_error = np.sqrt((1.0 + closed_form ** 2 / 2.0) / 25.0) / np.sqrt(4.0)
np.testing.assert_allclose(sharpe, [0.6612, 0.5586, 0.5410, 0.4045], atol=5e-4)
assert abs(sharpe.mean() - closed_form) < 2.0 * standard_error

# volatility-normalised turnover per contract against the closed-form proxy
annual_vol_turnover = 260.0 * gross.portfolio_vol_turnover.iloc[253:].mean() / 4.0
np.testing.assert_allclose(annual_vol_turnover, tf.expected_turnover(long_span=21, vol_target=0.15),
                           rtol=0.01)

# 2bp volume costs, default caps and a 15% portfolio volatility target on a 63-day covariance
net = run_european_tf_system(prices=prices, long_span=21, short_span=None, vol_span=33,
                             vol_target=0.15, volume_costs=0.0002, warmup_period=250,
                             signal_cap=3.0, weight_cap=5.0, portfolio_covar_span=63,
                             portfolio_target_vol=0.15)
traded = net.weights.diff().abs()
np.testing.assert_allclose((net.instrument_pnl - net.instrument_pnl_net).iloc[253:],
                           0.0002 * traded.iloc[253:], atol=1e-14)
assert net.signals.abs().max().max() <= 3.0
realised_vol = net.portfolio_pnl.pct_change().iloc[260:].std() * np.sqrt(260.0)
np.testing.assert_allclose(realised_vol, 0.15, atol=0.01)
np.testing.assert_allclose(260.0 * net.portfolio_turnover.iloc[253:].mean(), 165.28, atol=0.01)
np.testing.assert_allclose(260.0 * net.portfolio_cost.iloc[253:].mean(), 0.0331, atol=5e-5)
```

The signals have standard deviations near 1.10, as the AR(1) closed form predicts. The four
realised Sharpe ratios average 0.54 against a closed-form 0.67: the gap is within two standard
errors of 25-year samples and includes the attenuation by the estimated volatility. The
volatility-normalised turnover per contract matches the proxy of 13.3 within 1%. With a 21-day
filter the notional turnover is 165 times capital a year, dominated by the 8%-volatility
contract B, so a volume cost of only 2bp costs 3.3% a year.

## Implementation in trendfollowing

| Quantity | Formula | trendfollowing entry point |
|---|---|---|
| Signal | $S_t$ of $z_t$, single or long-short | `trendfollowing.systems.european.compute_tf_signal(returns, vol_norm_returns=None, long_span=33, short_span=None, vol_span=33)` |
| Signal and weight | $w_t=S_t\sigma_{\mathrm{target}}/(\sqrt{\mathrm{af}}\sigma_t)$, optional signal cap | `trendfollowing.systems.european.compute_tf_signal_weight(returns, long_span, short_span, vol_span, vol_target, annualization_factor, signal_cap)` |
| Instrument P&L of a weight path | $w_{t-1}r_t$ on NumPy arrays | `trendfollowing.systems.european.compute_tf_strat_pnl(returns, long_span, short_span, vol_span, vol_target, annualization_factor)` |
| Full backtest | steps 1 to 7 above | `trendfollowing.systems.european.run_european_tf_system(prices, ...)` |
| Accounting | gross and net P&L, turnover, costs | `trendfollowing.systems.backtest_utils.compute_pnl(weights, returns, volume_costs, vols)` |
| Result container | fields above | `trendfollowing.systems.backtest_utils.BacktestOutputs` |
| Path statistics | total and annual P&L, volatility, Sharpe of arithmetic paths | `trendfollowing.systems.backtest_utils.compute_path_stats(pnl_paths, annualization_factor=260.0)` |

The system lives in
[european.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/systems/european.py)
and the accounting in
[backtest_utils.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/systems/backtest_utils.py);
the filter, covariance and return conversions are delegated to
[qis](https://github.com/ArturSepp/QuantInvestStrats). Performance reporting of the resulting NAVs
belongs to qis as well, for example `qis.compute_ra_perf_table` or
`qis.generate_multi_asset_factsheet`.
API reference: {py:func}`trendfollowing.systems.european.run_european_tf_system`,
{py:func}`trendfollowing.systems.european.compute_tf_signal_weight`,
{py:func}`trendfollowing.systems.backtest_utils.compute_pnl` and
{py:class}`trendfollowing.systems.backtest_utils.BacktestOutputs`.

Contract details:

- `prices` is a `DataFrame` of price levels with a `DatetimeIndex`, one column per instrument;
  ragged starts are kept, and each column's warmup counts from its own first finite weight.
- `volume_costs` is a float or a `DataFrame` aligned with `prices`; any other type raises
  `NotImplementedError`.
- The function defaults differ between layers: `vol_target=0.3` in the runner,
  `0.15` in `compute_tf_strat_pnl` and `0.30` in `compute_tf_signal_weight`; spans default to 31
  or 33 days. Pass every parameter explicitly when comparing runs.
- The volatility and covariance recursions are seeded with full-sample moments, an in-sample
  initialisation that the warmup attenuates but does not remove; see the
  [system comparison guide](system_comparison_and_backtest.md).

## Interpretation and limitations

- The runner is a research backtest: positions are fractional, executed at the close, with
  proportional costs and no market impact, margin or financing.
- Caps change the system the closed forms describe. With `signal_cap=3.0` about 0.3% to 0.5% of
  signal days are capped in the example, a small effect; a tight cap makes the signal nonlinear.
- Portfolio volatility targeting stabilises realised risk but introduces a common leverage factor
  across instruments that the per-instrument closed forms do not model.
- Per-instrument volatility targets such as the paper's `vol_target=0.0035` scale with the number
  of instruments; choose them for a target portfolio volatility, not as a per-contract risk.

## See also

- [Volatility normalisation and position sizing](volatility_normalisation.md)
- [EWMA filters and variance-preserving signals](ewma_filters.md)
- [The American system](american_system.md)
- [Time-series momentum](tsmom_system.md)
- [Compare and backtest the three systems](system_comparison_and_backtest.md)
- [Bibliography](bibliography.md)

## References

1. Sepp, A., and Lucic, V. (2026). The Science and Practice of Trend-Following Systems. Working paper. [arXiv:2607.19497](https://arxiv.org/abs/2607.19497); [SSRN 3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787). Sections 3, 4 and 7 define the European system and apply it to futures.
2. Dao, T.-L., Nguyen, T.-T., Deremble, C., Lempérière, Y., Bouchaud, J.-P., and Potters, M. (2017). Tail Protection for Long Investors: Convexity at Work. *Journal of Investment Strategies*, 7(1), 61–84. The volatility-normalised European trend system.
3. Baz, J., Granger, N., Harvey, C. R., Le Roux, N., and Rattray, S. (2015). Dissecting Investment Strategies in the Cross Section and Time Series. Working paper, SSRN. A continuous trend signal from moving averages of normalised returns.
4. Hurst, B., Ooi, Y. H., and Pedersen, L. H. (2017). A Century of Evidence on Trend-Following Investing. *The Journal of Portfolio Management*, 44(1), 15–29. [DOI: 10.3905/jpm.2017.44.1.015](https://doi.org/10.3905/jpm.2017.44.1.015). The volume-based cost schedule.
5. Sepp, A., and Lucic, V. trendfollowing: Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python. [Software citation metadata](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).
6. Sepp, A. qis: Performance analytics, portfolio backtesting, risk analysis, and factsheet reporting in Python. [Software citation metadata](https://github.com/ArturSepp/QuantInvestStrats/blob/main/CITATION.cff).
