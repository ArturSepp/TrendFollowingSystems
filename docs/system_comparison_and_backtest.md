# Compare and backtest the three systems

`trendfollowing` contains three reference implementations from *The Science and Practice of
Trend-Following Systems*. They share a data and P&L contract, but they do not encode the same
signal or use comparable default sizing parameters. Choose the design first; do not select a
runner by comparing its defaults.

## Choose the system

| System | Position rule | Main interface | Use it when |
|---|---|---|---|
| European | continuous EWMA weights from a variance-preserving filter of volatility-normalized returns | `trendfollowing.systems.european.run_european_tf_system` | You want the continuous system behind the package's closed-form expected-return, Sharpe, skewness, and turnover results. |
| American | binary direction from a fast/slow price crossover, with an ATR entry buffer and ATR trailing stops | `trendfollowing.systems.american.run_american_system` | You want a stateful, Turtle-style entry and exit rule whose position size is fixed when the trade opens. |
| TSMOM | TSMOM signs of volatility-normalized period returns, averaged over multiple periods | `trendfollowing.systems.tsmom.run_tsmom_system` | You want a time-series-momentum rule based on the direction of several trailing return blocks rather than an EWMA crossover. |

The American implementation's `true_range` is the rolling mean absolute one-day price change,
not an OHLC high-low true range. Its entry threshold and trailing stop are expressed in multiples
of that scale. TSMOM first averages signed daily normalized returns into blocks of
`num_ra_returns`, then averages `num_periods` blocks. The European signal may use one long EWMA
or the variance-preserving difference between a long and a short EWMA.

## Common input and output contract

Each runner accepts `prices`, a pandas `DataFrame` with a `DatetimeIndex` and one futures price
series per column. Pass price levels, not a return matrix. Missing histories and ragged starts in
the packaged panel are retained so each instrument begins when its data becomes available.

All three runners return
`trendfollowing.systems.backtest_utils.BacktestOutputs`. Its fields have these units:

| Field | Meaning and units |
|---|---|
| `weights` | Dimensionless return exposures. They are not long-only portfolio weights and do not have to sum to one. |
| `signals` | Dimensionless signal values where exposed by the runner. The American state machine returns weights but no separate signal matrix. |
| `instrument_pnl` / `instrument_pnl_net` | Per-instrument daily return contributions before and after transaction costs. |
| `portfolio_pnl` / `portfolio_pnl_net` | Compounded gross and net NAV series, despite the historical `pnl` field names. |
| `portfolio_turnover` | Sum of absolute changes in dimensionless exposure. |
| `portfolio_vol_turnover` | Absolute exposure changes multiplied by the runner's annualized volatility estimates. |
| `portfolio_cost` | Daily fractional return drag deducted from the gross contribution. |

The European runner converts prices to log returns internally. The American and TSMOM runners
use `qis.to_returns` with its default relative-return convention. The maintained root example
then computes an arithmetic simple-return performance summary from
`portfolio_pnl_net.pct_change()`. Keep those layers distinct when comparing a custom result.

## Costs, volatility targeting, and caps

`volume_costs` is either a scalar or a `DataFrame` aligned with `prices`.
It is a one-way fractional cost per unit of absolute weight change: a scalar `0.0020` means 20
basis points for one unit of exposure turnover. The packaged `volume_costs` panel instead varies
the rate by date, instrument, and asset class. Net contribution deducts
`abs(weight[t] - weight[t-1]) * volume_costs[t]`.

European and TSMOM weights multiply their signal by an inverse-volatility exposure controlled by
`vol_target`. American sizing uses `risk_multiplier` and the previous ATR scale when a trade
opens. The systems' default sizing values therefore are not a controlled comparison.

The optional portfolio-level volatility targeting is active only when
`portfolio_covar_span` is not `None`; the resulting exposure is scaled toward
`portfolio_target_vol`. European also exposes `signal_cap` and `weight_cap`, while American
exposes `weight_abs_limit`.
All annualized volatility calculations use an annualization factor of 260 unless explicitly
changed.

