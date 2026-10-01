---
myst:
  html_meta:
    description: >-
      API reference of trendfollowing: every public object, grouped by the handbook chapter that
      explains it, with signatures and docstrings, the package constants and the module map.
---

# API reference

*Author: [Artur Sepp](https://github.com/ArturSepp) / First recorded: [2026-08-16](https://github.com/ArturSepp/TrendFollowingSystems/commit/1bceb64e2e10fa0014d10f4fbb69c84ece61f667)*

The public interface of [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

The stable import name is `trendfollowing`. The analytical functions are re-exported at the
package top level, as listed in
[`src/trendfollowing/__init__.py`](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/__init__.py);
systems, processes, the data layer and the backtest helpers are imported from their modules.
Every object below is explained in exactly one handbook chapter, and the sections follow the order
of the sidebar. `tests/test_documentation_handbook.py` checks that every top-level export appears
here. The docstrings are plain-text formula notes and are shown verbatim.

Portfolio performance analytics, factsheets and reporting belong to
[qis](https://github.com/ArturSepp/QuantInvestStrats), rather than to a parallel API in this
package.

## Module map

| Module | Responsibility |
|---|---|
| `trendfollowing.analytics` | Closed-form filters, autocorrelation functions, expected returns, turnover, Sharpe ratios, skewness and the Sharpe difference test |
| `trendfollowing.processes` | White-noise, AR(p), MA(q) and ARFIMA path simulation |
| `trendfollowing.systems` | European, American and time-series-momentum reference systems and their accounting |
| `trendfollowing.universe` | The immutable futures dataset installed with the wheel and its cost schedule |
| `trendfollowing.backtests` | Portfolio-level grids and the joint backtest of the paper, reported through qis |
| `trendfollowing.conventions` | Annualisation constants of the papers |
| `trendfollowing.local_path` | Package resources and external writable folders |

## Constants

| Name | Value | Meaning | Explained in |
|---|---|---|---|
| `trendfollowing.AF_DAILY` | `260.0` | Trading days per year, the paper convention | [Notation and conventions](notation_and_conventions.md) |
| `trendfollowing.PPY_QUARTERLY` | `4.0` | Periods per year of quarterly statistics | [Notation and conventions](notation_and_conventions.md) |
| `trendfollowing.PPY_MONTHLY` | `12.0` | Periods per year of monthly statistics | [Notation and conventions](notation_and_conventions.md) |
| `trendfollowing.__version__` | installed version | Distribution version, `0+unknown` from an uninstalled tree | [Installation](installation.md) |
| `trendfollowing.universe.COST_STRUCTURE` | three periods by seven classes | One-way volume costs | [The futures universe and cost schedule](futures_universe_and_costs.md) |
| `trendfollowing.backtests.PERF_PARAMS` | `qis.PerfParams` | Arithmetic Sharpe convention of the grids | [The futures evidence](case_study_futures_evidence.md) |
| `trendfollowing.backtests.regime_classifier` | `qis.BenchmarkReturnsQuantilesRegime` | Quarterly 16/84 regimes of the benchmark | [Realised Sharpe ratios](sharpe_inference.md) |

## Notation and conventions

Explained in [Notation and conventions](notation_and_conventions.md).

```{eval-rst}
.. autofunction:: trendfollowing.compute_daily_annualised_vol
```

## EWMA filters and variance-preserving signals

Explained in [EWMA filters and variance-preserving signals](ewma_filters.md).

```{eval-rst}
.. autofunction:: trendfollowing.span_to_nu
.. autofunction:: trendfollowing.compute_ewm_long_short_weights
```

## Volatility normalisation and position sizing

Explained in [Volatility normalisation and position sizing](volatility_normalisation.md).

```{eval-rst}
.. autofunction:: trendfollowing.systems.backtest_utils.compute_vol
.. autofunction:: trendfollowing.systems.backtest_utils.compute_vol_norm_returns
.. autofunction:: trendfollowing.systems.backtest_utils.compute_vol_target_weight
```

## Return-generating processes

Explained in [Return-generating processes](return_processes.md). `ProcessType` has the members
`WHITE_NOISE`, `AR_P`, `MA_Q` and `ARFIMA`.

```{eval-rst}
.. autofunction:: trendfollowing.population_acf
.. autofunction:: trendfollowing.power_autocorr
.. autofunction:: trendfollowing.analytics.autocorrelation.ma_weights
.. autoclass:: trendfollowing.processes.path_engine.ProcessType
.. autofunction:: trendfollowing.processes.path_engine.generate_paths
.. autofunction:: trendfollowing.processes.path_engine.simulate_white_noise_paths
.. autofunction:: trendfollowing.processes.path_engine.simulate_ar_p_paths
.. autofunction:: trendfollowing.processes.path_engine.simulate_ma_q_paths
.. autofunction:: trendfollowing.processes.path_engine.simulate_arfima_paths
.. autofunction:: trendfollowing.processes.path_engine.set_seed
.. autofunction:: trendfollowing.processes.arfima.arfima
```

## The P&L decomposition

Explained in [The P&L decomposition: autocorrelation and drift channels](pnl_decomposition.md).

```{eval-rst}
.. autofunction:: trendfollowing.compute_psi_nu
.. autofunction:: trendfollowing.expected_annual_return
.. autofunction:: trendfollowing.expected_pnl_white_noise
.. autofunction:: trendfollowing.expected_pnl_ar1
.. autofunction:: trendfollowing.expected_pnl_ma1
.. autofunction:: trendfollowing.expected_pnl_arfima
```

## The closed-form Sharpe ratio

Explained in [The closed-form Sharpe ratio](sharpe_ratio_closed_form.md). `SignalMoments` is a
named tuple with the fields `s_mean`, `s_var` and `s_cov`.

```{eval-rst}
.. autoclass:: trendfollowing.SignalMoments
.. autofunction:: trendfollowing.compute_signal_moments
.. autofunction:: trendfollowing.compute_daily_moments
.. autofunction:: trendfollowing.compute_annualised_sharpe
.. autofunction:: trendfollowing.analytics.sharpe.compute_kurtosis_loading
.. autofunction:: trendfollowing.analytics.sharpe.kurtosis_loading_ar1
```

## Sharpe ratios under white noise, AR(1) and ARFIMA

Explained in [Sharpe ratios under white noise, AR(1) and ARFIMA](sharpe_under_processes.md).

```{eval-rst}
.. autofunction:: trendfollowing.sharpe_white_noise
.. autofunction:: trendfollowing.sharpe_white_noise_approx
.. autofunction:: trendfollowing.sharpe_ar1
.. autofunction:: trendfollowing.sharpe_ar1_approx
.. autofunction:: trendfollowing.sharpe_arfima
```

## Turnover, trading costs and the net Sharpe ratio

Explained in [Turnover, trading costs and the net Sharpe ratio](turnover_and_net_sharpe.md).

```{eval-rst}
.. autofunction:: trendfollowing.expected_turnover
```

## Skewness of aggregated returns

Explained in [Skewness of aggregated returns](aggregated_skewness.md).

```{eval-rst}
.. autofunction:: trendfollowing.aggregated_third_moment_white_noise
.. autofunction:: trendfollowing.skewness_white_noise
.. autofunction:: trendfollowing.skewness_master_curve
.. autofunction:: trendfollowing.skewness_peak_horizon
```

## The European system

Explained in [The European system](european_system.md). `BacktestOutputs` is the result of all
three runners.

```{eval-rst}
.. autofunction:: trendfollowing.systems.european.compute_tf_signal
.. autofunction:: trendfollowing.systems.european.compute_tf_signal_weight
.. autofunction:: trendfollowing.systems.european.compute_tf_strat_pnl
.. autofunction:: trendfollowing.systems.european.run_european_tf_system
.. autoclass:: trendfollowing.systems.backtest_utils.BacktestOutputs
   :members: np_arrays_to_frames
.. autofunction:: trendfollowing.systems.backtest_utils.compute_pnl
.. autofunction:: trendfollowing.systems.backtest_utils.compute_path_stats
```

## The American system

Explained in [The American system](american_system.md).

```{eval-rst}
.. autofunction:: trendfollowing.systems.american.run_american_on_instrument
.. autofunction:: trendfollowing.systems.american.run_american_system
```

## Time-series momentum

Explained in [Time-series momentum](tsmom_system.md).

```{eval-rst}
.. autofunction:: trendfollowing.systems.tsmom.compute_tsmom_signal_weight
.. autofunction:: trendfollowing.systems.tsmom.run_tsmom_system
```

## The futures universe and cost schedule

Explained in [The futures universe and cost schedule](futures_universe_and_costs.md).

```{eval-rst}
.. autofunction:: trendfollowing.universe.load_data
.. autofunction:: trendfollowing.universe.get_costs
.. autofunction:: trendfollowing.universe.generate_data
.. autofunction:: trendfollowing.local_path.get_universe_data_path
.. autofunction:: trendfollowing.local_path.get_resource_path
.. autofunction:: trendfollowing.local_path.get_papers_data_path
.. autofunction:: trendfollowing.local_path.get_output_path
```

## Realised Sharpe ratios and their comparison

Explained in [Realised Sharpe ratios and their comparison](sharpe_inference.md).

```{eval-rst}
.. autofunction:: trendfollowing.compute_realized_sharpe
.. autoclass:: trendfollowing.analytics.sharpe_test.SharpeDiffTest
.. autofunction:: trendfollowing.analytics.sharpe_test.sharpe_difference_test
```

## The futures evidence of Sepp and Lucic (2026)

Explained in [The futures evidence of Sepp and Lucic (2026)](case_study_futures_evidence.md).
`TFstrategy` has the members `EUROPEAN`, `AMERICAN` and `TSMOM`.

```{eval-rst}
.. autoclass:: trendfollowing.backtests.TFstrategy
.. autofunction:: trendfollowing.backtests.joint_backtest
.. autofunction:: trendfollowing.backtests.backtest_span_grid
.. autofunction:: trendfollowing.backtests.backtest_american_atr_multiplies_grid
.. autofunction:: trendfollowing.backtests.backtest_tsmom_grid
.. autofunction:: trendfollowing.backtests.cross_backtest_portfolio_covar_span
.. autofunction:: trendfollowing.backtests.plot_backtest
.. autofunction:: trendfollowing.backtests.plot_grid_backtest
```

## See also

- [Quickstart](quickstart.md) for a first top-level call
- [Example workflows](workflows.md) for executable integrations
- [Documentation standard](documentation_standard.md) for how this page is maintained
