"""
portfolio-level backtests of the three tf systems on the futures universe: the
joint run against the benchmarks, the span and parameter grids, the tsmom lookback
grid, and the portfolio volatility-targeting cross-section behind the
implementation exhibits of the paper
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""

import numpy as np
import pandas as pd
import qis as qis
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Optional, Union, List, Tuple
from enum import Enum

from trendfollowing.systems.american import run_american_system
from trendfollowing.systems.european import run_european_tf_system
from trendfollowing.systems.tsmom import run_tsmom_system


PERF_PARAMS = qis.PerfParams(
    freq_reg='W-WED',
    freq_vol='B',
    freq_drawdown='B',
    sharpe_convention=qis.perfstats.config.SharpeConvention.ARITHMETIC,
)
regime_classifier = qis.BenchmarkReturnsQuantilesRegime(
    freq='QE', q=np.array([0.0, 0.16, 0.84, 1.0])
)  # one-sigma 16/84 cut


class TFstrategy(Enum):
    """
    enum of the three system designs
    """

    EUROPEAN = 1
    AMERICAN = 2
    TSMOM = 3


def joint_backtest(
    prices: pd.DataFrame,
    volume_costs: pd.DataFrame,
    benchmark_prices: pd.DataFrame,
    time_period: qis.TimePeriod = None,
) -> plt.Figure:
    """
    run the european ls(250,20), the american, and the tsmom systems on common
    prices with volume-based costs and report them against the benchmarks
    """
    e_backtest_outputs = run_european_tf_system(
        prices=prices,
        long_span=250,
        short_span=20,
        vol_span=33,
        vol_target=0.0035,
        portfolio_covar_span=None,
        portfolio_target_vol=0.15,
        volume_costs=volume_costs,
    )

    a_backtest_outputs = run_american_system(
        prices=prices,
        risk_multiplier=0.0004,
        vol_span=33,
        portfolio_covar_span=None,
        portfolio_target_vol=0.15,
        volume_costs=volume_costs,
    )

    tsmom_backtest_outputs = run_tsmom_system(
        prices=prices,
        num_ra_returns=5,
        num_periods=10,
        vol_span=33,
        vol_target=0.0035,
        portfolio_covar_span=None,
        portfolio_target_vol=0.15,
        volume_costs=volume_costs,
    )

    prices = pd.concat(
        [
            benchmark_prices,
            e_backtest_outputs.portfolio_pnl.rename('European gross'),
            e_backtest_outputs.portfolio_pnl_net.rename('European net'),
            a_backtest_outputs.portfolio_pnl.rename('American gross'),
            a_backtest_outputs.portfolio_pnl_net.rename('American net'),
            tsmom_backtest_outputs.portfolio_pnl.rename('TSMOM gross'),
            tsmom_backtest_outputs.portfolio_pnl_net.rename('TSMOM net'),
        ],
        axis=1,
        sort=True,
    )

    fig = qis.generate_multi_asset_factsheet(
        prices=prices,
        benchmark=benchmark_prices.columns[0],
        time_period=time_period,
        **qis.fetch_default_report_kwargs(time_period=time_period, add_rates_data=False),
    )
    df = pd.concat(
        [
            benchmark_prices.iloc[:, -1],
            e_backtest_outputs.portfolio_pnl_net.rename('European net'),
            a_backtest_outputs.portfolio_pnl_net.rename('American net'),
            tsmom_backtest_outputs.portfolio_pnl_net.rename('TSMOM net'),
        ],
        axis=1,
        sort=True,
    )

    qis.plot_returns_corr_matrix_time_series(
        prices=df, span=100, time_period=time_period, framealpha=0.9
    )

    return fig


def backtest_span_grid(
    prices: pd.DataFrame,
    volume_costs: pd.DataFrame,
    benchmark_prices: pd.DataFrame,
    tf_strategy: TFstrategy = TFstrategy.EUROPEAN,
    long_spans: List[int] = (30, 50, 75, 100, 175, 250, 375, 500),
    short_spans: List[int] = (5, 10, 20, 30, 40, 50, 75, 100),
    vol_span: int = 33,
    vol_target: float = 0.05,
    risk_multiplier: float = 0.0004,
    portfolio_covar_span: Optional[int] = 100,
    portfolio_target_vol: float = 0.15,
    annualization_factor: float = 260.0,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # long_spans = (100, 250, 500)
    # short_spans = (20, 40, 100)
    """
    sharpe ratio, turnover, and costs of one system across the grid of long and short filter spans
    """
    benchmark = benchmark_prices.columns[0]

    net_sharpes = {}
    bear_sharpes = {}
    costs = {}
    for idx1, long_span in enumerate(long_spans):
        pnls = {}
        costs_ = {}
        for idx2, short_span in enumerate(short_spans):
            if long_span > short_span:
                if tf_strategy == TFstrategy.EUROPEAN:
                    backtest_outputs = run_european_tf_system(
                        prices=prices,
                        long_span=long_span,
                        short_span=short_span,
                        vol_span=vol_span,
                        vol_target=vol_target,
                        portfolio_covar_span=portfolio_covar_span,
                        portfolio_target_vol=portfolio_target_vol,
                        annualization_factor=annualization_factor,
                        volume_costs=volume_costs,
                    )
                elif tf_strategy == TFstrategy.AMERICAN:
                    backtest_outputs = run_american_system(
                        prices=prices,
                        long_span=long_span,
                        short_span=short_span,
                        vol_span=vol_span,
                        stop_loss_atr_multiplier=5.0,
                        signal_atr_multiplier=5.0,
                        annualization_factor=annualization_factor,
                        risk_multiplier=risk_multiplier,
                        volume_costs=volume_costs,
                    )
                else:
                    raise NotImplementedError(f"{tf_strategy}")

                pnls[f"short={short_span:0.0f}"] = pd.Series(
                    backtest_outputs.portfolio_pnl_net, index=prices.index
                )
                costs_[f"short={short_span:0.0f}"] = pd.Series(
                    backtest_outputs.portfolio_cost, index=prices.index
                )

        pnls = pd.DataFrame.from_dict(pnls, orient='columns')
        prices1 = pd.concat([benchmark_prices[benchmark], pnls], axis=1, sort=True)
        costs_ = pd.DataFrame.from_dict(costs_, orient='columns')

        ra_perf_table = qis.compute_bnb_regimes_pa_perf_table(
            prices=prices1,
            benchmark=benchmark,
            regime_classifier=regime_classifier,
            perf_params=PERF_PARAMS,
        )

        net_sharpes[f"long={long_span:0.0f}"] = ra_perf_table[qis.PerfStat.SHARPE_ARITH.to_str()]
        bear_sharpes[f"long={long_span:0.0f}"] = ra_perf_table[qis.PerfStat.BEAR_SHARPE.to_str()]
        costs[f"long={long_span:0.0f}"] = annualization_factor * costs_.mean(axis=0)

    net_sharpes = pd.DataFrame.from_dict(net_sharpes, orient='index').drop(benchmark, axis=1)
    bear_sharpes = pd.DataFrame.from_dict(bear_sharpes, orient='index').drop(benchmark, axis=1)
    costs = pd.DataFrame.from_dict(costs, orient='index')

    return net_sharpes, bear_sharpes, costs


def backtest_american_atr_multiplies_grid(
    prices: pd.DataFrame,
    volume_costs: pd.DataFrame,
    benchmark_prices: pd.DataFrame,
    stop_loss_atr_multipliers: List[float] = np.linspace(0.5, 7.5, 8),
    signal_atr_multipliers: List[float] = np.linspace(0.5, 7.5, 8),
    long_span: int = 250,
    short_span: int = 50,
    vol_span: int = 33,
    vol_target: float = 0.05,
    risk_multiplier: float = 0.0004,
    portfolio_covar_span: Optional[int] = 100,
    portfolio_target_vol: float = 0.15,
    annualization_factor: float = 260.0,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    performance of the american system across the grid of atr risk multipliers
    """
    benchmark = benchmark_prices.columns[0]
    net_sharpes = {}
    bear_sharpes = {}
    costs = {}
    for idx1, stop_loss_atr_multiplier in enumerate(stop_loss_atr_multipliers):
        pnls = {}
        costs_ = {}
        for idx2, signal_atr_multiplier in enumerate(signal_atr_multipliers):
            backtest_outputs = run_american_system(
                prices=prices,
                long_span=long_span,
                short_span=short_span,
                vol_span=vol_span,
                stop_loss_atr_multiplier=stop_loss_atr_multiplier,
                signal_atr_multiplier=signal_atr_multiplier,
                annualization_factor=annualization_factor,
                risk_multiplier=risk_multiplier,
                volume_costs=volume_costs,
            )
            key2 = f"signal q={signal_atr_multiplier:0.2f}"
            pnls[key2] = pd.Series(backtest_outputs.portfolio_pnl_net, index=prices.index)
            costs_[key2] = pd.Series(backtest_outputs.portfolio_cost, index=prices.index)
        pnls = pd.DataFrame.from_dict(pnls, orient='columns')
        costs_ = pd.DataFrame.from_dict(costs_, orient='columns')
        prices1 = pd.concat([benchmark_prices[benchmark], pnls], axis=1, sort=True)
        ra_perf_table = qis.compute_bnb_regimes_pa_perf_table(
            prices=prices1,
            benchmark=benchmark,
            regime_classifier=regime_classifier,
            perf_params=PERF_PARAMS,
        )
        key1 = f"stop-loss p={stop_loss_atr_multiplier:0.2f}"
        net_sharpes[key1] = ra_perf_table[qis.PerfStat.SHARPE_ARITH.to_str()]
        bear_sharpes[key1] = ra_perf_table[qis.PerfStat.BEAR_SHARPE.to_str()]
        costs[key1] = annualization_factor * costs_.mean(axis=0)
    net_sharpes = pd.DataFrame.from_dict(net_sharpes, orient='index').drop(benchmark, axis=1)
    bear_sharpes = pd.DataFrame.from_dict(bear_sharpes, orient='index').drop(benchmark, axis=1)
    costs = pd.DataFrame.from_dict(costs, orient='index')
    return net_sharpes, bear_sharpes, costs


