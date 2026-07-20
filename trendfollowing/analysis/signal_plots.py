"""
illustration of signal plots
"""
import pandas as pd
import os
import numpy as np
import qis as qis
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Optional, Dict
from enum import Enum

# my projects
from trendfollowing.systems.backtest_utils import compute_vol_norm_returns
from trendfollowing.systems.european import compute_tf_signal_weight, compute_tf_signal, compute_tf_strat_pnl


def plot_vol_norm_returns(returns_dict: Dict[str, pd.Series], vol_span: int = 31) -> plt.Figure:
    """
    plot the volatility-normalized returns of the given instruments
    """
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(len(returns_dict.keys()), 2, figsize=(15, 12), tight_layout=True)
        axs = qis.to_flat_list(axs)
        for idx, (key, returns) in enumerate(returns_dict.items()):
            vol_norm_returns = compute_vol_norm_returns(returns=returns.to_numpy(), vol_span=vol_span)
            vol_norm_returns = pd.Series(vol_norm_returns, index=returns.index, name=key)
            qis.plot_time_series(df=vol_norm_returns, title=f"{key} vol normalised returns",
                                 ax=axs[2*idx])
            qis.plot_histogram(df=vol_norm_returns, title=f"{key} vol normalised returns",
                               ax=axs[2*idx+1])
    return fig


def plot_signal(returns_dict: Dict[str, pd.Series],
                long_span: int = 31,
                short_span: Optional[int] = None,
                vol_span: int = 31
                ) -> plt.Figure:
    """
    plot the ewma tf signal of the given instruments
    """
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(len(returns_dict.keys()), 2, figsize=(15, 12), tight_layout=True)
        axs = qis.to_flat_list(axs)
        for idx, (key, returns) in enumerate(returns_dict.items()):
            tf_signal = compute_tf_signal(returns=returns.to_numpy(), long_span=long_span, short_span=short_span, vol_span=vol_span)
            tf_signal = pd.Series(tf_signal, index=returns.index, name=key)
            qis.plot_time_series(df=tf_signal, title=f"{key} signal",
                                 ax=axs[2*idx])
            qis.plot_histogram(df=tf_signal, title=f"{key} signal",
                               ax=axs[2*idx+1])
    return fig


def plot_signal_weight(returns_dict: Dict[str, pd.Series],
                       long_span: int = 31,
                       short_span: Optional[int] = None,
                       vol_span: int = 33,
                       vol_target: float = 0.3
                       ) -> plt.Figure:
    """
    plot the signal and the volatility-target weight of the given instruments
    """
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(len(returns_dict.keys()), 2, figsize=(15, 12), tight_layout=True)
        axs = qis.to_flat_list(axs)
        for idx, (key, returns) in enumerate(returns_dict.items()):
            tf_signal_weight, signals, vols = compute_tf_signal_weight(returns=returns.to_numpy(), long_span=long_span,
                                                                       short_span=short_span, vol_span=vol_span,
                                                                       vol_target=vol_target)
            tf_signal_weight = pd.Series(tf_signal_weight, index=returns.index, name=key)
            qis.plot_time_series(df=tf_signal_weight, title=f"{key} signal",
                                 ax=axs[2*idx])
            qis.plot_histogram(df=tf_signal_weight, title=f"{key} signal",
                               ax=axs[2*idx+1])
    return fig


def plot_strat_pnl(returns_dict: Dict[str, pd.Series],
                   long_span: int = 31,
                   short_span: Optional[int] = None,
                   vol_span: int = 33,
                   vol_target: float = 0.3
                   ) -> plt.Figure:
    """
    plot the strategy pnl of the given instruments under the ewma signal
    """
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(len(returns_dict.keys()), 2, figsize=(15, 12), tight_layout=True)
        axs = qis.to_flat_list(axs)
        for idx, (key, returns) in enumerate(returns_dict.items()):
            pnl, weights, vols = compute_tf_strat_pnl(returns=returns.to_numpy(), long_span=long_span, short_span=short_span,
                                          vol_span=vol_span,
                                          vol_target=vol_target)
            pnl = pd.Series(pnl, index=returns.index, name=key)
            qis.plot_time_series(df=pnl, title=f"{key} cum p&l",
                                 ax=axs[2*idx])
            qis.plot_histogram(df=pnl.diff(1), title=f"{key} daily p&l",
                               ax=axs[2*idx+1])
    return fig


