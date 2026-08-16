"""
screener for TF signal
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
import os
import numpy as np
import pandas as pd
import qis as qis
from qis.plots.utils import get_n_colors, set_legend
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import norm
from typing import List
from enum import Enum

from trendfollowing.systems.american import run_american_system
from trendfollowing.systems.european import run_european_tf_system, compute_tf_signal
from trendfollowing.systems.tsmom import run_tsmom_system
from trendfollowing.systems.backtest_utils import compute_vol, BacktestOutputs, compute_vol_target_weight


def run_european_screener(prices: pd.DataFrame,
                          group_data: pd.Series,
                          group_order: List[str],
                          long_span: int = 250,
                          short_span: int = 20,
                          vol_span: int = 33,
                          window: int = 10
                          ):
    """
    backtest_outputs = run_european_tf_system(prices=prices,
                                              long_span=long_span,
                                              short_span=short_span,
                                              vol_span=vol_span,
                                              vol_target=0.05,
                                              portfolio_covar_span=None,
                                              volume_costs=volume_costs)
    """
    backtest_outputs = run_american_system(prices=prices,
                                           long_span=long_span,
                                           short_span=short_span,
                                           vol_span=vol_span,
                                           stop_loss_atr_multiplier=10.0,
                                           signal_atr_multiplier=5.0,
                                           portfolio_covar_span=None,
                                           volume_costs=0.0)
    am_position = np.sign(backtest_outputs.weights)

    returns = qis.to_returns(prices, is_log_returns=True, is_first_zero=False)

    next_periods = pd.date_range(start=returns.index[-1] + pd.DateOffset(days=1), periods=window, freq='1d')
    returns_next_periods = pd.concat([returns, pd.DataFrame(0.0, columns=returns.columns, index=next_periods)], axis=0)
    returns_next_periods = returns_next_periods.iloc[window:, :] # align shape

    returns_np = returns.to_numpy()
    returns_next_periods_np = returns_next_periods.to_numpy()
    vols_current = compute_vol(returns=returns_np, vol_span=vol_span, is_lag1=True)
    vols_predicted = compute_vol(returns=returns_np, vol_span=vol_span, is_lag1=True)

    vol_norm_returns_current = returns_np / vols_current
    vol_norm_returns_predicted = returns_next_periods_np / vols_current

    signal_current = compute_tf_signal(returns=returns_np,
                                       vol_norm_returns=vol_norm_returns_current,
                                       long_span=long_span,
                                       short_span=short_span,
                                       vol_span=vol_span)
    signal_predicted = compute_tf_signal(returns=returns_next_periods_np,
                                         vol_norm_returns=vol_norm_returns_predicted,
                                         long_span=long_span,
                                         short_span=short_span,
                                         vol_span=vol_span)
    df = pd.DataFrame(signal_current, columns=returns.columns, index=returns.index)
    df_predicted = pd.DataFrame(signal_predicted, columns=returns_next_periods.columns, index=returns_next_periods.index)

    # df = backtest_outputs.signals
    dfs = qis.split_df_by_groups(df=df, group_data=group_data, group_order=group_order)
    dfs_predicted = qis.split_df_by_groups(df=df_predicted, group_data=group_data, group_order=group_order)

    joint = []
    colors = get_n_colors(n=len(dfs.keys()))
    all_colors = []
    for idx, (key, df) in enumerate(dfs.items()):
        df_1 = df.iloc[-1, :].sort_values(ascending=False)
        joint.append(df_1)
        all_colors.append([colors[idx]]*len(df_1.index))
    joint = pd.concat(joint)

    joint_predicted = []
    for idx, (key, df) in enumerate(dfs_predicted.items()):
        df_next_1 = df.iloc[-1, :].sort_values(ascending=False)
        joint_predicted.append(df_next_1)
    joint_predicted = pd.concat(joint_predicted)

    joint = joint.apply(lambda x: 2.0*norm.cdf(x)-1.0)
    joint_predicted = joint_predicted.apply(lambda x: 2.0*norm.cdf(x)-1.0)
    all_colors = qis.to_flat_list(all_colors)

    with sns.axes_style("darkgrid"):
        fig, ax = plt.subplots(1, 1, figsize=(8, 16), tight_layout=True)

        qis.plot_vbars(df=joint,
                       colors=all_colors,
                       totals=joint_predicted.loc[joint.index].to_list(),
                       fontsize=8,
                       axvline_color=None,
                       var_format='{:.2f}',
                       x_limits=(-1.0, 1.0),
                       bbox_to_anchor=None,
                       add_bar_values=False,
                       add_total_bar=True,
                       total_bar_linestyle='dotted',
                       total_bar_linewidth=3,
                       is_category_names_colors=False,
                       xlabel='Signal',
                       ax=ax)
        set_legend(ax=ax,
                       labels=list(dfs.keys()),
                       colors=colors,
                       legend_loc='upper left',
                       fontsize=10,
                       reverse_columns=False,
                       framealpha=0.9,
                       bbox_to_anchor=None)
        # add american
        am_position_t = am_position.iloc[-1, :].loc[joint.index].to_list()
        for idx, total in enumerate(am_position_t):
            # ax.vlines(x=total, ymin=idx-0.25, ymax=idx+0.25, marker='o', linestyle='None', color='red', linewidth=3, )
            ax.scatter(x=0.995*total, y=idx, marker='o', color='red', s=3, zorder=10)
        ax.margins(x=0.01)

        for idx, t in enumerate(ax.yaxis.get_ticklabels()):
            t.set_color(all_colors[idx])
    return fig



class LocalTests(Enum):
    """
    runnable example cases
    """
    TF_UNIVERSE = 1
    SMALL_UNIVERSE = 2


def run_local_test(local_test: LocalTests):
    """Run local tests for development and debugging purposes.

    These are integration tests that download real data and generate reports.
    Use for quick verification during development.
    """

    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    local_path = os.environ.get("TF_FIGURE_PATH", qis.local_path.get_output_path())  # set TF_FIGURE_PATH to the paper figures folder

    if local_test == LocalTests.TF_UNIVERSE:
        time_period = qis.TimePeriod(start='31Dec1998', end=None)
        from trendfollowing.universe import load_data
        prices, volume_costs, benchmark_prices, group_data, group_order = load_data(time_period=time_period)

        prices = prices.rename(group_data['names'].to_dict(), axis=1)
        group_data = group_data.rename(group_data['names'].to_dict(), axis=0)['group_data']
        fig = run_european_screener(prices=prices, group_data=group_data, group_order=group_order)
        qis.save_fig(fig, file_name='tf_signal', local_path=qis.get_output_path())

    elif local_test == LocalTests.SMALL_UNIVERSE:
        from bbg_fetch import fetch_field_timeseries_per_tickers
        time_period = qis.TimePeriod(start='31Dec1998', end=None)

        tickers = {'SPX Index': 'S&P500',
                   'DAX Index': 'DAX',
                   'TY1 Comdty': 'UST',
                   'RX1 Comdty': 'Bunds',
                   'LGCPTRUH Index': 'IG',
                   'LG30TRUH Index': 'HY',
                   'EUR BGN Curncy': 'EUR',
                   'JPY BGN Curncy': 'JPY'}
        group_data = pd.Series(['EQ', 'EQ', 'FI', 'FI', 'Credit', 'Credit', 'FX', 'FX'], index=list(tickers.values()))
        prices = fetch_field_timeseries_per_tickers(tickers=tickers, freq='B', field='PX_LAST').ffill()
        prices = time_period.locate(prices)

        fig = run_european_screener(prices=prices, group_data=group_data, group_order=['EQ', 'FI', 'Credit', 'FX'])
        qis.save_fig(fig, file_name='tf_signal', local_path=qis.get_output_path())


    plt.show()


if __name__ == '__main__':

    run_local_test(local_test=LocalTests.TF_UNIVERSE)