def cross_backtest_portfolio_covar_span(
    prices: pd.DataFrame,
    portfolio_covar_spans: List[Optional[int]] = (None, 30, 60, 90, 130, 260, 520),
    tf_strategy: TFstrategy = TFstrategy.EUROPEAN,
    long_span: int = 250,
    short_span: Optional[int] = 20,
    vol_span: int = 33,
    vol_target: float = 0.05,
    risk_multiplier: float = 0.0004,
    portfolio_covar_span: Optional[int] = None,
    portfolio_target_vol: float = 0.15,
    annualization_factor: float = 260.0,
    volume_costs: Union[float, pd.DataFrame] = 0.0010,
    time_period: qis.TimePeriod = None,
) -> pd.DataFrame:
    """
    performance of one system across the portfolio covariance spans of the
    portfolio-level volatility targeting
    """
    pnls = {}
    for portfolio_covar_span in portfolio_covar_spans:
        if tf_strategy == TFstrategy.EUROPEAN:
            backtest_outputs = run_european_tf_system(
                prices=prices,
                long_span=long_span,
                short_span=short_span,
                vol_span=portfolio_covar_span or vol_span,
                vol_target=vol_target,
                portfolio_covar_span=portfolio_covar_span,
                portfolio_target_vol=portfolio_target_vol,
                annualization_factor=annualization_factor,
                volume_costs=volume_costs,
            )
        elif tf_strategy == TFstrategy.AMERICAN:
            backtest_outputs = run_american_system(
                prices=prices,
                long_span=long_span,
                short_span=short_span,
                portfolio_covar_span=portfolio_covar_span,
                risk_multiplier=risk_multiplier,
                volume_costs=volume_costs,
            )
        elif tf_strategy == TFstrategy.TSMOM:
            backtest_outputs = run_tsmom_system(
                prices=prices, portfolio_covar_span=portfolio_covar_span, volume_costs=volume_costs
            )

        else:
            raise NotImplementedError(f"{tf_strategy}")

        if portfolio_covar_span is not None:
            key = f"span = {portfolio_covar_span: 0.0f}"
        else:
            key = 'No vol target'
        pnls[key] = backtest_outputs.portfolio_pnl_net
    pnls = pd.DataFrame.from_dict(pnls, orient='columns')
    if time_period is not None:
        pnls = time_period.locate(pnls)
    return pnls