def check_filter_span(returns: pd.Series, long_span: int = 100, short_span: int = 10):
    """
    visual check of the single and long-short filters at the given spans on one instrument
    """
    long_spans = np.linspace(100, 1000, 10)
    signals = {}
    for long_span in long_spans:
        signals[f"span={long_span}"] = qis.compute_ewm_long_short_filter(data=returns, long_span=long_span, short_span=None)
    signals = pd.DataFrame.from_dict(signals, orient='columns')
    with sns.axes_style("darkgrid"):
        fig, ax = plt.subplots(1, 1, figsize=(15, 12), tight_layout=True)
        qis.plot_histogram(df=signals, title='long', ax=ax)


def check_long_short_filters(returns: pd.DataFrame, long_span: int = 100, short_span: int = 10):
    """
    visual check of the long-short filter combinations on a return panel
    """
    signal_unit = qis.compute_ewm_long_short_filter(data=returns, long_span=long_span, short_span=None)
    signal_2 = qis.compute_ewm_long_short_filter(data=returns, long_span=long_span, short_span=short_span)

    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(1, 2, figsize=(15, 12), tight_layout=True)
        qis.plot_histogram(df=signal_unit, title='long', ax=axs[0])
        qis.plot_histogram(df=signal_2, title='ls', ax=axs[1])


class LocalTests(Enum):
    PLOT_VOL_NORM_RETURNS = 1
    PLOT_SIGNAL = 2
    PLOT_SIGNAL_WEIGHT = 3
    PLOT_PNL = 4
    CHECK_SIGNAL = 4


def run_local_test(local_test: LocalTests):
    """Run local tests for development and debugging purposes.

    These are integration tests that download real data and generate reports.
    Use for quick verification during development.
    """
    local_path = os.environ.get("TF_RESOURCE_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources", ""))

    prices = qis.load_df_from_csv(file_name='bbg_futures_close', local_path=local_path)
    time_period = qis.TimePeriod(start='31Dec1999', end=None)
    prices = time_period.locate(prices)
    returns = qis.to_returns(prices=prices)

    if local_test == LocalTests.PLOT_VOL_NORM_RETURNS:
        returns_dict = {'S&P 500': returns['ES1 Index'].dropna(), 'UST10Y': returns['TY1 Comdty'].dropna()}
        print(returns_dict)
        plot_vol_norm_returns(returns_dict=returns_dict)

    elif local_test == LocalTests.PLOT_SIGNAL:
        returns_dict = {'S&P 500': returns['ES1 Index'].dropna(), 'UST10Y': returns['TY1 Comdty'].dropna()}
        print(returns_dict)
        plot_signal(returns_dict=returns_dict,
                    long_span=100,
                    short_span=None,
                    vol_span=31)

    elif local_test == LocalTests.PLOT_SIGNAL_WEIGHT:
        returns_dict = {'S&P 500': returns['ES1 Index'].dropna(), 'UST10Y': returns['TY1 Comdty'].dropna()}
        print(returns_dict)
        plot_signal_weight(returns_dict=returns_dict,
                           long_span=100,
                           short_span=None,
                           vol_span=31)

    elif local_test == LocalTests.PLOT_PNL:
        returns_dict = {'S&P 500': returns['ES1 Index'].dropna(), 'UST10Y': returns['TY1 Comdty'].dropna()}
        print(returns_dict)
        plot_strat_pnl(returns_dict=returns_dict,
                       long_span=250,
                       short_span=20,
                       vol_span=31)

    elif local_test == LocalTests.CHECK_SIGNAL:

        # signals = compute_tf_signal(returns=returns.to_numpy(), tf_span=120)
        #signals = pd.DataFrame(signals, index=returns.index, columns=returns.columns)
        #qis.plot_histogram(df=signals)

        returns = pd.DataFrame(np.random.normal(loc=0.0, scale=0.2, size=(100000, 30)))
        ra_returns, _, _ = qis.compute_ra_returns(returns=returns)
        #check_long_short_filters(returns=ra_returns)

        check_filter_span(returns=ra_returns.iloc[:, 0])
    plt.show()


if __name__ == '__main__':

    local_test = LocalTests.PLOT_PNL

    run_local_test(local_test=local_test)
