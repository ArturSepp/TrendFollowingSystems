---
myst:
  html_meta:
    description: >-
      The American trend-following system as implemented in trendfollowing: binary positions
      from the crossover of two price EWMA filters with an average-true-range entry buffer,
      position sizing at trade inception and trailing stop-losses, the risk budget per trade, and
      how the implementation's range measure and constant-weight P&L differ from the definition.
---

# The American system

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Implemented in [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

The American trend-following system trades breakouts: it opens a position of fixed size when a fast
moving average of prices crosses a slow one by more than a buffer, and it closes the position only
when a trailing stop-loss is breached and the signal has turned off. It descends from the turtle
traders of the 1980s (Covel, 2009; Faith, 2007). Its positions are binary (fully on or off) and
its trades discrete, which makes its turnover about half that of the continuous European system.
This chapter defines the system, documents its state machine in `run_american_system`, and states
where the implementation departs from the definition.

## Overview

The American system differs from the [European system](european_system.md) in three ways
(Sepp and Lucic, 2026, Appendix A.1):

1. **The signal is a crossover of price filters**, not a filter of normalised returns, and it is
   switched on only beyond a buffer proportional to a range measure.
2. **The size is fixed at inception** from the range at entry, rather than updated daily.
3. **The exit is a trailing stop-loss**, not a signal reversal: a continuing trend raises the stop
   and defers the exit.

The labels European and American follow industry usage and have nothing to do with option exercise
styles. Channel and breakout rules are tested by Lukac, Brorsen and Irwin (1988) and Szakmary,
Shen and Sharma (2010); moving-average crossovers by Brock, Lakonishok and LeBaron (1992); and the
stop-loss leg by Kaminski and Lo (2014).

## Inputs, notation, and assumptions

| Convention | This article |
|---|---|
| Return basis | Simple returns of each price column for the P&L; price levels for the signal |
| Normalisation | A price-unit range: in the definition the average true range, in the runner the rolling mean absolute price change |
| Signal filter | Crossover of EWMA filters of prices with spans $N_1\gt N_2$ and an entry buffer of $\omega$ ranges |
| Moment basis | Sample paths of the supplied prices |
| Annualisation | `annualization_factor=260` for the volatility used in the turnover fields |
| Timing | Filters and price at $t$, range at $t-1$; the weight decided at $t$ earns the return of $t+1$ |
| Costs | One-way volume cost per unit of notional turnover, as for the European runner |
| trendfollowing default | `run_american_system(prices, long_span=250, short_span=20, vol_span=33, risk_multiplier=0.01, weight_abs_limit=10.0, stop_loss_atr_multiplier=5.0, signal_atr_multiplier=5.0, warmup_period=250, volume_costs=0.002)` |

| Symbol or input | Meaning | Units and convention |
|---|---|---|
| $\bar s_t^{(\nu_1)}$, $\bar s_t^{(\nu_2)}$ | Slow and fast EWMA filters of the price | Price units |
| $\mathrm{ATR}(t)$ | Average true range over $N_\sigma$ days | Price units |
| $\omega$ | Entry buffer in ranges, `signal_atr_multiplier` | Dimensionless |
| $p$ | Stop-loss width in ranges, `stop_loss_atr_multiplier` | Dimensionless |
| $\chi$ | Risk multiple, `risk_multiplier` | Fraction of notional per range |
| $\bar w$ | Size cap, `weight_abs_limit` | Exposure per unit of capital |
| $\mathrm{sl}(t)$ | Trailing stop level | Price units |
| $t_0$, $\tau$ | Entry and exit day of a trade | Days |

## Methodology

### The average true range

**Definition (true range).** With daily high, low and close prices,

$$
\mathrm{tr}(t)=\max\left\lbrace\lvert s_t^{\mathrm{high}}-s_t^{\mathrm{low}}\rvert,\lvert s_t^{\mathrm{high}}-s_{t-1}^{\mathrm{close}}\rvert,\lvert s_t^{\mathrm{low}}-s_{t-1}^{\mathrm{close}}\rvert\right\rbrace,
\qquad
\mathrm{ATR}(t)=\frac{1}{N_\sigma}\sum_{n=0}^{N_\sigma-1}\mathrm{tr}(t-n).
$$

The ATR is a price-unit volatility measure. Across the paper's core contracts it explains on
average 90% of the variation of the standard deviation of returns, so both risk measures lead to
similar system behaviour (Sepp and Lucic, 2026, Section 2.2).

### The state machine

**Definition (American system; Sepp and Lucic, 2026, Appendix A.1).** With slow and fast filters
$\bar s_t^{(\nu_1)}=\mathcal{L}^{(\nu_1)}(s_t)$ and $\bar s_t^{(\nu_2)}=\mathcal{L}^{(\nu_2)}(s_t)$,
$\nu_1\gt\nu_2$:

**Entry.** From a flat position, open long when $\bar s_t^{(\nu_2)}\gt\bar s_t^{(\nu_1)}+\omega\mathrm{ATR}(t)$
and short when $\bar s_t^{(\nu_2)}\lt\bar s_t^{(\nu_1)}-\omega\mathrm{ATR}(t)$. A long position
opens with size and stop

$$
w^{\mathrm{long}}=\chi\frac{s_t}{\mathrm{ATR}(t)},
\qquad
\mathrm{sl}^{\mathrm{long}}(t)=s_t-p\mathrm{ATR}(t),
$$

and a short position symmetrically with $w^{\mathrm{short}}=-\chi s_t/\mathrm{ATR}(t)$ and
$\mathrm{sl}^{\mathrm{short}}(t)=s_t+p\mathrm{ATR}(t)$.

**Exit.** Close a long position when $s_t\lt\mathrm{sl}(t-1)$ and the long entry condition is off;
otherwise trail the stop, $\mathrm{sl}(t)=\max\lbrace\mathrm{sl}(t-1),s_t-p\mathrm{ATR}(t)\rbrace$.
Close a short position symmetrically, trailing its stop with the minimum.

The exit requires both conditions: a stop breach while the entry signal is still on would re-open
the position on the next day.

**Identity (risk budget per trade).** At entry, the stop distance in returns times the size is
$(p\mathrm{ATR}(t)/s_t)\chi s_t/\mathrm{ATR}(t)=\chi p$: each trade risks the fraction $\chi p$ of
capital to its initial stop, whatever the contract's volatility.

**Proof.** Multiply. $\square$

### Trade P&L and the trailing stop

The trailing-stop recursion unwinds to $\mathrm{sl}(t)=\max_{t_0\le u\le t}\lbrace s_u-p\mathrm{ATR}(u)\rbrace$
for a long trade, so the exit price is close to $s_{\max}-p\mathrm{ATR}$ and, for a short trade, to
$s_{\min}+p\mathrm{ATR}$: the system gives back about $p$ ranges from the best price of the trade. A
position of fixed quantity earns exactly $w(s_\tau/s_{t_0}-1)$ over the trade. Both statements are
heuristics that need an approximately constant range, an entry signal that is off at the first
breach, and no gaps or slippage.

### The implementation

`run_american_system(prices, ...)` runs the state machine per column (`run_american_on_instrument`)
with three choices that differ from the definition:

- **Range.** The runner's `true_range` is the rolling mean of the absolute close-to-close price
  change over `vol_span` days, with at least `vol_span // 2` observations: a close-only proxy of
  the ATR that needs no high and low prices.
- **Timing.** Entry, size and stop on day $t$ use the price and filters of day $t$ and the range of
  day $t-1$. The filters are `qis.ewm_recursion` of the prices seeded with the first price. A
  position opens only after more than `warmup_period` finite prices of that column.
- **Accounting.** The size is a weight held constant over the trade and applied to simple returns,
  $\pi_t=w_{t-1}r_t$, through the same `compute_pnl` as the European runner. A constant weight is a
  position rebalanced daily to constant exposure, not a fixed number of contracts, so the
  accumulated P&L of a trade differs slightly from $w(s_\tau/s_{t_0}-1)$. Sizes are capped at
  `weight_abs_limit`.

> **Pitfall.** The American runner returns no signal matrix, because its signal is a state, and its
> warmup counts finite prices of each column inside the state machine, whereas the European and
> TSMOM runners mask the first finite weights. Compare its weights, NAVs and turnover with the other
> systems, not its signals, and align warmups explicitly in a ragged panel.

### Empirical behaviour

In the paper's grid backtests the American system with $\omega=p=5$ peaks around the spans 250 and
20, like the European system; at matched lookbacks the two correlate at 95%, and the American system
generates about 50% lower turnover and costs, because it trades discretely (Sepp and Lucic, 2026,
Sections 7.1 and 7.2). The European closed form ranks the American system's realised Sharpe ratios
across contracts with a correlation of 0.92 and a slope of 0.61 at spans above one month: the
buffer, the stops and the binary sizing act as an implementation discount on the same alpha
(Section 7.3).

## Worked example

The block runs the system on a synthetic price path with drift, rebuilds its inputs independently,
and checks the state machine: every change is an entry from flat or an exit to flat, entries satisfy
the buffered crossover with the inception size, exits satisfy the stop-and-signal rule, stops trail
monotonically, and the P&L is the lagged weight times the simple return.

```python
import numpy as np
import pandas as pd
import qis
from trendfollowing.systems.american import run_american_on_instrument, run_american_system

rng = np.random.default_rng(20261001)
n_days = 260 * 12
log_price = np.cumsum(0.0003 + 0.01 * rng.standard_normal(n_days))
prices = pd.DataFrame({'X': 100.0 * np.exp(log_price)},
                      index=pd.bdate_range('2000-01-03', periods=n_days))
long_span, short_span, vol_span = 100, 10, 33
risk_multiple, size_cap, stop_width, buffer = 0.01, 10.0, 5.0, 1.0

out = run_american_system(prices=prices, long_span=long_span, short_span=short_span,
                          vol_span=vol_span, risk_multiplier=risk_multiple,
                          weight_abs_limit=size_cap, stop_loss_atr_multiplier=stop_width,
                          signal_atr_multiplier=buffer, warmup_period=250, volume_costs=0.0)
weights = out.weights['X'].to_numpy()

# the runner's inputs, rebuilt: close-to-close range proxy and EWMA filters of the price
price = prices['X'].to_numpy()
true_range = prices['X'].diff().abs().rolling(vol_span, min_periods=vol_span // 2).mean().to_numpy()
slow = qis.ewm_recursion(a=price, span=long_span, init_value=price[0])
fast = qis.ewm_recursion(a=price, span=short_span, init_value=price[0])
replayed, stops = run_american_on_instrument(price=price, long_ewma=slow, short_ewma=fast,
                                             true_range=true_range, risk_multiplier=risk_multiple,
                                             stop_loss_atr_multiplier=stop_width,
                                             signal_atr_multiplier=buffer,
                                             weight_abs_limit=size_cap, warmup_period=250)
np.testing.assert_allclose(weights, replayed)

# every change is an entry from flat or an exit to flat: positions never flip in one day
changes = np.flatnonzero(np.diff(weights) != 0.0) + 1
entries = [t for t in changes if weights[t - 1] == 0.0]
exits = [t for t in changes if weights[t] == 0.0]
assert len(entries) + len(exits) == len(changes) == 97 and entries[0] == 250

for t in entries:  # buffered crossover and size fixed at inception from the range of t - 1
    np.testing.assert_allclose(abs(weights[t]), min(risk_multiple * price[t] / true_range[t - 1],
                                                    size_cap))
    np.testing.assert_allclose(abs(weights[t]) * stop_width * true_range[t - 1] / price[t],
                               risk_multiple * stop_width)  # the risk budget per trade
    if weights[t] > 0.0:
        assert fast[t] > slow[t] + buffer * true_range[t - 1]
    else:
        assert fast[t] < slow[t] - buffer * true_range[t - 1]

for t in exits:  # stop breached and entry signal off
    if weights[t - 1] > 0.0:
        assert price[t] < stops[t - 1] and not fast[t] > slow[t] + buffer * true_range[t - 1]
    else:
        assert price[t] > stops[t - 1] and not fast[t] < slow[t] - buffer * true_range[t - 1]

for start, end in zip(entries, exits):  # stops only trail in the direction of the trade
    direction = np.sign(weights[start])
    assert np.all(direction * np.diff(stops[start:end]) >= 0.0)

# P&L: lagged weight times the simple return; constant weight is not a fixed quantity
simple_returns = prices['X'].pct_change().to_numpy()
np.testing.assert_allclose(out.instrument_pnl['X'].to_numpy()[1:], weights[:-1] * simple_returns[1:],
                           atol=1e-15)
start, end = entries[0], exits[0]
constant_weight = np.sum(weights[start:end] * simple_returns[start + 1:end + 1])
fixed_quantity = weights[start] * (price[end] / price[start] - 1.0)
np.testing.assert_allclose([constant_weight, fixed_quantity], [-0.0878, -0.0886], atol=5e-5)
```

On twelve years of a drifting random walk, the system makes 49 entries and 48 exits and is long
57% of the time after the warmup, short 32% and flat 11%. The first trade is a short entered on
the first eligible day and stopped out 30 days later; held at a constant weight it loses 8.78% of
capital, held at a fixed quantity it would have lost 8.86%.

## Implementation in trendfollowing

| Quantity | Formula | trendfollowing entry point |
|---|---|---|
| State machine for one instrument | entry, size, trailing stop and exit; returns weights and stops | `trendfollowing.systems.american.run_american_on_instrument(price, long_ewma, short_ewma, true_range, risk_multiplier=0.01, stop_loss_atr_multiplier=10.0, signal_atr_multiplier=5.0, weight_abs_limit=5.0, warmup_period=250)` |
| Full backtest | range proxy, filters, state machine, optional portfolio target, accounting | `trendfollowing.systems.american.run_american_system(prices, ...)` |
| Accounting and results | as for the European system | `compute_pnl` and `BacktestOutputs` of `trendfollowing.systems.backtest_utils` |

The system lives in
[american.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/systems/american.py).
The OHLC files of three contracts in the packaged data (`tf_system_data_ohlc_es1.csv`,
`_gc1.csv` and `_ty1.csv`) support the paper's comparison of the ATR with return volatility; the
runner itself needs closes only.
API reference: {py:func}`trendfollowing.systems.american.run_american_system` and
{py:func}`trendfollowing.systems.american.run_american_on_instrument`.

Contract details:

- `run_american_on_instrument` is compiled with Numba and works on one-dimensional arrays; the
  runner passes `weight_abs_limit`, `risk_multiplier` and both multipliers through, and its
  defaults differ from the state machine's (`stop_loss_atr_multiplier=5.0` against `10.0`).
- A series may start with missing prices; the warmup counts finite prices of that column only.
- `volume_costs` is a float or a `DataFrame` aligned with `prices`.

## Interpretation and limitations

- The close-to-close range proxy is not the ATR of the definition; on contracts with large
  intraday ranges relative to close-to-close moves the two scale positions differently.
- The binary size makes the American system's volatility depend on how often it is in the market;
  matching its volatility to another system needs a calibrated `risk_multiplier`, as the paper's
  value of 0.0004 for the 84-contract portfolio.
- Buffers and stops make the system path dependent and nonlinear: no closed form describes it, and
  at fast spans the stops disengage it from the signal.
- Breakout systems are sensitive to the execution price at the breakout; the backtest executes at
  the close of the signal day with no slippage.

## See also

- [The European system](european_system.md)
- [Time-series momentum](tsmom_system.md)
- [Compare and backtest the three systems](system_comparison_and_backtest.md)
- [The futures evidence of Sepp and Lucic (2026)](case_study_futures_evidence.md)
- [Bibliography](bibliography.md)

## References

1. Sepp, A., and Lucic, V. (2026). The Science and Practice of Trend-Following Systems. Working paper. [arXiv:2607.19497](https://arxiv.org/abs/2607.19497); [SSRN 3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787). Appendix A.1 defines the American system; Section 7 tests it.
2. Covel, M. (2009). *The Complete Turtle Trader*. HarperCollins. The turtle-trading programme.
3. Faith, C. (2007). *Way of the Turtle: The Secret Methods that Turned Ordinary People into Legendary Traders*. McGraw-Hill. The turtle rules of entry, sizing and exit.
4. Brock, W., Lakonishok, J., and LeBaron, B. (1992). Simple Technical Trading Rules and the Stochastic Properties of Stock Returns. *The Journal of Finance*, 47(5), 1731–1764. [DOI: 10.1111/j.1540-6261.1992.tb04681.x](https://doi.org/10.1111/j.1540-6261.1992.tb04681.x). Moving-average crossover rules.
5. Kaminski, K. M., and Lo, A. W. (2014). When Do Stop-Loss Rules Stop Losses? *Journal of Financial Markets*, 18, 234–254. [DOI: 10.1016/j.finmar.2013.07.001](https://doi.org/10.1016/j.finmar.2013.07.001). The stop-loss exit.
6. Lukac, L. P., Brorsen, B. W., and Irwin, S. H. (1988). A Test of Futures Market Disequilibrium Using Twelve Different Technical Trading Systems. *Applied Economics*, 20(5), 623–639. [DOI: 10.1080/00036848800000113](https://doi.org/10.1080/00036848800000113). Channel and breakout systems on futures.
7. Szakmary, A. C., Shen, Q., and Sharma, S. C. (2010). Trend-Following Trading Strategies in Commodity Futures: A Re-Examination. *Journal of Banking and Finance*, 34(2), 409–426. [DOI: 10.1016/j.jbankfin.2009.08.004](https://doi.org/10.1016/j.jbankfin.2009.08.004). Breakout rules on commodity futures.
8. Sepp, A., and Lucic, V. trendfollowing: Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python. [Software citation metadata](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).
