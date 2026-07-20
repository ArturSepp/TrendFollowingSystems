"""
figures for article
"""
import pandas as pd
import os
import numpy as np
import qis as qis
from qis.plots.utils import (add_scatter_points, align_x_limits_axs, align_y_limits_axs, set_ax_xy_labels, set_labels_frequency)
from qis.utils.df_groups import convert_df_column_to_df_by_groups
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Optional, List, Tuple
from enum import Enum
from qis import PerfStat

from trendfollowing.universe import load_data
from trendfollowing.systems.european import run_european_tf_system
from trendfollowing.systems.american import run_american_system
from trendfollowing.systems.tsmom import run_tsmom_system
from trendfollowing.backtests import (cross_backtest_portfolio_covar_span,
                                                      backtest_span_grid,
                                                      backtest_american_atr_multiplies_grid,
                                                      backtest_tsmom_grid,
                                                      TFstrategy)

PERF_PARAMS = qis.PerfParams(freq_reg='ME', freq_vol='B', freq_skewness='QE', freq_drawdown='B',
                             sharpe_convention=qis.perfstats.config.SharpeConvention.ARITHMETIC)  # eq (5.1) convention
regime_classifier = qis.BenchmarkReturnsQuantilesRegime(freq='QE', q=np.array([0.0, 0.16, 0.84, 1.0]))  # the manuscript's one-sigma 16/84 cut
regime_classifier_1Y = qis.BenchmarkReturnsQuantilesRegime(freq='YE', q=np.array([0.0, 0.16, 0.84, 1.0]))


