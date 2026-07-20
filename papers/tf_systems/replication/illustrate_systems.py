"""
illustration of different ts systems per instrument
"""
import pandas as pd
import os
import numpy as np
import qis as qis
from qis.plots.utils import align_x_limits_axs
from qis.utils.df_ops import get_first_nonnan_values
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Optional
from enum import Enum

from trendfollowing.universe import load_data
from trendfollowing.systems.backtest_utils import compute_vol_norm_returns, compute_vol_target_weight, compute_vol
from trendfollowing.systems.european import compute_tf_signal, compute_tf_strat_pnl
from trendfollowing.systems.american import run_american_on_instrument
from trendfollowing.systems.tsmom import compute_tsmom_signal_weight


def plot_european_signals_long(price: pd.Series,
                               short_span: Optional[int] = None,
                               vol_target: float = 0.15,
                               annualization_factor: float = 260
                               ) -> plt.Figure:
    returns = qis.to_returns(prices=price, is_log_returns=True)
    returns_np = returns.to_numpy()
    vol_spans = [15, 60, 240]
    long_spans = [30, 120, 480]

    vol_norm_returns = {}
    tf_signals = {}
    voltarget_weights = {}
    weights = {}
    pnl = {}
    for long_span, vol_span in zip(long_spans, vol_spans):
        vol_norm_returns[f"vol_span={vol_span:0.0f}"] = pd.Series(compute_vol_norm_returns(returns=returns_np, vol_span=vol_span),
                                                                  index=returns.index)
        tf_signals[f"long_span={long_span:0.0f}, vol_span={vol_span:0.0f}"] = pd.Series(
            compute_tf_signal(returns=returns_np,
                              long_span=long_span,
                              short_span=short_span,
                              vol_span=vol_span),
            index=returns.index)
        vt_weights, vols = compute_vol_target_weight(returns=returns_np,
                                                     vol_span=vol_span,
                                                     vol_target=vol_target,
                                                     annualization_factor=annualization_factor)
        voltarget_weights[f"long_span={long_span:0.0f}, vol_span={vol_span:0.0f}"] = pd.Series(vt_weights, index=returns.index)

        pnl_, weights_, vols_ = compute_tf_strat_pnl(returns=returns_np,
                                                     long_span=long_span,
                                                     short_span=short_span,
                                                     vol_span=vol_span,
                                                     vol_target=vol_target,
                                                     annualization_factor=annualization_factor)
        pnl[f"long_span={long_span:0.0f}, vol_span={vol_span:0.0f}"] = pd.Series(pnl_, index=returns.index)
        weights[f"long_span={long_span:0.0f}, vol_span={vol_span:0.0f}"] = pd.Series(weights_, index=returns.index)
    vol_norm_returns = pd.DataFrame.from_dict(vol_norm_returns, orient='columns')
    tf_signals = pd.DataFrame.from_dict(tf_signals, orient='columns')
    voltarget_weights = pd.DataFrame.from_dict(voltarget_weights, orient='columns')
    pnl = pd.DataFrame.from_dict(pnl, orient='columns')
    weights = pd.DataFrame.from_dict(weights, orient='columns')

    dfs = {'Volatility normalised returns': (vol_norm_returns, vol_norm_returns),
           'EWMA filter signals': (tf_signals, tf_signals),
           '15% Volatility target weights': (voltarget_weights, voltarget_weights),
           'Trend-following system weights': (weights, weights),
           ('Cumulative returns of the strategy', 'Daily returns of the strategy*sqrt(260)'): (pnl.cumsum(axis=0), np.sqrt(annualization_factor)*pnl)}
    x_limitss = [(-5.0, 5.0), (-5.0, 5.0), (0.0, 5.0), (-5.0, 5.0), (-1.0, 1.0)]
    with sns.axes_style('darkgrid'):
        fig, axs = plt.subplots(len(dfs.keys()), 2, figsize=(15, 11), tight_layout=True)
        # fig, ax = plt.subplots(1, 1, figsize=(11, 5), tight_layout=True)

        kwargs = dict(framealpha=0.90, date_format='%Y')
        for idx, (key, dfs) in enumerate(dfs.items()):
            if isinstance(key, tuple):
                title1 = f"({qis.idx_to_alphabet(idx+1)}1) {key[0]}: time series"
                title2 = f"({qis.idx_to_alphabet(idx+1)}2) {key[1]}: histogram"
                legend_stats = qis.LegendStats.LAST
            else:
                title1 = f"({qis.idx_to_alphabet(idx+1)}1) {key}: time series"
                title2 = f"({qis.idx_to_alphabet(idx+1)}2) {key}: histogram"
                legend_stats = qis.LegendStats.AVG_STD
            qis.plot_time_series(df=dfs[0], title=title1,
                                 legend_stats=legend_stats,
                                 ax=axs[idx, 0], **kwargs)
            qis.plot_histogram(df=dfs[1], title=title2,
                               legend_stats=qis.LegendStats.AVG_STD,
                               desc_table_type=qis.DescTableType.NONE,
                               x_limits=x_limitss[idx],
                               ax=axs[idx, 1], **kwargs)
        # align_x_limits_axs(axs=axs[:, 0], is_invisible_xs=True)

    return fig