Performance analytics, covariance estimation, factsheets, and plotting are delegated to
[`qis`](https://quantinveststrats.readthedocs.io/). The existing comparison and factsheet helper
is `trendfollowing.backtests.joint_backtest`; use the lower-level `qis` documentation for its
reporting conventions rather than assuming a second reporting implementation here.

## Warmup and no look-ahead timing

The default `warmup_period=250` suppresses the first 250 rows of European and TSMOM weights.
American counts finite observations separately for each instrument and cannot open a position
until more than 250 have been seen. A calendar row count and an instrument's observation count
are not interchangeable in a ragged panel.

At the application boundary, the shared P&L function enforces no look-ahead: an exposure decided
at date *t* is multiplied by the return at *t+1*. After initialization, European and TSMOM
normalize a return using lagged volatility. Current-date information may enter a weight at date
*t* because that weight is held only over the next interval. Costs are charged on the date the
exposure changes.

That application lag prevents a direct same-row signal/P&L accident.
It does not make a supplied full-panel calculation fully point-in-time.
The current volatility helper seeds its EWMA with the
variance of the supplied return array, and optional portfolio covariance targeting starts from an
in-sample covariance. These are in-sample initialization choices. The 250-day warmup attenuates
their influence but does not change their information set.

For a strict point-in-time research comparison, estimate on expanding or rolling prefixes that
contain only information available at each decision date, and record the seed and burn-in rule.
Also keep universe membership, cost schedules, parameter selection, and portfolio covariance
estimation point-in-time. The packaged full-history workflow is a paper replication; it is not an
out-of-sample trading simulation merely because weight application is lagged.

## Packaged universe and override

`trendfollowing.universe.load_data` loads the immutable 84-contract futures panel installed in
the wheel. It returns, in order:

1. `prices`;
2. the aligned `volume_costs` panel;
3. 60/40 and SG Trend `benchmark_prices`;
4. `descriptive_df` with instrument metadata; and
5. the seven-asset-class `group_order`.

The panel begins on 1959-07-02 and contains Equities, Bonds, STIR, FX, Energy, Metals, and
Agriculture histories through July 2026. Loading it requires no network or vendor license.

Set `TF_RESOURCE_PATH` to a local folder containing the same `tf_system_data_*.csv` files to
override the installed resources. The path is resolved when `load_data()` is called, so changing
the environment variable does not require a fresh Python process. The override changes the data
source, not the system formulas. You may also pass a user-supplied price and cost panel directly
to a runner.

## Run the authoritative empirical root example

[`examples/backtest_european_system.py`](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/examples/backtest_european_system.py)
is the maintained reusable example. From a core installation and any writable working directory,
run:

```console
python examples/backtest_european_system.py
```

It loads the packaged universe, runs European LS(250,20) with a 33-day volatility estimator, a
63-day portfolio covariance estimator, a 15% portfolio volatility target, the packaged
volume-based costs, and a 250-day warmup. The fixed packaged-data result is:

```text
sharpe       1.095
an_vol       0.152
an_return    0.166
max_dd      -0.362
```

The Sharpe is the annualized arithmetic simple-return ratio with zero cash-rate subtraction and
sample standard deviation (`ddof=1`). The script writes `example_european_backtest.png` to the
current directory. These are historical replication outputs, not a forecast or a claim that one
system dominates the others.

## Verification catalog

### Reusable package workflow

- `tests/test_examples.py` runs the authoritative root scripts headlessly and gates their claimed
  output and files.
- `tests/test_universe.py` gates the 84-contract shape, first date, benchmarks, metadata alignment,
  and packaged OHLC samples.
- `tests/test_packaged_resources.py` checks installed resource files, call-time
  `TF_RESOURCE_PATH` resolution, and the external-only regeneration boundary.
- A wheel audit should import every interface named on this page from the built artifact, not infer
  public names from checkout-only `dir()` side effects.

### Paper reproduction

The root example is deliberately smaller than the paper pipeline. The checkout-only
[`papers/tf_systems/replication/backtest_figs.py`](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/papers/tf_systems/replication/backtest_figs.py)
constructs the controlled three-system comparison and paper figures. The
[`reproduce_all_figures.py`](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/papers/tf_systems/replication/reproduce_all_figures.py)
catalog maps the system illustrations, cost assumptions, grids, SG comparison, and long-term
backtests to their generators. `papers/tf_systems/replication/sg_sharpe_test.py` gates the printed
comparison separately.

Use the {doc}`paper and replication map <paper>` before regenerating exhibits. Paper modules may
write figures and tables and may require checkout-only tooling; they are not installed in the
wheel. For application research, start with `load_data`, one runner, and `BacktestOutputs`, then
add reporting through `qis` with an explicitly stated return and Sharpe convention.

## Non-goals

This guide does not add a strategy, broker integration, optimizer, paper result, or general-purpose
backtesting engine. It documents the three existing reference systems and their current verified
boundaries.