def compute_joint_backtest_data(prices: pd.DataFrame,
                                volume_costs: pd.DataFrame,
                                portfolio_covar_span: Optional[int] = None,
                                is_net: bool = True
                                ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    e_backtest_outputs = run_european_tf_system(prices=prices,
                                                long_span=250,
                                                short_span=20,
                                                vol_span=33,
                                                vol_target=0.0035,
                                                portfolio_covar_span=portfolio_covar_span,
                                                portfolio_target_vol=0.15,
                                                volume_costs=volume_costs)

    a_backtest_outputs = run_american_system(prices=prices,
                                             long_span=250,
                                             short_span=20,
                                             vol_span=33,
                                             risk_multiplier=0.00021,
                                             stop_loss_atr_multiplier=5.0,
                                             signal_atr_multiplier=5.0,
                                             portfolio_covar_span=portfolio_covar_span,
                                             volume_costs=volume_costs)

    tsmom_backtest_outputs = run_tsmom_system(prices=prices,
                                              num_ra_returns=10,
                                              num_periods=10,
                                              vol_span=33,
                                              vol_target=0.00415,
                                              portfolio_covar_span=portfolio_covar_span,
                                              portfolio_target_vol=0.15,
                                              volume_costs=volume_costs)

    navs = pd.concat([e_backtest_outputs.portfolio_pnl_net.rename('European'),
                      a_backtest_outputs.portfolio_pnl_net.rename('American'),
                      tsmom_backtest_outputs.portfolio_pnl_net.rename('TSMOM')], axis=1)
    if is_net:
        navs = qis.compute_net_navs_ex_perf_man_fees(navs=navs,
                                man_fee=0.02,
                                perf_fee=0.2,
                                perf_fee_frequency='YE')

    turnover = pd.concat([e_backtest_outputs.portfolio_vol_turnover.rename('European'),
                          a_backtest_outputs.portfolio_vol_turnover.rename('American'),
                          tsmom_backtest_outputs.portfolio_vol_turnover.rename('TSMOM')], axis=1)

    costs = pd.concat([e_backtest_outputs.portfolio_cost.rename('European'),
                       a_backtest_outputs.portfolio_cost.rename('American'),
                       tsmom_backtest_outputs.portfolio_cost.rename('TSMOM')], axis=1)
    return navs, turnover, costs


def plot_joint_backtest(prices: pd.DataFrame,
                        volume_costs: pd.DataFrame,
                        benchmark_prices: pd.DataFrame,
                        time_period: qis.TimePeriod = None,
                        is_22_figure: bool = True,
                        is_net: bool = True
                        ) -> plt.Figure:

    navs, turnover, costs = compute_joint_backtest_data(prices=prices,
                                                        volume_costs=volume_costs,
                                                        is_net=is_net,
                                                        portfolio_covar_span=None)
    prices = pd.concat([benchmark_prices.iloc[:, -1], navs], axis=1)

    if time_period is not None:
        benchmark_prices = time_period.locate(benchmark_prices)

    report = qis.MultiAssetsReport(prices=prices,
                                   benchmark_prices=benchmark_prices.iloc[:, 0],
                                   perf_params=PERF_PARAMS,
                                   regime_classifier=regime_classifier)

    kwargs = dict(linewidth=0.5,
                  weight='normal',
                  markersize=1,
                  framealpha=0.75,
                  time_period=time_period,
                  fontsize=12,
                  x_date_freq='YE',
                  date_format='%Y',
                  perf_params=PERF_PARAMS,
                  regime_classifier=regime_classifier,
                  digits_to_show=1,
                  sharpe_digits=2
                  )
    perf_columns = [PerfStat.PA_RETURN,
                    PerfStat.VOL,
                    PerfStat.SHARPE_ARITH,  # eq (5.1): sqrt(a)*mean/std of daily excess returns
                    PerfStat.MAX_DD,
                    #PerfStat.LAST_DD,
                    PerfStat.SKEWNESS,
                    #PerfStat.ALPHA_AN,
                    PerfStat.BETA,
                    PerfStat.R2]

    with sns.axes_style("darkgrid"):
        if is_22_figure:
            fig = plt.figure(figsize=(16, 7), constrained_layout=True)
            gs = fig.add_gridspec(nrows=4, ncols=2, wspace=0.0, hspace=0.0)

            ax1 = fig.add_subplot(gs[:2, 0])
            benchmark = benchmark_prices.columns[0]
            report.plot_nav(regime_benchmark=benchmark,
                            add_benchmarks_to_navs=False,
                            is_log=False,
                            title=f"(A1) Cumulative performance",
                            perf_stats_labels=None,
                            ax=ax1,
                            **kwargs)

            ax2 = fig.add_subplot(gs[2:4, 0])
            init_value = qis.compute_masked_covar_corr(data=qis.to_returns(prices, drop_first=True).to_numpy(), is_covar=True)
            qis.plot_returns_corr_matrix_time_series(prices=prices,
                                                     y_limits=(0.0, 1.0),
                                                     span=260,
                                                     title='(B1) EWMA correlation with 1y span',
                                                     legend_loc='lower left',
                                                     init_value=init_value,
                                                     ax=ax2,
                                                     **kwargs)
            report.add_regime_shadows(ax=ax2, regime_benchmark=benchmark, data_df=benchmark_prices)

            # ra + heatmap
            report.plot_ra_perf_table(benchmark=benchmark,
                                      perf_columns=perf_columns,
                                      title=f"(A2) Risk-adjusted performance table",
                                      ax=fig.add_subplot(gs[0, 1]),
                                      **qis.update_kwargs(kwargs, dict(fontsize=10)))
            report.plot_annual_returns(ax=fig.add_subplot(gs[1, 1]),
                                       title=f"(B2) Annual returns",
                                       heatmap_freq='YE',
                                       table_fontsize=8,
                                       add_total=False,
                                       **kwargs)
            # costs
            ax5 = fig.add_subplot(gs[2:4, 1])
            costs = time_period.locate(costs.rolling(260).sum())
            qis.plot_time_series(df=costs,
                                 var_format='{:,.2%}',
                                 title='(C2) 1y rolling cost',
                                 ax=ax5,
                                 **kwargs
                                 )
            report.add_regime_shadows(ax=ax5, regime_benchmark=benchmark, data_df=benchmark_prices)

        else:
            fig = plt.figure(figsize=(14, 14), constrained_layout=True)
            # 7 figures, *6 palce holders
            gs = fig.add_gridspec(nrows=6, ncols=2, wspace=0.0, hspace=0.0)
            ax1 = fig.add_subplot(gs[:2, 0])
            benchmark = benchmark_prices.columns[0]
            report.plot_nav(regime_benchmark=benchmark,
                            perf_stats_labels=None,
                            add_benchmarks_to_navs=False,
                            is_log=True,
                            title=f"(A1) Cumulative log-performance",
                            ax=ax1,
                            **kwargs)

            ax2 = fig.add_subplot(gs[2:4, 0])
            report.plot_drawdowns(regime_benchmark=benchmark,
                                  add_benchmarks_to_navs=False,
                                  title='(B1) Running Drawdowns',
                                  ax=ax2,
                                  **kwargs)

            ax3 = fig.add_subplot(gs[4:6, 0])
            init_value = qis.compute_masked_covar_corr(data=qis.to_returns(prices, drop_first=True).to_numpy(), is_covar=True)
            qis.plot_returns_corr_matrix_time_series(prices=prices,
                                                     y_limits=(0.0, 1.0),
                                                     span=260,
                                                     title='(C1) EWMA correlation with 1y span',
                                                     legend_loc='lower left',
                                                     init_value=init_value,
                                                     ax=ax3,
                                                     **kwargs)
            report.add_regime_shadows(ax=ax3, regime_benchmark=benchmark, data_df=benchmark_prices)

            align_x_limits_axs([ax1, ax2, ax3])

            # ra + heatmap
            report.plot_ra_perf_table(benchmark=benchmark,
                                      perf_columns=perf_columns,
                                      title=f"(A2i) Risk-adjusted performance table",
                                      ax=fig.add_subplot(gs[0, 1]),
                                      **qis.update_kwargs(kwargs, dict(fontsize=10)))
            report.plot_annual_returns(ax=fig.add_subplot(gs[1, 1]),
                                       title=f"(A2ii) Annual returns",
                                       heatmap_freq='YE',
                                       table_fontsize=8,
                                       add_total=False,
                                       **kwargs)
            # turnover
            ax4 = fig.add_subplot(gs[2:4, 1])
            turnover = time_period.locate(turnover.rolling(260).sum())
            qis.plot_time_series(df=turnover,
                                 var_format='{:,.0%}',
                                 title=f'(B2) 1y rolling volatility-adjusted turnover',
                                 ax=ax4,
                                 **kwargs
                                 )
            report.add_regime_shadows(ax=ax4, regime_benchmark=benchmark, data_df=benchmark_prices)

            # costs
            ax5 = fig.add_subplot(gs[4:6, 1])
            costs = time_period.locate(costs.rolling(260).sum())
            qis.plot_time_series(df=costs,
                                 var_format='{:,.2%}',
                                 title='(C2) 1y rolling cost',
                                 ax=ax5,
                                 **kwargs
                                 )
            report.add_regime_shadows(ax=ax5, regime_benchmark=benchmark, data_df=benchmark_prices)
            align_x_limits_axs([ax4, ax5])

    return fig


def longterm_backtest(prices: pd.DataFrame,
                      volume_costs: pd.DataFrame,
                      benchmark_prices: pd.DataFrame,
                      vol_target: float = 0.0035,
                      risk_multiplier: float = 0.000255,
                      portfolio_covar_span: Optional[int] = None,
                      time_period: qis.TimePeriod = None,
                      is_22_figure: bool = True,
                      is_net: bool = True
                      ) -> plt.Figure:

    navs, turnover, costs = compute_joint_backtest_data(prices=prices,
                                                        volume_costs=volume_costs,
                                                        is_net=is_net,
                                                        portfolio_covar_span=portfolio_covar_span)

    rolling_vol, _ = qis.compute_rolling_perf_stat(prices=navs,
                                                   rolling_perf_stat=qis.RollingPerfStat.VOL,
                                                   roll_freq='B',
                                                   roll_periods=3*260)

    rolling_return, _ = qis.compute_rolling_perf_stat(prices=navs,
                                                      rolling_perf_stat=qis.RollingPerfStat.PA_RETURNS,
                                                      roll_freq='B',
                                                      roll_periods=3*260)

    rolling_sharpe, _ = qis.compute_rolling_perf_stat(prices=navs,
                                                      rolling_perf_stat=qis.RollingPerfStat.SHARPE,
                                                      roll_freq='B',
                                                      roll_periods=3*260)

    if time_period is not None:
        benchmark_prices = time_period.locate(benchmark_prices)

    report = qis.MultiAssetsReport(prices=navs,
                                   benchmark_prices=benchmark_prices.iloc[:, 0],
                                   perf_params=PERF_PARAMS,
                                   regime_classifier=regime_classifier_1Y)

    kwargs = dict(linewidth=0.5,
                  weight='normal',
                  markersize=1,
                  framealpha=0.75,
                  time_period=time_period,
                  fontsize=12,
                  x_date_freq='YE',
                  date_format='%Y',
                  perf_params=PERF_PARAMS,
                  regime_classifier=regime_classifier
                  )

    with sns.axes_style("darkgrid"):

        if is_22_figure:
            fig = plt.figure(figsize=(16, 7), constrained_layout=True)
            gs = fig.add_gridspec(nrows=2, ncols=2, wspace=0.0, hspace=0.0)
            ax1 = fig.add_subplot(gs[0, 0])
            benchmark = benchmark_prices.columns[0]
            report.plot_nav(regime_benchmark=benchmark,
                            add_benchmarks_to_navs=False,
                            is_log=True,
                            title=f"(A1) Cumulative log-performance",
                            ax=ax1,
                            **kwargs)

            ax2 = fig.add_subplot(gs[1, 0])
            qis.plot_time_series(df=rolling_vol,
                                 var_format='{:,.0%}',
                                 title='(B1) 3y rolling volatility',
                                 ax=ax2,
                                 **kwargs
                                 )
            report.add_regime_shadows(ax=ax2, regime_benchmark=benchmark, data_df=benchmark_prices)

            align_x_limits_axs([ax1, ax2], is_invisible_xs=True)
            set_labels_frequency(ax=ax2, labels_frequency=4)

            ax4 = fig.add_subplot(gs[0, 1])
            qis.plot_time_series(df=rolling_return,
                                 var_format='{:,.0%}',
                                 title='(A2) 3y rolling p.a. return',
                                 ax=ax4,
                                 **kwargs
                                 )
            report.add_regime_shadows(ax=ax4, regime_benchmark=benchmark, data_df=benchmark_prices)

            ax5 = fig.add_subplot(gs[1, 1])
            qis.plot_time_series(df=rolling_sharpe,
                                 var_format='{:,.2f}',
                                 title='(B2) 3y rolling Sharpe',
                                 ax=ax5,
                                 **kwargs
                                 )
            report.add_regime_shadows(ax=ax5, regime_benchmark=benchmark, data_df=benchmark_prices)
            align_x_limits_axs([ax4, ax5], is_invisible_xs=True)
            set_labels_frequency(ax=ax5, labels_frequency=4)

        else:

            fig = plt.figure(figsize=(14, 14), constrained_layout=True)
            # 7 figures, *6 palce holders
            gs = fig.add_gridspec(nrows=6, ncols=2, wspace=0.0, hspace=0.0)
            ax1 = fig.add_subplot(gs[:2, 0])
            benchmark = benchmark_prices.columns[0]
            report.plot_nav(regime_benchmark=benchmark,
                            add_benchmarks_to_navs=False,
                            is_log=True,
                            title=f"(A1) Cumulative log-performance",
                            ax=ax1,
                            **kwargs)

            ax2 = fig.add_subplot(gs[2:4, 0])
            report.plot_drawdowns(regime_benchmark=benchmark,
                                  add_benchmarks_to_navs=False,
                                  title='(B1) Running Drawdowns',
                                  ax=ax2,
                                  **kwargs)

            ax3 = fig.add_subplot(gs[4:6, 0])
            qis.plot_time_series(df=rolling_vol,
                                 var_format='{:,.0%}',
                                 title='(C1) 3y rolling volatility',
                                 ax=ax3,
                                 **kwargs
                                 )
            report.add_regime_shadows(ax=ax3, regime_benchmark=benchmark, data_df=benchmark_prices)

            align_x_limits_axs([ax1, ax2, ax3], is_invisible_xs=True)
            set_labels_frequency(ax=ax3, labels_frequency=4)

            ax4 = fig.add_subplot(gs[:2, 1])
            qis.plot_time_series(df=rolling_return,
                                 var_format='{:,.0%}',
                                 title='(A2) 3y rolling p.a. return',
                                 ax=ax4,
                                 **kwargs
                                 )
            report.add_regime_shadows(ax=ax4, regime_benchmark=benchmark, data_df=benchmark_prices)

            ax5 = fig.add_subplot(gs[2:4, 1])
            qis.plot_time_series(df=rolling_sharpe,
                                 var_format='{:,.2f}',
                                 title='(B2) 3y rolling Sharpe',
                                 ax=ax5,
                                 **kwargs
                                 )
            report.add_regime_shadows(ax=ax5, regime_benchmark=benchmark, data_df=benchmark_prices)

            # costs
            ax6 = fig.add_subplot(gs[4:6, 1])
            costs = time_period.locate(costs.rolling(260).sum())
            qis.plot_time_series(df=costs,
                                 var_format='{:,.2%}',
                                 title='(C2) 1y rolling cost',
                                 ax=ax6,
                                 **kwargs
                                 )
            report.add_regime_shadows(ax=ax6, regime_benchmark=benchmark, data_df=benchmark_prices)
            align_x_limits_axs([ax4, ax5, ax6], is_invisible_xs=True)
            set_labels_frequency(ax=ax6, labels_frequency=4)

    return fig


def plot_sharpe_for_portfolio_vol_target(prices: pd.DataFrame,
                                         volume_costs: pd.DataFrame,
                                         vol_target: float = 0.0035,
                                         risk_multiplier: float = 0.000255,
                                         is_net: bool = True,
                                         time_period: qis.TimePeriod = None,
                                         **kwargs
                                         ) -> plt.Figure:
    e_pnls0 = cross_backtest_portfolio_covar_span(prices=prices, tf_strategy=TFstrategy.EUROPEAN,
                                                  volume_costs=volume_costs,
                                                  vol_target=vol_target,
                                                  risk_multiplier=risk_multiplier,
                                                  time_period=time_period,
                                                  **kwargs)
    if is_net:
        e_pnls0 = qis.compute_net_navs_ex_perf_man_fees(navs=e_pnls0, man_fee=0.02, perf_fee=0.2, perf_fee_frequency='YE')

    a_pnls0 = cross_backtest_portfolio_covar_span(prices=prices, tf_strategy=TFstrategy.AMERICAN,
                                                  volume_costs=volume_costs,
                                                  vol_target=vol_target,
                                                  risk_multiplier=risk_multiplier,
                                                  time_period=time_period,
                                                  **kwargs)
    if is_net:
        a_pnls0 = qis.compute_net_navs_ex_perf_man_fees(navs=a_pnls0, man_fee=0.02, perf_fee=0.2, perf_fee_frequency='YE')

    tsmom_pnls0 = cross_backtest_portfolio_covar_span(prices=prices, tf_strategy=TFstrategy.TSMOM,
                                                      volume_costs=volume_costs,
                                                      vol_target=vol_target,
                                                      risk_multiplier=risk_multiplier,
                                                      time_period=time_period,
                                                      **kwargs)
    if is_net:
        tsmom_pnls0 = qis.compute_net_navs_ex_perf_man_fees(navs=tsmom_pnls0, man_fee=0.02, perf_fee=0.2, perf_fee_frequency='YE')

    # ra_perf_table = qis.compute_ra_perf_table(prices=prices, perf_params=perf_params)
    fig_kwargs = qis.update_kwargs(kwargs, dict(add_total_bar=False, fontsize=12,
                                                perf_column=qis.PerfStat.SHARPE_RF0))
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(1, 3, figsize=(14, 6), tight_layout=True)
        qis.plot_ra_perf_bars(prices=e_pnls0,
                              title=f"European TF",
                              ax=axs[0],
                              **fig_kwargs)
        qis.plot_ra_perf_bars(prices=a_pnls0,
                              title=f"American TF",
                              ax=axs[1],
                              **fig_kwargs)
        qis.plot_ra_perf_bars(prices=tsmom_pnls0,
                              title=f"TSMOM TF",
                              ax=axs[2],
                              **fig_kwargs)
        set_ax_xy_labels(ax=axs[0], xlabel='Sharpe', ylabel=None, **fig_kwargs)
        set_ax_xy_labels(ax=axs[1], xlabel='Sharpe', ylabel=None, **fig_kwargs)
        set_ax_xy_labels(ax=axs[2], xlabel='Sharpe', ylabel=None, **fig_kwargs)

    return fig


def plot_sharpe_skeweness(prices: pd.DataFrame,
                          volume_costs: pd.DataFrame,
                          benchmark_prices: pd.DataFrame,
                          is_bear_sharpe: bool = False,
                          vol_target: float = 0.0035,
                          risk_multiplier: float = 0.000255,
                          is_net: bool = True,
                          time_period: qis.TimePeriod = None,
                          portfolio_covar_spans: List[Optional[int]] = (None, 30, 60, 90, 130, 260, 520),
                          freq: str = 'QE',
                          **kwargs
                          ) -> plt.Figure:
    e_pnls0 = cross_backtest_portfolio_covar_span(prices=prices, tf_strategy=TFstrategy.EUROPEAN,
                                                  volume_costs=volume_costs,
                                                  vol_target=vol_target,
                                                  risk_multiplier=risk_multiplier,
                                                  time_period=time_period,
                                                  portfolio_covar_spans=portfolio_covar_spans,
                                                  **kwargs)
    if is_net:
        e_pnls0 = qis.compute_net_navs_ex_perf_man_fees(navs=e_pnls0, man_fee=0.02, perf_fee=0.2, perf_fee_frequency='YE')

    a_pnls0 = cross_backtest_portfolio_covar_span(prices=prices, tf_strategy=TFstrategy.AMERICAN,
                                                  volume_costs=volume_costs,
                                                  vol_target=vol_target,
                                                  risk_multiplier=risk_multiplier,
                                                  long_span=250,
                                                  short_span=20,
                                                  time_period=time_period,
                                                  portfolio_covar_spans=portfolio_covar_spans,
                                                  **kwargs)
    if is_net:
        a_pnls0 = qis.compute_net_navs_ex_perf_man_fees(navs=a_pnls0, man_fee=0.02, perf_fee=0.2, perf_fee_frequency='YE')

    tsmom_pnls0 = cross_backtest_portfolio_covar_span(prices=prices, tf_strategy=TFstrategy.TSMOM,
                                                      volume_costs=volume_costs,
                                                      vol_target=vol_target,
                                                      risk_multiplier=risk_multiplier,
                                                      time_period=time_period,
                                                      portfolio_covar_spans=portfolio_covar_spans,
                                                      **kwargs)
    if is_net:
        tsmom_pnls0 = qis.compute_net_navs_ex_perf_man_fees(navs=tsmom_pnls0, man_fee=0.02, perf_fee=0.2, perf_fee_frequency='YE')

    regime_classifier = qis.BenchmarkReturnsQuantilesRegime(freq=freq)
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(1, 3, figsize=(16, 6), tight_layout=True)

        if is_bear_sharpe:
            y_var = PerfStat.BEAR_SHARPE
        else:
            y_var = PerfStat.SKEWNESS

        kwargs = dict(perf_params=PERF_PARAMS,
                      regime_classifier=regime_classifier,
                      x_var=qis.PerfStat.SHARPE_RF0,
                      drop_benchmark=True,
                      y_var=y_var,
                      full_sample_order=1,
                      order=None,
                      ci=None,
                      full_sample_label='',
                      fontsize=12)
        pnls = {'European': e_pnls0, 'American': a_pnls0, 'TSMOM': tsmom_pnls0}

        for idx, (key, prices) in enumerate(pnls.items()):
            annotation_labels = list(prices.columns)
            colors = ['blue']
            annotation_colors = ['red'] + ['blue']*(len(prices.columns)-1)

            if is_bear_sharpe:
                benchmark_price = benchmark_prices.iloc[:, 0]
                benchmark = benchmark_prices.columns[0]
            else:
                benchmark_price = None
                benchmark = None
            qis.plot_ra_perf_scatter(prices=prices,
                                     benchmark=benchmark,
                                     benchmark_price=benchmark_price,
                                     annotation_labels=annotation_labels,
                                     annotation_colors=annotation_colors,
                                     colors=colors,
                                     title=f"({qis.idx_to_alphabet(idx+1)}) {key}",
                                     ax=axs[idx],
                                     **kwargs)
            # add_scatter_points()

        # align_y_limits_axs(axs)

    return fig


def plot_regime_diversification(prices: pd.DataFrame,
                                volume_costs: pd.DataFrame,
                                benchmark_prices: pd.DataFrame,
                                time_period: qis.TimePeriod = None,
                                is_net: bool = True
                                ) -> plt.Figure:
    navs, turnover, costs = compute_joint_backtest_data(prices=prices,
                                                        volume_costs=volume_costs,
                                                        is_net=is_net)
    benchmark = benchmark_prices.columns[0]
    prices = pd.concat([benchmark_prices, navs], axis=1)

    if time_period is not None:
        benchmark_prices = time_period.locate(benchmark_prices)

    report = qis.MultiAssetsReport(prices=prices,
                                   benchmark_prices=benchmark_prices[benchmark],
                                   perf_params=PERF_PARAMS,
                                   regime_classifier=regime_classifier)

    kwargs = dict(linewidth=0.5,
                  weight='normal',
                  markersize=1,
                  framealpha=0.75,
                  time_period=time_period,
                  fontsize=12,
                  x_date_freq='YE',
                  date_format='%Y',
                  perf_params=PERF_PARAMS,
                  regime_classifier=regime_classifier,
                  digits_to_show=1,
                  sharpe_digits=2
                  )

    with sns.axes_style("darkgrid"):

        fig, axs = plt.subplots(1, 2, figsize=(16, 7), tight_layout=True)

        report.plot_nav(regime_benchmark=benchmark,
                        add_benchmarks_to_navs=True,
                        is_log=True,
                        perf_stats_labels=[PerfStat.SHARPE_RF0],
                        title=f"(A) Cumulative log-performance with regimes in the background",
                        ax=axs[0],
                        **kwargs)

        report.plot_regime_data(benchmark=benchmark,
                                title=f"(B) Regime Conditional Sharpe ratios",
                                drop_benchmark=False,
                                is_top_totals=False,
                                ax=axs[1],
                                **kwargs)
    return fig


def plot_smart_diversification(prices: pd.DataFrame,
                               volume_costs: pd.DataFrame,
                               benchmark_prices: pd.DataFrame,
                               portfolio_covar_span: Optional[int] = None,
                               is_net: bool = True,
                               time_period: qis.TimePeriod = None,
                               is_principal_weight_fixed: bool = False
                               ) -> plt.Figure:

    navs, turnover, costs = compute_joint_backtest_data(prices=prices,
                                                        volume_costs=volume_costs,
                                                        portfolio_covar_span=portfolio_covar_span,
                                                        is_net=is_net)

    balanced = benchmark_prices.iloc[:, 0]

    sd_report = qis.SmartDiversificationReport(principal_nav=balanced,
                                               overlay_navs=navs,
                                               perf_params=PERF_PARAMS,
                                               regime_classifier=regime_classifier
                                               )

    kwargs = dict(linewidth=0.5,
                  weight='normal',
                  markersize=1,
                  framealpha=0.75,
                  time_period=time_period,
                  fontsize=14,
                  x_date_freq='YE',
                  date_format='%Y',
                  perf_params=PERF_PARAMS,
                  regime_classifier=regime_classifier
                  )

    with sns.axes_style('darkgrid'):
        fig, ax = plt.subplots(1, 1, figsize=(16, 7), tight_layout=True)
        sd_report.plot_smart_diversification_curve(x_var=PerfStat.BEAR_SHARPE,
                                                   y_var=PerfStat.SHARPE_RF0,
                                                   title='Total Sharpe vs Bear-Sharpe',
                                                   is_principal_weight_fixed=is_principal_weight_fixed,
                                                   ax=ax,
                                                   **kwargs)

    return fig


def plot_backtest_overlay(prices: pd.DataFrame,
                          volume_costs: pd.DataFrame,
                          benchmark_prices: pd.DataFrame,
                          portfolio_covar_span: Optional[int] = None,
                          is_net: bool = True,
                          time_period: qis.TimePeriod = None
                          ) -> plt.Figure:

    navs, turnover, costs = compute_joint_backtest_data(prices=prices,
                                                        volume_costs=volume_costs,
                                                        portfolio_covar_span=portfolio_covar_span,
                                                        is_net=is_net)

    overlay_weight = np.linspace(0.0, 1.0, 5)
    balanced = benchmark_prices.iloc[:, 0]
    kwargs = dict(linewidth=0.5,
                  weight='normal',
                  markersize=1,
                  framealpha=0.75,
                  time_period=time_period,
                  fontsize=12,
                  x_date_freq='YE',
                  date_format='%Y',
                  perf_params=PERF_PARAMS,
                  regime_classifier=regime_classifier
                  )

    with sns.axes_style('darkgrid'):
        fig, axs = plt.subplots(1, len(navs.columns), figsize=(16, 6), tight_layout=True)

        for idx, column in enumerate(navs.columns):
            e_prices = pd.concat([balanced, navs[column]], axis=1)
            e_overlays = {}
            for ov in overlay_weight:
                ticker = f"{1-ov:0.0%}/{ov:0.0%} Balanced/{column} TF"
                e_overlays[ticker] = qis.backtest_model_portfolio(prices=e_prices, weights=np.array([1.0-ov, ov]),
                                                                  rebalancing_freq='QE').get_portfolio_nav()
            e_overlays = pd.DataFrame.from_dict(e_overlays, orient='columns')

            if time_period is not None:
                e_overlays = time_period.locate(e_overlays)

            e_report = qis.MultiAssetsReport(prices=e_overlays,
                                             benchmark_prices=balanced,
                                             perf_params=PERF_PARAMS,
                                             regime_classifier=regime_classifier)
            e_report.plot_regime_data(benchmark=str(balanced.name),
                                      title=f"{qis.idx_to_alphabet(idx+1)} 60/40 Balanced with {column} TF",
                                      drop_benchmark=True,
                                      is_top_totals=False,
                                      add_bar_values=False,
                                      ax=axs[idx],
                                      **kwargs)
    return fig


def plot_grid_backtest_table(net_sharpes: pd.DataFrame, bear_sharpes: pd.DataFrame, costs: pd.DataFrame,
                             row_title: Optional[str] = None  # system name shown as the row supertitle
                             ) -> plt.Figure:
    fig, axs = plt.subplots(1, 3, figsize=(15, 5.2), tight_layout=True)
    kwargs = dict(fontsize=10)
    qis.plot_heatmap(df=net_sharpes, var_format='{:.2f}', title='(A) Sharpe ratio', ax=axs[0], **kwargs)
    qis.plot_heatmap(df=bear_sharpes, var_format='{:.2f}', title='(B) Bear Sharpe ratio', ax=axs[1], **kwargs)
    qis.plot_heatmap(df=costs, var_format='{:.1%}', title='(C) Annualised avg cost', ax=axs[2], **kwargs)
    if row_title is not None:
        qis.set_suptitle(fig, title=row_title)
    return fig


def compute_sharpe_ratios(prices: pd.DataFrame,
                          volume_costs: pd.DataFrame,
                          portfolio_covar_span: Optional[int] = None,
                          is_net: bool = True
                          ) -> None:

    e_backtest_outputs = run_european_tf_system(prices=prices,
                                                long_span=250,
                                                short_span=20,
                                                vol_span=33,
                                                vol_target=0.0035,
                                                portfolio_covar_span=portfolio_covar_span,
                                                portfolio_target_vol=0.15,
                                                volume_costs=volume_costs)
    instrument_pnl = e_backtest_outputs.instrument_pnl_net
    instrument_navs = qis.returns_to_nav(returns=instrument_pnl)
    prices_at_navs = prices.where(instrument_navs.isna()==False, other=np.nan)
    instrument_navs_sharpe = log_sharpes(prices=instrument_navs).rename('TF marginal')
    prices_sharpe = log_sharpes(prices_at_navs).rename('Delta1')
    df = pd.concat([prices_sharpe, instrument_navs_sharpe], axis=1)
    qis.plot_scatter(df=df, fit_intercept=False)


def log_sharpes(prices: pd.DataFrame):
    returns = qis.to_returns(prices=prices, is_log_returns=False).mean(axis=0)
    vols = qis.to_returns(prices=prices, is_log_returns=True).std(axis=0)
    return np.sqrt(260) * returns.divide(vols)


class LocalTests(Enum):
    UNIVERSE_TABLE = 2
    COST_ASSUMPTIONS = 13
    GRID_BACKTEST = 3
    JOINT_BACKTEST_CG = 4
    LONG_TERM_BACKTEST = 5
    SHARPE_VOL_TARGET = 7
    SKEWENESS_VOL_TARGET = 8
    REGIME_DIVERSIFICATION = 9
    PLOT_SMART_DIVERSIFICATION = 10
    TF_OVERLAY = 11
    JOINT_INSTRUMENT_SHARPE_VS_TF_SHARPE = 12


def run_local_test(local_test: LocalTests):
    """Run local tests for development and debugging purposes.

    These are integration tests that download real data and generate reports.
    Use for quick verification during development.
    """

    local_path = os.environ.get("TF_FIGURE_PATH", qis.local_path.get_output_path())  # set TF_FIGURE_PATH to the paper figures folder

    prices, volume_costs, benchmark_prices, descriptive_df, group_order = load_data(time_period=None)

    end_date = '30Jun2026'
    time_period_2000 = qis.TimePeriod(start='31Dec1999', end=end_date)

    if local_test == LocalTests.UNIVERSE_TABLE:
        #print(group_data)
        df = convert_df_column_to_df_by_groups(df=descriptive_df,
                                                   group_data=descriptive_df['group_data'],
                                                   column='names',
                                                   group_order=group_order)
        df.index = [x+1 for x in df.index]
        fig, ax = plt.subplots(1, 1, figsize=(15, 5), tight_layout=True)
        qis.plot_df_table(df=df.replace({np.nan: ''}), ax=ax)
        qis.save_fig(fig, file_name=f"universe_table", local_path=local_path)

    elif local_test == LocalTests.COST_ASSUMPTIONS:
        from trendfollowing.universe import COST_STRUCTURE
        periods = {'Until Dec 1992': list(COST_STRUCTURE.values())[0],
                   'Jan 1993 to Dec 2002': list(COST_STRUCTURE.values())[1],
                   'From Jan 2003': list(COST_STRUCTURE.values())[2]}
        df = pd.DataFrame({name: pd.Series(costs) for name, costs in periods.items()}).loc[group_order, :]
        df = df.map(lambda x: f"{10000.0 * x:0.0f}bp")
        fig, ax = plt.subplots(1, 1, figsize=(7, 3), tight_layout=True)
        qis.plot_df_table(df=df, ax=ax)
        qis.save_fig(fig, file_name=f"cost_assumptions", local_path=local_path)

    elif local_test == LocalTests.GRID_BACKTEST:
        time_period = qis.TimePeriod(start='31Dec1997', end=end_date)
        prices = time_period.locate(prices)
        volume_costs = time_period.locate(volume_costs)

        # the three paper grids are generated sequentially with their exhibit parameters
        net_sharpes, bear_sharpes, costs = backtest_span_grid(prices=prices,
                                                              volume_costs=volume_costs,
                                                              benchmark_prices=benchmark_prices,
                                                              long_spans=[20, 50, 75, 100, 175, 250, 375, 500],
                                                              short_spans=[5, 10, 20, 30, 40, 50, 75, 100],
                                                              vol_target=0.0035,
                                                              portfolio_covar_span=None,
                                                              tf_strategy=TFstrategy.EUROPEAN)
        fig = plot_grid_backtest_table(net_sharpes=net_sharpes, bear_sharpes=bear_sharpes, costs=costs, row_title='European')
        qis.save_fig(fig, file_name=f"european_grid", local_path=local_path)

        net_sharpes, bear_sharpes, costs = backtest_span_grid(prices=prices,
                                                              volume_costs=volume_costs,
                                                              benchmark_prices=benchmark_prices,
                                                              long_spans=[20, 50, 75, 100, 175, 250, 375, 500],
                                                              short_spans=[5, 10, 20, 30, 40, 50, 75, 100],
                                                              vol_target=0.0035,
                                                              risk_multiplier=0.0004,
                                                              portfolio_covar_span=None,
                                                              tf_strategy=TFstrategy.AMERICAN)
        fig = plot_grid_backtest_table(net_sharpes=net_sharpes, bear_sharpes=bear_sharpes, costs=costs, row_title='American')
        qis.save_fig(fig, file_name=f"american_grid_spans", local_path=local_path)

        net_sharpes, bear_sharpes, costs = backtest_tsmom_grid(prices=prices,
                                                               volume_costs=volume_costs,
                                                               portfolio_covar_span=None,
                                                               benchmark_prices=benchmark_prices)
        fig = plot_grid_backtest_table(net_sharpes=net_sharpes, bear_sharpes=bear_sharpes, costs=costs, row_title='TSMOM')
        qis.save_fig(fig, file_name=f"tsmom_grid", local_path=local_path)

    elif local_test == LocalTests.JOINT_BACKTEST_CG:
        is_22_figure = False
        fig = plot_joint_backtest(prices=prices,
                                  volume_costs=volume_costs,
                                  benchmark_prices=benchmark_prices,
                                  time_period=time_period_2000,
                                  is_22_figure=is_22_figure,
                                  is_net=True)
        if is_22_figure:
            qis.save_fig(fig, file_name=f"tf_sg_backtest", local_path=local_path)
        else:
            qis.save_fig(fig, file_name=f"tf_sg_backtest_paper", local_path=local_path)

    elif local_test == LocalTests.LONG_TERM_BACKTEST:
        # both paper variants: unit notional and portfolio vol targeting
        fig = longterm_backtest(prices=prices,
                                volume_costs=volume_costs,
                                benchmark_prices=benchmark_prices,
                                portfolio_covar_span=None,
                                time_period=qis.TimePeriod(start='01Jan1965', end=end_date))
        qis.save_fig(fig, file_name=f"lt_backtest", local_path=local_path)
        fig = longterm_backtest(prices=prices,
                                volume_costs=volume_costs,
                                benchmark_prices=benchmark_prices,
                                portfolio_covar_span=100,
                                time_period=qis.TimePeriod(start='01Jan1965', end=end_date))
        qis.save_fig(fig, file_name=f"lt_backtest_vol_target", local_path=local_path)

    elif local_test == LocalTests.SHARPE_VOL_TARGET:
        fig = plot_sharpe_for_portfolio_vol_target(prices=prices,
                                                   volume_costs=volume_costs,
                                                   long_span=250,
                                                   short_span=20,
                                                   vol_span=33,
                                                   vol_target=0.0035,
                                                   risk_multiplier=0.000255,
                                                   portfolio_covar_span=250,
                                                   portfolio_target_vol=0.15,
                                                   time_period=time_period_2000)
        qis.save_fig(fig, file_name=f"sharpe_vol_target", local_path=local_path)

    elif local_test == LocalTests.SKEWENESS_VOL_TARGET:
        # sharpe_skeweness is the paper exhibit; the bear-sharpe variant supports the companion paper
        for is_bear_sharpe in [False, True]:
            fig = plot_sharpe_skeweness(prices=prices,
                                        volume_costs=volume_costs,
                                        benchmark_prices=benchmark_prices,
                                        is_bear_sharpe=is_bear_sharpe,
                                        vol_target=0.0035,
                                        risk_multiplier=0.000245,
                                        portfolio_target_vol=0.15,
                                        freq='QE',
                                        time_period=time_period_2000)
            file_name = f"sharpe_bearsharpe" if is_bear_sharpe else f"sharpe_skeweness"
            qis.save_fig(fig, file_name=file_name, local_path=local_path)

    elif local_test == LocalTests.REGIME_DIVERSIFICATION:
        fig = plot_regime_diversification(prices=prices,
                                          volume_costs=volume_costs,
                                          benchmark_prices=benchmark_prices,
                                          time_period=time_period_2000,
                                          is_net=True)
        qis.save_fig(fig, file_name=f"regime_diversification", local_path=local_path)

    elif local_test == LocalTests.PLOT_SMART_DIVERSIFICATION:
        fig = plot_smart_diversification(prices=prices,
                                         volume_costs=volume_costs,
                                         benchmark_prices=benchmark_prices,
                                         time_period=time_period_2000,
                                         is_net=True,
                                         is_principal_weight_fixed=True)
        # qis.save_fig(fig, file_name=f"smart_diversification", local_path=local_path)

    elif local_test == LocalTests.TF_OVERLAY:
        fig = plot_backtest_overlay(prices=prices,
                                    volume_costs=volume_costs,
                                    benchmark_prices=benchmark_prices,
                                    portfolio_covar_span=None,
                                    time_period=time_period_2000)
        # qis.save_fig(fig, file_name=f"lt_backtest_overlay", local_path=local_path)

    elif local_test == LocalTests.JOINT_INSTRUMENT_SHARPE_VS_TF_SHARPE:
        compute_sharpe_ratios(prices=prices,
                              volume_costs=volume_costs)

    plt.show()


if __name__ == '__main__':

    run_local_test(local_test=LocalTests.PLOT_SMART_DIVERSIFICATION)
