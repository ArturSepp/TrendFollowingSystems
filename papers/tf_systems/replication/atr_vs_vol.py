# packages
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import qis as qis
from qis.utils.sampling import split_to_samples
from typing import Dict, Union
from enum import Enum

# project
from trendfollowing.systems.backtest_utils import compute_vol


def get_ohlc_data(ticker: str = 'ES1 Index', time_period: qis.TimePeriod = None) -> pd.DataFrame:
    """
    load daily ohlc fields for the ticker from the packaged resources, with a terminal fetch as fallback
    the resource file is tf_system_data_ohlc_{prefix}.csv with columns px_open, px_high, px_low, px_last
    """
    from trendfollowing.universe import LOCAL_PATH
    file_name = f"tf_system_data_ohlc_{ticker.split()[0].lower()}"
    file_path = os.path.join(LOCAL_PATH, f"{file_name}.csv")
    if os.path.isfile(file_path):
        df = qis.load_df_from_csv(file_name=file_name, local_path=LOCAL_PATH)
    else:
        from bbg_fetch import fetch_fields_timeseries_per_ticker  # runtime dependency: requires terminal access
        df = fetch_fields_timeseries_per_ticker(ticker=ticker, fields=['PX_OPEN', 'PX_HIGH', 'PX_LOW', 'PX_LAST'])
    if time_period is not None:
        df = time_period.locate(df)
    return df


def compute_atr(ohlc_prices: pd.DataFrame, is_norm: bool = True, is_agg: bool = True) -> Union[float, pd.Series]:
    high_low = np.abs(ohlc_prices['PX_HIGH'] - ohlc_prices['PX_LOW']).to_numpy()[1:]
    high_close = np.abs(ohlc_prices['PX_HIGH'] - ohlc_prices['PX_LAST'].shift(1)).to_numpy()[1:]
    low_close = np.abs(ohlc_prices['PX_LOW'] - ohlc_prices['PX_LAST'].shift(1)).to_numpy()[1:]
    atr = np.maximum(high_low, np.maximum(high_close, low_close))
    if is_norm:
        atr = atr / ohlc_prices['PX_LAST'].to_numpy()[:-1]
        # atr /= np.sqrt(np.pi/2.0)
    if is_agg:
        atr = np.nanmean(atr)
    else:
        atr = pd.Series(atr, index=ohlc_prices.index[1:], name='ATR')
    return atr


def compute_ewma_atr(ohlc_prices: pd.DataFrame, vol_span: int = 33) -> pd.Series:
    atr = compute_atr(ohlc_prices=ohlc_prices, is_norm=True, is_agg=False)
    ewma_atr = qis.compute_ewm(data=atr, span=vol_span)
    return ewma_atr


def estimate_atr_vol(samples: Dict[pd.Timestamp, pd.DataFrame]) -> pd.DataFrame:
    atrs = {}
    vols = {}
    for date, sample in samples.items():
        atrs[date] = compute_atr(sample) # / sample['PX_LAST'].iloc[0] / np.sqrt(np.pi/2.0)
        returns = qis.to_returns(sample['PX_LAST'], is_log_returns=False, drop_first=True)
        # vols[date] = np.nanstd(returns)
        vols[date] = np.sqrt(np.nanmean(np.square(returns)))
    atrs = pd.Series(atrs, name='ARTR')
    vols = pd.Series(vols, name='St. Dev')
    df = pd.concat([vols, atrs], axis=1)
    return df


def plot_scatter_figure(tickers: Dict[str, str], time_period: qis.TimePeriod = None) -> plt.Figure:

    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(1, len(tickers.keys()), figsize=(16, 7), tight_layout=True)

    for idx, (ticker, name) in enumerate(tickers.items()):
        ohlc_data = get_ohlc_data(ticker=ticker, time_period=time_period)
        samples = split_to_samples(data=ohlc_data, sample_freq='ME')
        df = estimate_atr_vol(samples=samples)
        qis.plot_scatter(df,
                         full_sample_order=1,
                         x_limits=(0.0, None),
                         y_limits=(0.0, None),
                         xvar_format='{:.1%}',
                         yvar_format='{:.1%}',
                         full_sample_label='',
                         fontsize=14,
                         title=f"{name}",
                         ax=axs[idx])

    return fig


