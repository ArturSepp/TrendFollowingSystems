"""
empirical autocorrelation analysis of futures returns: per-instrument and
per-group acf estimates and plots behind the autocorrelation exhibits of the paper
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
# packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import qis as qis
from typing import Tuple, Dict, List, Union
from enum import Enum

import qis.utils.df_groups as dfg
import qis.utils.dates as da
import qis.models.linear.ra_returns as tra
import qis.plots.boxplot as box
import qis.perfstats.returns as ret
from qis.models.linear.auto_corr import estimate_acf_from_paths

from futures_strats.data.universes.futures.bbg_futures import Universes
from futures_strats.local_path import LOCAL_PATH


def compute_returns_autocorrelation(prices: Union[pd.DataFrame, pd.Series],
                                    freq: str = 'B',
                                    span: int = 31,
                                    autocorr_span: int = 31,
                                    is_ra_returns: bool = False
                                    ) -> Union[pd.DataFrame, pd.Series]:

    """
    sample acf of log returns per instrument at the given lags
    """
    if isinstance(prices, pd.Series):
        prices = prices.to_frame()
    returns_1 = qis.to_returns(prices=prices, is_log_returns=True, freq=None, drop_first=True)
    autocorr_df = qis.ewm_xy_convolution(returns=returns_1,
                                         freq=freq,
                                         convolution_type=qis.ConvolutionType.AUTO_CORR,
                                         is_ra_returns=is_ra_returns)
    return autocorr_df


def compute_returns_autocorrelation0(prices: Union[pd.DataFrame, pd.Series],
                                    freq: str = 'B',
                                    span: int = 31,
                                    autocorr_span: int = 31,
                                    is_ra_returns: bool = False
                                    ) -> Union[pd.DataFrame, pd.Series]:
    """
    sample acf of log returns per instrument, legacy variant kept for comparison
    """
    if is_ra_returns:
        returns_1 = qis.to_returns(prices=prices, is_log_returns=True, freq=None, drop_first=True)
        returns = qis.compute_sum_freq_ra_returns(returns=returns_1, freq=freq, span=span,
                                                  is_log_returns_to_arithmetic=False,
                                                  is_norm=False,
                                                  warmup_period=100)
    else:
        returns = qis.to_returns(prices=prices, is_log_returns=True, freq=freq, drop_first=True)

    autocorr_df = qis.compute_ewm_vector_autocorr_df(data=returns,
                                                     span=autocorr_span,
                                                     lag=1,
                                                     is_normalize=True)
    return autocorr_df


def get_prices(time_period: da.TimePeriod = None) -> Tuple[Dict, pd.Series]:
    """
    load the asset-class price dictionary and group metadata for the acf exhibits
    """
    universe_data = Universes.BBG_FUTURES.load_universe_data(local_path=LOCAL_PATH)
    prices = universe_data.get_prices(time_period=time_period)
    prices = prices.dropna(axis=1, how='all')
    ac_data = universe_data.get_ac_data()[prices.columns]
    ac_data = ac_data.apply(lambda x: x.value)
    ac_prices = dfg.split_df_by_groups(df=prices, group_data=ac_data, total_column='Universe')

    return ac_prices, ac_data


def plot_instrument_acf(price: pd.Series,
                        freqs: List[str] = ('B', 'W-MON', 'ME', 'QE'),
                        ra_spans: List[int] = (2.5, 5, 21, 63),
                        nlags: int = 20,
                        is_ra_returns: bool = False
                        ):

    """
    plot the sample acf and pacf bars of one instrument's returns
    """
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(2, 2, figsize=(12, 8), tight_layout=True)
        axs = qis.to_flat_list(axs)

        for idx, freq in enumerate(freqs):
            returns_1 = qis.to_returns(prices=price, is_log_returns=True, freq=None, drop_first=True)
            if is_ra_returns:
                returns = qis.compute_sum_freq_ra_returns(returns=returns_1, freq=freq, span=ra_spans[idx],
                                                          is_log_returns_to_arithmetic=False,
                                                          is_norm=False)
            else:
                returns = qis.to_returns(prices=price, is_log_returns=True, freq=freq, drop_first=True)

            acfs, pacfs = qis.estimate_acf_from_path(path=returns, nlags=nlags)
            qis.plot_bars(df=acfs,
                          title=f"Returns frequency={freq}",
                          legend_loc=None,
                          x_rotation=0,
                          xlabel='lag',
                          ax=axs[idx])
            ax = axs[idx]
            n_error = 1.0 / np.sqrt(len(returns.index))
            ax.axhline(n_error, color='red', linestyle='dashed', linewidth=1)
            ax.axhline(-n_error, color='red', linestyle='dashed', linewidth=1)
            qis.set_suptitle(fig, title=f"Autocorrelation of {price.name}: {qis.get_time_period(df=price).to_str()}")


def plot_instrument_acf_ewm(prices: Union[pd.Series, pd.DataFrame],
                            freqs: List[str] = ('B', 'W-MON', 'ME', 'QE'),
                            ra_span: int = 31,
                            autocorr_spans: List[int] = (10*260, 10*52, 10*12, 10*4),
                            is_ra_returns: bool = False
                            ):

    """
    plot the ewm-smoothed acf of instrument returns across lags
    """
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(2, 2, figsize=(12, 8), tight_layout=True)
        axs = qis.to_flat_list(axs)

        for idx, freq in enumerate(freqs):
            autocorr_df = compute_returns_autocorrelation(prices=prices,
                                                          freq=freq,
                                                          span=ra_span,
                                                          autocorr_span=autocorr_spans[idx],
                                                          is_ra_returns=is_ra_returns)
            if isinstance(prices, pd.DataFrame) and len(prices.columns) > 10:
                legend_loc = None
            else:
                legend_loc = 'upper left'
            qis.plot_time_series(df=autocorr_df,
                                 title=f"Returns frequency={freq}",
                                 x_date_freq='YE',
                                 date_format='%d-%b-%y',
                                 legend_loc=legend_loc,
                                 ax=axs[idx])
            ax = axs[idx]
            n_error = 1.0 / np.sqrt(autocorr_spans[idx])
            ax.axhline(n_error, color='red', linestyle='dashed', linewidth=1)
            ax.axhline(-n_error, color='red', linestyle='dashed', linewidth=1)



def plot_group_acf_ewm(prices: pd.DataFrame,
                       freqs: List[str] = ('B', 'W-MON', 'ME', 'QE'),
                       ra_span: int = 31,
                       autocorr_spans: List[int] = (10*260, 10*52, 10*12, 10*4),
                       is_ra_returns: bool = False
                       ) -> plt.Figure:

    """
    plot the ewm-smoothed acf aggregated by asset group
    """
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(2, 2, figsize=(12, 8), tight_layout=True)
        axs = qis.to_flat_list(axs)

        for idx, freq in enumerate(freqs):
            autocorr_df = compute_returns_autocorrelation(prices=prices,
                                                          freq=freq,
                                                          span=ra_span,
                                                          autocorr_span=autocorr_spans[idx],
                                                          is_ra_returns=is_ra_returns)
            autocorr_df = autocorr_df.replace({0.0: np.nan})
            df = pd.concat([autocorr_df.quantile(q=0.25, axis=1).rename('25% Quantile'),
                            autocorr_df.median(axis=1).rename('Median'),
                            autocorr_df.quantile(q=0.75, axis=1).rename('75% Quantile')], axis=1)

            qis.plot_time_series(df=df,
                                 title=f"Returns frequency={freq}",
                                 x_date_freq='YE',
                                 date_format='%d-%b-%y',
                                 framealpha=0.9,
                                 trend_line=qis.TrendLine.ZERO_SHADOWS,
                                 ax=axs[idx])
            ax = axs[idx]
            n_error = 1.0 / np.sqrt(autocorr_spans[idx])
            ax.axhline(n_error, color='red', linestyle='dashed', linewidth=1)
            ax.axhline(-n_error, color='red', linestyle='dashed', linewidth=1)

    return fig


def plot_acf(time_period: da.TimePeriod = None):
    ac_prices, ac_data = get_prices(time_period=time_period)

    freq = 'QE'
    ac_acfs = []
    for ac, prices in ac_prices.items():
        returns = ret.to_returns(prices=prices, freq=freq)
        acfs, m_acf, std_acf = estimate_acf_from_paths(paths=returns, is_pacf=True)
        ac_acfs.append(acfs)
    ac_acfs = pd.concat(ac_acfs, axis=1)

    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(1, 1, figsize=(18, 10), tight_layout=True)
        box.df_boxplot_by_index(df=ac_acfs, ax=axs)

    returns = ret.to_returns(prices=ac_prices['Universe'], freq=freq)
    returns, weights, _ = tra.compute_ra_returns(returns=ret.to_returns(prices=ac_prices['Universe'],is_first_zero=True), ewm_lambda=0.94)
    # returns = returns.resample('QE').sum().iloc[1:, :]
    print(returns)

    acfs, m_acf, std_acf = estimate_acf_from_paths(paths=returns, is_pacf=True, nlags=100)
    acfs = acfs.drop(0, axis=0)
    ac_acfs = acfs.T.dropna(axis=0, how='all')
    ac_acfs.columns = [f"lag-{n}" for n in range(len(ac_acfs.columns))]
    ac_acfs['ac'] = ac_data
    ac_acfs = ac_acfs.set_index('ac')
    print(ac_acfs)
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(1, 1, figsize=(18, 10), tight_layout=True)
        box.df_boxplot_by_hue_var(df=ac_acfs, x_index_var_name='ac', hue_var_name='lags', ax=axs)


class LocalTests(Enum):
    DATA = 1
    ACF = 2
    INSTRUMENT_ACF = 3
    TIME_SERIES_AUTOCORR = 4
    GROUP_TIME_SERIES_AUTOCORR = 5


def run_local_test(local_test: LocalTests):
    """Run local tests for development and debugging purposes.

    These are integration tests that download real data and generate reports.
    Use for quick verification during development.
    """

    from futures_strats.local_path import LOCAL_PATH
    universe_data = Universes.BBG_FUTURES.load_universe_data(local_path=LOCAL_PATH)
    prices = universe_data.get_prices(freq='B').ffill()
    time_period = da.TimePeriod('31Dec1990', None)
    prices = time_period.locate(prices)

    if local_test == LocalTests.DATA:
        get_prices()

    elif local_test == LocalTests.ACF:
        plot_acf(time_period=time_period)

    elif local_test == LocalTests.INSTRUMENT_ACF:
        # price = prices['NI1 Index'].dropna()
        price = prices['ES1 Index'].dropna()
        plot_instrument_acf(price=price, is_ra_returns=False)

    elif local_test == LocalTests.TIME_SERIES_AUTOCORR:
        # price = prices['NI1 Index'].dropna()
        # price = prices['ES1 Index'].dropna()
        price = prices['GC1 Comdty'].dropna()
        plot_instrument_acf_ewm(prices=price, is_ra_returns=True)

    elif local_test == LocalTests.GROUP_TIME_SERIES_AUTOCORR:
        group_data = universe_data.get_ac_data()
        dfs = qis.split_df_by_groups(df=prices, group_data=group_data)
        # plot_instrument_acf_ewm(prices=dfs['AcCom.EQ'], is_ra_returns=False)
        figs = []
        for key, df in dfs.items():
            fig = plot_group_acf_ewm(prices=df, is_ra_returns=True)
            qis.set_suptitle(fig, title=f"{key}")
            figs.append(fig)
        qis.save_figs_to_pdf(figs, file_name='group_acf', local_path=qis.get_output_path())

    plt.show()


if __name__ == '__main__':

    local_test = LocalTests.TIME_SERIES_AUTOCORR

run_local_test(local_test=local_test)
