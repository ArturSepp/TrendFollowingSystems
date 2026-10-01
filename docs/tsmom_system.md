---
myst:
  html_meta:
    description: >-
      The time-series momentum (TSMOM) system as implemented in trendfollowing: the normalised
      sum of signs of daily returns over M periods of L days, its unit-variance property, the
      rebalancing grid and forward fill, the sign-filter discount of the Bussgang identity, and
      the generalisation of Moskowitz, Ooi and Pedersen (2012).
---

# Time-series momentum

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Implemented in [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

Time-series momentum (TSMOM) takes a position in the direction of an instrument's own past return,
sized by its volatility. In the academic form of Moskowitz, Ooi and Pedersen (2012) the signal is
the sign of the trailing twelve-month return, rebalanced monthly. The trendfollowing implementation
generalises it to the normalised sum of the signs of daily returns over $M$ periods of $L$ days,
which has unit variance under serial independence, mirrors the European signal, and separates the
lookback $ML$ from the rebalancing frequency $L$. This chapter defines the system, proves its
normalisation, and states the discount that the sign transform applies to the trend alpha.

## Overview

TSMOM is the third system design of Sepp and Lucic (2026, Section 3), common in academic studies
(Moskowitz, Ooi and Pedersen, 2012; Hurst, Ooi and Pedersen, 2013; Baltas, 2015; Dudler, Gmür and
Malamud, 2015). Compared with the [European system](european_system.md) it replaces the linear
EWMA filter by a box filter of signs, and it rebalances on a grid of every $L$ days instead of
daily. The chapter answers three questions:

1. How is the generalised TSMOM signal constructed, and why is it a z-score?
2. Which dates does it use and when is it applied?
3. How does the sign transform change the alpha relative to a linear signal?

## Inputs, notation, and assumptions

| Convention | This article |
|---|---|
| Return basis | Simple returns of each price column, for the signal and for the P&L |
| Normalisation | Signs of $r_t/\sigma_{t-1}$, equal to the signs of $r_t$; volatility-target weight with $\sigma_t$ at the block end |
| Signal filter | Sum of the signs of the last $ML$ daily returns, divided by $\sqrt{ML}$, on a grid of every $L$ days |
| Moment basis | Serially independent returns with zero median for the unit-variance result |
| Annualisation | `annualization_factor=260` for the volatility target |
| Timing | The weight at a block end uses returns up to that day, is forward filled, and earns from the next day |
| Costs | One-way volume cost per unit of notional turnover, as for the European runner |
| trendfollowing default | `run_tsmom_system(prices, num_ra_returns=10, num_periods=10, vol_span=33, vol_target=0.00435, portfolio_covar_span=None, portfolio_target_vol=0.15, volume_costs=0.002, warmup_period=250)` |

| Symbol or input | Meaning | Units and convention |
|---|---|---|
| $L$ | Period length, `num_ra_returns` | Days; also the rebalancing interval |
| $M$ | Number of periods, `num_periods` | Lookback of $ML$ days |
| $t'$ | Block end on the rebalancing grid | Every $L$-th day, aligned so that the last block is complete |
| $b_{t'}$ | Sum of the $L$ daily signs in the block ending at $t'$ | Integer in $[-L,L]$ |

## Methodology

### From monthly signs to daily signs

**Definition (Moskowitz, Ooi and Pedersen, 2012).** With month-end prices, the classical weight is
the average sign of the trailing twelve-month return over $M$ rolling windows, scaled by the
inverse annualised volatility,

$$
w_t=\frac{1}{M}\sum_{m=1}^{M}\operatorname{sign}\left(\frac{s_{t-m+1}}{s_{t-m-11}}-1\right)\frac{\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}\sigma_{t-1}} .
$$

Dudler, Gmür and Malamud (2015) average the signs of volatility-normalised returns instead.

**Definition (generalised TSMOM; Sepp and Lucic, 2026, Appendix A.2).** On the grid of block ends
$t'$, every $L$ days,

$$
S_{t'}=\frac{1}{\sqrt{ML}}\sum_{m=1}^{M}b_{t'-(m-1)L},
\qquad
b_{t'}=\sum_{t=t'-L+1}^{t'}\operatorname{sign}\left(\frac{r_t}{\sigma_{t-1}}\right),
\qquad
w_{t'}=S_{t'}\frac{\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}\sigma_{t'}},
$$

and $w_{t'}$ is forward filled until the next block end.

**Proposition (unit variance).** If the daily returns are serially independent with a distribution
continuous at zero and with zero median, then $\mathbb{E}[S_{t'}]=0$ and $\operatorname{Var}[S_{t'}]=1$.

**Proof.** The double sum reindexes to a single sum of $ML$ daily signs over disjoint days. Each
sign is a Rademacher variable with unit variance, and independence makes them uncorrelated, so the
sum has variance $ML$. $\square$

Three consequences follow. The signal value depends on $(L,M)$ only through the product $ML$,
while $L$ sets the rebalancing frequency. The sign removes the volatility estimator from the signal,
because $\operatorname{sign}(r_t/\sigma_{t-1})=\operatorname{sign}(r_t)$. And the strategy volatility
per instrument is approximately $\sigma_{\mathrm{target}}$ whatever $L$ and $M$. An atom at zero, such
as a day without a price change, lowers the variance of the sign.

### The sign-filter discount

**Identity (Bussgang).** For a jointly Gaussian pair $(S,z)$ with $S$ of zero mean and unit variance,

$$
\mathbb{E}[\operatorname{sign}(S)z]=\sqrt{\frac{2}{\pi}}\mathbb{E}[Sz]\approx 0.80\mathbb{E}[Sz].
$$

**Proof.** Project $z=\mathbb{E}[Sz]S+e$ with $e$ independent of $S$; then
$\mathbb{E}[\operatorname{sign}(S)z]=\mathbb{E}[Sz]\mathbb{E}[\lvert S\rvert]$ and
$\mathbb{E}[\lvert S\rvert]=\sqrt{2/\pi}$. $\square$

The sign transform scales the autocorrelation channel by $\sqrt{2/\pi}$ and leaves the variance at
one to leading order, since $\operatorname{sign}^2=1$. This is the benchmark slope of a TSMOM
system against the European closed form. Empirically, with daily signs and the number of periods
equal to the span, the European closed form ranks the realised Sharpe ratios of TSMOM across the 84
contracts with a correlation of 0.89 and a slope of 0.73, close to the Gaussian benchmark of 0.80
(Sepp and Lucic, 2026, Section 7.3).

### The implementation

`compute_tsmom_signal_weight(returns, num_ra_returns=L, num_periods=M, ...)` computes the signs of
the volatility-normalised returns, sums them over blocks of $L$ rows with
`qis.utils.df_freq.df_resample_at_int_index`, and averages $M$ consecutive blocks. The blocks are
aligned backwards from the last row, so that the final block is complete; each block takes the date
of its last row. Missing signs are skipped within a block, by a NaN-aware mean scaled by $L$. The
volatility-target weight uses the unlagged volatility at the block end, $\sigma_{t'}$, where the
definition writes $\sigma_{t'-1}$. Signal, weight and volatility are then forward filled to the daily
index. `run_tsmom_system` adds the optional portfolio volatility target, masks the first
`warmup_period` finite weights, and accounts P&L on simple returns with `compute_pnl`.

In the paper's grid backtests TSMOM peaks around $M=L=10$, and the SG Trend comparison uses $L=10$
and $M=10$ (Sepp and Lucic, 2026, Sections 7.1 and 7.2). The rebalancing every $L$ days generates
turnover of the same order as the European system; the paper recommends weekly to monthly
rebalancing, $L$ between 5 and 30.

## Worked example

The block checks the signal against the direct sum of signs at the block ends, the forward fill and
the volatility-target weight, the unit variance under independence, and the Bussgang identity by
simulation.

```python
import numpy as np
import pandas as pd
from trendfollowing.systems.backtest_utils import compute_vol_norm_returns, compute_vol_target_weight
from trendfollowing.systems.tsmom import compute_tsmom_signal_weight, run_tsmom_system

rng = np.random.default_rng(20261001)
dates = pd.bdate_range('2010-01-01', periods=1000)
returns = pd.DataFrame(0.01 * rng.standard_normal((1000, 2)), index=dates, columns=['A', 'B'])
L, M = 5, 4

weights, signals, vols = compute_tsmom_signal_weight(returns=returns, num_ra_returns=L,
                                                     num_periods=M, vol_span=33, vol_target=0.15)

# the signs of normalised returns are the signs of returns
z = pd.DataFrame(compute_vol_norm_returns(returns=returns.to_numpy(), vol_span=33), index=dates,
                 columns=returns.columns)
assert (np.sign(z.iloc[2:]) == np.sign(returns.iloc[2:])).all().all()

# block ends: every L-th row counted back from the last row; the signal there is the
# sum of the last M * L signs divided by sqrt(M * L)
block_ends = dates[::-1][::L][::-1]
direct = np.sign(z).rolling(M * L).sum() / np.sqrt(M * L)
at_ends = direct.reindex(block_ends).dropna()
np.testing.assert_allclose(signals.reindex(at_ends.index).to_numpy(), at_ends.to_numpy(), atol=1e-12)

# between block ends the signal is forward filled: it changes only on block ends
changed = signals.diff().abs().fillna(0.0).gt(0.0).any(axis=1)
assert set(changed[changed].index) <= set(block_ends)

# the weight is the volatility-target weight at the block end times the signal
weight_vt, _ = compute_vol_target_weight(returns=returns.to_numpy(), vol_span=33, vol_target=0.15)
weight_vt = pd.DataFrame(weight_vt, index=dates, columns=returns.columns)
np.testing.assert_allclose(weights.reindex(at_ends.index).to_numpy(),
                           (weight_vt.reindex(at_ends.index) * at_ends).to_numpy(), rtol=1e-12,
                           atol=1e-14)

# unit variance under independence: 40 columns of 4000 days, signal on non-overlapping blocks
panel = pd.DataFrame(rng.standard_normal((4000, 40)), index=pd.bdate_range('2000-01-03', periods=4000))
_, panel_signals, _ = compute_tsmom_signal_weight(returns=panel, num_ra_returns=10, num_periods=10)
disjoint = panel_signals.iloc[200::100].to_numpy().ravel()
np.testing.assert_allclose([disjoint.mean(), disjoint.var()], [0.0, 1.0], atol=0.06)

# Bussgang: the sign transform keeps sqrt(2 / pi) of the covariance with the next return
correlated = rng.multivariate_normal([0.0, 0.0], [[1.0, 0.1], [0.1, 1.0]], size=2_000_000)
signal_draw, next_return = correlated[:, 0], correlated[:, 1]
ratio = np.mean(np.sign(signal_draw) * next_return) / np.mean(signal_draw * next_return)
np.testing.assert_allclose(ratio, np.sqrt(2.0 / np.pi), atol=0.03)

# the backtest applies the lagged weight to simple returns
prices = 100.0 * (1.0 + returns).cumprod()
out = run_tsmom_system(prices=prices, num_ra_returns=L, num_periods=M, vol_span=33, vol_target=0.15,
                       volume_costs=0.0, warmup_period=250)
simple = prices.pct_change()
np.testing.assert_allclose(out.instrument_pnl.iloc[300:].to_numpy(),
                           (out.weights.shift(1) * simple).iloc[300:].to_numpy(), atol=1e-14)
```

The signals at the block ends equal the normalised sums of signs exactly, and they change only on
block ends. Across 40 independent columns the signal has mean zero and unit variance, and a linear
signal correlated at 0.1 with the next return keeps 80% of its covariance after the sign transform.

## Implementation in trendfollowing

| Quantity | Formula | trendfollowing entry point |
|---|---|---|
| Signal, weight and volatility | $S_{t'}$, $w_{t'}$ and $\sqrt{\mathrm{af}}\sigma_{t'}$, forward filled | `trendfollowing.systems.tsmom.compute_tsmom_signal_weight(returns, num_ra_returns=22, num_periods=12, vol_span=33, vol_target=0.15, annualization_factor=260)` |
| Full backtest | signal, optional portfolio target, warmup, accounting | `trendfollowing.systems.tsmom.run_tsmom_system(prices, ...)` |
| Accounting and results | as for the European system | `compute_pnl` and `BacktestOutputs` of `trendfollowing.systems.backtest_utils` |

The system lives in
[tsmom.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/systems/tsmom.py).
API reference: {py:func}`trendfollowing.systems.tsmom.compute_tsmom_signal_weight` and
{py:func}`trendfollowing.systems.tsmom.run_tsmom_system`.

Contract details:

- `compute_tsmom_signal_weight` takes a returns `DataFrame`; `run_tsmom_system` takes prices and
  converts them with `qis.to_returns`.
- The defaults differ between the two functions ($L=22$, $M=12$ against $L=10$, $M=10$) and
  the runner's `vol_target=0.00435` is a per-instrument target for a large portfolio. Pass the
  parameters explicitly.
- A `volume_costs` frame is forward filled onto the weight index.

> **Pitfall.** The first signal value requires $M$ complete blocks, so the system is flat for at
> least $ML$ days before the warmup is applied on top. With large $M$ and $L$ the effective start is
> later than `warmup_period` suggests.

## Interpretation and limitations

- The sign transform discards the size of returns: a large move counts as much as a small one,
  which makes the signal robust to outliers and blind to their information.
- The unit-variance result assumes zero-median independent returns. Positive drift shifts the mean
  of the signs, and positive autocorrelation raises their variance.
- Rebalancing every $L$ days makes the system's performance depend on the phase of the grid; the
  implementation aligns the grid to the last row of the sample, so extending the sample by one day
  shifts every block end.
- The European closed form ranks TSMOM empirically, not mathematically: the transfer rests on the
  Gaussian sign identity and the matched lookback, and its slope is an implementation discount.

## See also

- [The European system](european_system.md)
- [The American system](american_system.md)
- [EWMA filters and variance-preserving signals](ewma_filters.md)
- [Compare and backtest the three systems](system_comparison_and_backtest.md)
- [Bibliography](bibliography.md)

## References

1. Sepp, A., and Lucic, V. (2026). The Science and Practice of Trend-Following Systems. Working paper. [arXiv:2607.19497](https://arxiv.org/abs/2607.19497); [SSRN 3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787). Appendix A.2 defines the generalised TSMOM system; Section 7.3 measures its implementation discount.
2. Moskowitz, T. J., Ooi, Y. H., and Pedersen, L. H. (2012). Time Series Momentum. *Journal of Financial Economics*, 104(2), 228–250. [DOI: 10.1016/j.jfineco.2011.11.003](https://doi.org/10.1016/j.jfineco.2011.11.003). The classical TSMOM signal.
3. Hurst, B., Ooi, Y. H., and Pedersen, L. H. (2013). Demystifying Managed Futures. *Journal of Investment Management*, 11(3), 42–58. TSMOM as a model of managed futures.
4. Baltas, N. (2015). Trend-Following, Risk-Parity and the Influence of Correlations. In Jurczenko, E. (ed.), *Risk-Based and Factor Investing*, 65–96. ISTE Press and Elsevier. TSMOM portfolio construction.
5. Dudler, M., Gmür, B., and Malamud, S. (2015). Momentum and Risk Adjustment. *The Journal of Alternative Investments*, 18(2), 91–103. Signs of volatility-normalised returns.
6. Sepp, A., and Lucic, V. trendfollowing: Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python. [Software citation metadata](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).