def backtest_tsmom_grid(
    prices: pd.DataFrame,
    volume_costs: pd.DataFrame,
    benchmark_prices: pd.DataFrame,
    num_ra_returnss: List[int] = np.linspace(3, 27, 8, dtype=int),
    num_periodss: List[int] = np.linspace(3, 27, 8, dtype=int),
    vol_span: int = 33,
    vol_target: float = 0.004,
    portfolio_covar_span: Optional[int] = None,
    portfolio_target_vol: float = 0.15,
    annualization_factor: float = 260.0,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    performance of the tsmom system across the grid of period lengths and lookbacks
    """
    benchmark = benchmark_prices.columns[0]

    net_sharpes = {}
    bear_sharpes = {}
    costs = {}
    for idx1, num_periods in enumerate(num_periodss):
        pnls = {}
        costs_ = {}
        for idx2, num_ra_returns in enumerate(num_ra_returnss):
            backtest_outputs = run_tsmom_system(
                prices=prices,
                num_ra_returns=int(num_ra_returns),
                num_periods=int(num_periods),
                vol_span=vol_span,
                vol_target=vol_target,
                portfolio_covar_span=portfolio_covar_span,
                portfolio_target_vol=portfolio_target_vol,
                volume_costs=volume_costs,
                annualization_factor=annualization_factor,
            )
            key2 = f"L returns={num_ra_returns:0.0f}"
            pnls[key2] = pd.Series(backtest_outputs.portfolio_pnl_net, index=prices.index)
            costs_[key2] = pd.Series(backtest_outputs.portfolio_cost, index=prices.index)

        pnls = pd.DataFrame.from_dict(pnls, orient='columns')
        prices1 = pd.concat([benchmark_prices[benchmark], pnls], axis=1, sort=True)
        costs_ = pd.DataFrame.from_dict(costs_, orient='columns')
        ra_perf_table = qis.compute_bnb_regimes_pa_perf_table(
            prices=prices1,
            benchmark=benchmark,
            regime_classifier=regime_classifier,
            perf_params=PERF_PARAMS,
        )
        key1 = f"M periods={num_periods:0.0f}"
        net_sharpes[key1] = ra_perf_table[qis.PerfStat.SHARPE_ARITH.to_str()]
        bear_sharpes[key1] = ra_perf_table[qis.PerfStat.BEAR_SHARPE.to_str()]
        costs[key1] = annualization_factor * costs_.mean(axis=0)

    net_sharpes = pd.DataFrame.from_dict(net_sharpes, orient='index').drop(benchmark, axis=1)
    bear_sharpes = pd.DataFrame.from_dict(bear_sharpes, orient='index').drop(benchmark, axis=1)
    costs = pd.DataFrame.from_dict(costs, orient='index')
    return net_sharpes, bear_sharpes, costs


def plot_backtest(pnl, net_pnl, turnover, costs, weights):
    """
    plot the pnl, net pnl, turnover, costs, and weights of one backtest
    """
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(2, 2, figsize=(15, 12), tight_layout=True)

        pnls = pd.concat([pnl, net_pnl.rename('net')], axis=1, sort=True)
        qis.plot_prices_with_dd(prices=pnls, axs=axs[:, 0])
        qis.plot_time_series(
            df=turnover.rolling(250).sum(),
            var_format='{:,.0%}',
            title='annual turnover',
            ax=axs[0, 1],
        )
        qis.plot_time_series(
            df=costs.rolling(250).sum(), var_format='{:,.2%}', title='annual costs', ax=axs[1, 1]
        )


def plot_grid_backtest(
    prices: pd.DataFrame,
    volume_costs: pd.DataFrame,
    benchmark_prices: pd.DataFrame,
    tf_strategy: TFstrategy = TFstrategy.EUROPEAN,
) -> None:
    """
    render the grid backtest tables as figures
    """
    net_sharpes, bear_sharpes, costs = backtest_span_grid(
        prices=prices,
        volume_costs=volume_costs,
        benchmark_prices=benchmark_prices,
        tf_strategy=tf_strategy,
    )
    qis.plot_heatmap(df=net_sharpes, var_format='{:.2f}', title='Net Sharpe')
    qis.plot_heatmap(df=bear_sharpes, var_format='{:.2f}', title='Bear Sharpe')
    qis.plot_heatmap(df=costs, var_format='{:.2f}', title='Bear Sharpe')