def plot_timeseries_figure(ticker: str,
                           time_period: qis.TimePeriod = None,
                           vol_span: int = 33,
                           annualization_factor: float = 260,
                           vol_target: float = 0.15
                           ) -> plt.Figure:

    ohlc_prices = get_ohlc_data(ticker=ticker, time_period=time_period)

    returns = qis.to_returns(prices=ohlc_prices['PX_LAST'], is_log_returns=True, drop_first=True)
    returns_np = returns.to_numpy()

    # vols
    ewma_vols_np =  compute_vol(returns=returns_np, vol_span=vol_span, is_lag1=False)
    ewma_vols = pd.Series(ewma_vols_np, index=returns.index, name='EMWA Vol')
    atr_ewma = compute_ewma_atr(ohlc_prices=ohlc_prices, vol_span=vol_span).rename('EWMA RTR') / 1.4
    vols = np.sqrt(annualization_factor) * pd.concat([ewma_vols, atr_ewma], axis=1)

    # target weights
    ewma_vol_target_weights = (vol_target / (np.sqrt(annualization_factor) * ewma_vols))
    atr_vol_target_weights = (vol_target / (np.sqrt(annualization_factor) *atr_ewma))
    voltarget_weights = pd.concat([ewma_vol_target_weights, atr_vol_target_weights], axis=1)

    # vol-norm returns
    ewma_vol_norm_returns = returns_np[:-1] / ewma_vols_np[1:]
    atr_vol_norm_returns = returns_np[:-1] / atr_ewma.to_numpy()[1:]
    vol_norm_returns = pd.concat([pd.Series(ewma_vol_norm_returns, index=returns.index[1:], name='EMWA Vol'),
                                  pd.Series(atr_vol_norm_returns, index=returns.index[1:], name='EMWA RTR')
                                  ], axis=1)
    dfs = {# ('Volatilities', 'Log-Volatilities'): (vols, np.log(vols)),
        'Volatilities': (vols, vols),
        '15% Volatility target weights': (voltarget_weights, voltarget_weights),
        'Volatility normalised returns': (vol_norm_returns, vol_norm_returns) }
    x_limitss = [(0.0, 1.0), (0.0, 3.0), (-4.0, 4.0)]
    var_formats = ['{:,.0%}', '{:,.2f}', '{:,.2f}']

    with sns.axes_style("darkgrid"):
        kwargs = dict(framealpha=0.90, date_format='%Y', fontsize=14)
        fig, axs = plt.subplots(len(dfs.keys()), 2, figsize=(16, 10), tight_layout=True)

        for idx, (key, dfs) in enumerate(dfs.items()):
            if isinstance(key, tuple):
                title1 = f"({qis.idx_to_alphabet(idx+1)}1) {key[0]}: time series"
                title2 = f"({qis.idx_to_alphabet(idx+1)}2) {key[1]}: histogram"
            else:
                title1 = f"({qis.idx_to_alphabet(idx+1)}1) {key}: time series"
                title2 = f"({qis.idx_to_alphabet(idx+1)}2) {key}: histogram"

            qis.plot_time_series(df=dfs[0], title=title1,
                                 legend_stats=qis.LegendStats.AVG_STD,
                                 var_format=var_formats[idx],
                                 ax=axs[idx, 0], **kwargs)
            qis.plot_histogram(df=dfs[1], title=title2,
                               legend_stats=qis.LegendStats.AVG_STD,
                               desc_table_type=qis.DescTableType.NONE,
                               xvar_format=var_formats[idx],
                               x_limits=x_limitss[idx],
                               ax=axs[idx, 1], **kwargs)

    return fig


class LocalTests(Enum):
    ONE_PLOT = 1
    SCATTER_FIGURE = 2
    TIME_SERIES_FIGURE = 3


def run_local_test(local_test: LocalTests):
    """Run local tests for development and debugging purposes.

    These are integration tests that download real data and generate reports.
    Use for quick verification during development.
    """

    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    local_path = os.environ.get("TF_FIGURE_PATH", qis.local_path.get_output_path())  # set TF_FIGURE_PATH to the paper figures folder

    if local_test == LocalTests.ONE_PLOT:
        ohlc_data = get_ohlc_data(ticker='GC1 Comdty')
        samples = split_to_samples(data=ohlc_data, sample_freq='ME')
        df = estimate_atr_vol(samples=samples)
        print(df)
        qis.plot_scatter(df, full_sample_order=1)

    elif local_test == LocalTests.SCATTER_FIGURE:
        tickers = {'ES1 Index': '(A) S&P 500', 'TY1 Comdty': '(B) UST 10Y', 'GC1 Comdty': '(C) Gold'}
        fig = plot_scatter_figure(tickers=tickers, time_period=qis.TimePeriod('31Dec1997', None))
        qis.save_fig(fig, file_name='atr_vs_vol', local_path=local_path)

    elif local_test == LocalTests.TIME_SERIES_FIGURE:
        ticker = 'ES1 Index'
        fig = plot_timeseries_figure(ticker=ticker, time_period=qis.TimePeriod('31Dec1997', '30Jun2026'))
        qis.save_fig(fig, file_name='atr_vs_vol_ts', local_path=local_path)

    plt.show()


if __name__ == '__main__':
    run_local_test(local_test=LocalTests.SCATTER_FIGURE)