def plot_european_signals_short(price: pd.Series,
                                short_span: Optional[int] = 20,
                                vol_target: float = 0.15,
                                vol_span: int = 33,
                                annualization_factor: float = 260
                                ) -> plt.Figure:
    returns = qis.to_returns(prices=price, is_log_returns=False)
    returns_np = returns.to_numpy()
    long_spans = {'fast': 30, 'medium': 125, 'slow': 250}

    tf_signals = {}
    voltarget_weights = {}
    weights = {}
    pnl = {}

    vol_norm_returns = pd.Series(compute_vol_norm_returns(returns=returns_np, vol_span=vol_span), index=returns.index, name='Vol normalised return')

    for key, long_span in long_spans.items():
        tf_signals[key] = pd.Series(compute_tf_signal(returns=returns_np,
                                                      long_span=long_span,
                                                      short_span=short_span,
                                                      vol_span=vol_span),
                                    index=returns.index)
        vt_weights, vols = compute_vol_target_weight(returns=returns_np,
                                                     vol_span=vol_span,
                                                     vol_target=vol_target,
                                                     annualization_factor=annualization_factor)
        voltarget_weights[key] = pd.Series(vt_weights, index=returns.index)

        pnl_, weights_, vols_ = compute_tf_strat_pnl(returns=returns_np,
                                                     long_span=long_span,
                                                     short_span=short_span,
                                                     vol_span=vol_span,
                                                     vol_target=vol_target,
                                                     annualization_factor=annualization_factor)
        pnl[key] = pd.Series(pnl_, index=returns.index)
        weights[key] = pd.Series(weights_, index=returns.index)
    tf_signals = pd.DataFrame.from_dict(tf_signals, orient='columns')
    voltarget_weights = pd.DataFrame.from_dict(voltarget_weights, orient='columns')
    pnl = pd.DataFrame.from_dict(pnl, orient='columns')
    weights = pd.DataFrame.from_dict(weights, orient='columns')

    dfs = {#'Volatility normalised returns': (vol_norm_returns, vol_norm_returns),
           'EWMA filter signals': (tf_signals, tf_signals),
           'Trend-following system weights': (weights, weights),
           ('Cumulative returns of the strategy', 'Daily returns of the strategy*sqrt(260)'): (pnl.cumsum(axis=0), np.sqrt(annualization_factor)*pnl)}
    x_limitss = [(-5.0, 5.0), (-5.0, 5.0), (-0.75, 0.75)]
    with sns.axes_style('darkgrid'):
        fig, axs = plt.subplots(len(dfs.keys()), 2, figsize=(16, 10), tight_layout=True)
        # fig, ax = plt.subplots(1, 1, figsize=(11, 5), tight_layout=True)

        kwargs = dict(framealpha=0.90, date_format='%Y', fontsize=14)
        for idx, (key, dfs) in enumerate(dfs.items()):
            if isinstance(key, tuple):
                title1 = f"({qis.idx_to_alphabet(idx+1)}1) {key[0]}: time series"
                title2 = f"({qis.idx_to_alphabet(idx+1)}2) {key[1]}: histogram"
                legend_stats = qis.LegendStats.LAST
            else:
                title1 = f"({qis.idx_to_alphabet(idx+1)}1) {key}: time series"
                title2 = f"({qis.idx_to_alphabet(idx+1)}2) {key}: histogram"
                legend_stats = qis.LegendStats.AVG_STD
            qis.plot_time_series(df=dfs[0], title=title1,
                                 legend_stats=legend_stats,
                                 ax=axs[idx, 0], **kwargs)
            qis.plot_histogram(df=dfs[1], title=title2,
                               legend_stats=qis.LegendStats.AVG_STD,
                               desc_table_type=qis.DescTableType.NONE,
                               x_limits=x_limitss[idx],
                               ax=axs[idx, 1], **kwargs)
        # align_x_limits_axs(axs=axs[:, 0], is_invisible_xs=True)

    return fig


def plot_american_signals(price: pd.Series,
                          annualization_factor: float = 260,
                          vol_span: int = 33,
                          long_span: int = 250,
                          short_span: int = 20,
                          weight_abs_limit: float = 10.0,
                          stop_loss_atr_multiplier: float = 5.0,
                          signal_atr_multiplier: float = 5.0,
                          risk_multiplier: float = 0.01,
                          warmup_period: int = 250
                          ):
    returns_np = qis.to_returns(price).to_numpy()
    # 1 compute volatility
    vols = np.sqrt(annualization_factor) * compute_vol(returns=returns_np, vol_span=vol_span, is_lag1=False)
    # true_range = np.power(np.pi/8.0, -5) * np.sqrt(annualization_factor) * vol
    # true_range = np.sqrt(annualization_factor) * vol
    true_range = np.abs(price.diff(1)).rolling(vol_span, min_periods=vol_span // 2).mean().to_numpy()
    np_prices = price.to_numpy()
    init_value = get_first_nonnan_values(np_prices)
    long_ewma = qis.ewm_recursion(a=np_prices, span=long_span, init_value=init_value)
    short_ewma = qis.ewm_recursion(a=np_prices, span=short_span, init_value=init_value)

    ewmas = pd.concat([pd.Series(long_ewma+signal_atr_multiplier*true_range, index=price.index, name='Slow Ewma + q*ATR'),
                       pd.Series(short_ewma, index=price.index, name='Fast Ewma'),
                       pd.Series(long_ewma - signal_atr_multiplier* true_range, index=price.index, name='Slow Ewma - q*ATR')
                       ],
                      axis=1)

    weights, stop_loss = run_american_on_instrument(price=np_prices,
                                                    long_ewma=long_ewma,
                                                    short_ewma=short_ewma,
                                                    true_range=true_range,
                                                    weight_abs_limit=weight_abs_limit,
                                                    risk_multiplier=risk_multiplier,
                                                    stop_loss_atr_multiplier=stop_loss_atr_multiplier,
                                                    signal_atr_multiplier=signal_atr_multiplier,
                                                    warmup_period=warmup_period)
    weights = pd.Series(weights, index=price.index, name='Position')

    # stop-loss
    stop_loss_long = pd.Series(np.where(weights > 0.0, stop_loss, np.nan), index=price.index, name='Long Stop-Loss').fillna(0.0)
    stop_loss_short = pd.Series(np.where(weights < 0.0, stop_loss, np.nan), index=price.index, name='Short Stop-Loss').fillna(0.0)
    prices = pd.concat([price, stop_loss_long, stop_loss_short], axis=1)

    # p&l
    instrument_pnl = weights[:-1] * returns_np[1:]
    instrument_pnl = np.append([np.nan], instrument_pnl)  # add zero row
    instrument_pnl = pd.Series(instrument_pnl, index=price.index, name='Cumulative P&L').cumsum()

    kwargs = dict(legend_stats=qis.LegendStats.NONE, fontsize=14)

    with sns.axes_style('darkgrid'):
        fig, axs = plt.subplots(3, 1, figsize=(15, 10), tight_layout=True)
        qis.plot_time_series(df=np.log(ewmas), title='(A) EWMA slow/fast filters (log-scale)',
                             var_format='{:,.2f}',
                             ax=axs[0], **kwargs)
        # qis.plot_time_series(df=prices, title='Prices',
        #                     ax=axs[1], **kwargs)
        qis.plot_time_series(df=weights, title='(B) Position size',
                             var_format='{:,.2f}',
                             ax=axs[1], **kwargs)
        qis.plot_time_series(df=instrument_pnl, title='(C) Cumulative P&L',
                             var_format='{:,.2f}',
                             ax=axs[2], **kwargs)
        align_x_limits_axs(axs=axs, is_invisible_xs=True)

    return fig


def plot_tsmom_signal_weight(price: pd.Series,
                             num_ra_returns: int = 10,
                             num_periods: int = 10,
                             vol_span: int = 33,
                             vol_target: float = 0.0435,
                             annualization_factor: float = 260.0,
                             warmup_period: Optional[int] = 250 # monthly basis
                             ) -> plt.Figure:

    returns = qis.to_returns(price, is_first_zero=False)
    weights, signals, vols = compute_tsmom_signal_weight(returns=returns.to_frame(),
                                                num_ra_returns=num_ra_returns,
                                                num_periods=num_periods,
                                                vol_span=vol_span,
                                                vol_target=vol_target,
                                                annualization_factor=annualization_factor)
    signals = signals.iloc[:, 0].rename('Signal')
    weights = weights.iloc[:, 0].rename('Position')

    instrument_pnl = weights.to_numpy()[:-1] * returns.to_numpy()[1:]
    instrument_pnl = np.append([np.nan], instrument_pnl)  # add zero row
    instrument_pnl = pd.Series(instrument_pnl, index=price.index, name='Cumulative P&L').cumsum()

    kwargs = dict(legend_stats=qis.LegendStats.NONE, fontsize=14)

    with sns.axes_style('darkgrid'):
        fig, axs = plt.subplots(3, 1, figsize=(15, 10), tight_layout=True)
        qis.plot_time_series(df=signals, title='(A) Signal = sum of signed risk-adjusted returns',
                             ax=axs[0], **kwargs)
        qis.plot_time_series(df=weights, title='(B) Position size',
                             ax=axs[1], **kwargs)
        qis.plot_time_series(df=instrument_pnl, title='(C) Cumulative P&L',
                             ax=axs[2], **kwargs)
        align_x_limits_axs(axs=axs, is_invisible_xs=True)

    return fig


class LocalTests(Enum):
    EUROPEAN_LONG = 1
    EUROPEAN_SHORT = 2
    AMERICAN = 3
    TSMOM = 4


def run_local_test(local_test: LocalTests):
    """Run local tests for development and debugging purposes.

    These are integration tests that download real data and generate reports.
    Use for quick verification during development.
    """

    local_path = os.environ.get("TF_FIGURE_PATH", qis.local_path.get_output_path())  # set TF_FIGURE_PATH to the paper figures folder

    prices, volume_costs, benchmark_prices, descriptive_df, group_order = load_data(time_period=None)

    time_period = qis.TimePeriod(start='31Dec1997', end='30Jun2026')
    prices = time_period.locate(prices)
    is_es = True
    if is_es:
        # ticker = 'NQ1 Index'
        ticker = 'ES1 Index'
    else:
        ticker = 'TY1 Comdty'

    price = prices[ticker].dropna()

    if local_test == LocalTests.EUROPEAN_LONG:
        fig = plot_european_signals_long(price=price)
        qis.save_fig(fig, file_name=f"{ticker.split(' ')[0]}_signals", local_path=local_path)

    elif local_test == LocalTests.EUROPEAN_SHORT:
        fig = plot_european_signals_short(price=price)
        qis.save_fig(fig, file_name=f"{ticker.split(' ')[0]}_short_signals", local_path=local_path)

    elif local_test == LocalTests.AMERICAN:
        fig = plot_american_signals(price=price)
        qis.save_fig(fig, file_name=f"{ticker.split(' ')[0]}_am_signal", local_path=local_path)

    elif local_test == LocalTests.TSMOM:
        fig = plot_tsmom_signal_weight(price=price)
        qis.save_fig(fig, file_name=f"{ticker.split(' ')[0]}_tsmom_signal", local_path=local_path)

    plt.show()


if __name__ == '__main__':

    run_local_test(local_test=LocalTests.EUROPEAN_SHORT)

