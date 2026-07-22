"""
futures universe data layer: loads the packaged dataset of the 84 futures contracts
(daily prices and usd returns, july 1959 to july 2026), the benchmark series, the
volume-based cost schedule following exhibit b1 of hurst et al (2017), and the
instrument metadata
set TF_RESOURCE_PATH to override the packaged data with a local folder
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
import os
import pandas as pd
import numpy as np
import qis as qis
from typing import List, Tuple
from qis import TimePeriod


# the dataset shipped with the package is the default; set TF_RESOURCE_PATH to override with a local data folder
from trendfollowing.local_path import get_universe_data_path
LOCAL_PATH = get_universe_data_path()


# one-way volume-based transaction costs by asset group and period, following exhibit b1 in hurst et al (2017)
COST_STRUCTURE = {TimePeriod(end='31Dec1992'): {'Equities': 0.0034, 'Bonds': 0.0006, 'STIR': 0.0006, 'FX': 0.0018,
                                                'Energy': 0.0058, 'Metals': 0.0058, 'Agriculture': 0.0058},
                  TimePeriod(end='31Dec2002'): {'Equities': 0.0011, 'Bonds': 0.0002, 'STIR': 0.0002, 'FX': 0.0006,
                                                'Energy': 0.0019, 'Metals': 0.0019, 'Agriculture': 0.0019},
                  TimePeriod(end='31Dec2029'): {'Equities': 0.0006, 'Bonds': 0.0001, 'STIR': 0.0001, 'FX': 0.0003,
                                                'Energy': 0.0010, 'Metals': 0.0010, 'Agriculture': 0.0010}}


def get_costs(prices: pd.DataFrame, group_data: pd.Series) -> pd.DataFrame:
    """
    one-way volume-based costs per instrument and date from the period and asset-class schedule
    """
    cost_structure = COST_STRUCTURE

    costs = pd.DataFrame(data=0.0, index=prices.index, columns=prices.columns)
    start_date = prices.index[0]
    for date, ac_cost in cost_structure.items():
        end_date = date.end
        instrument_costs = group_data.map(ac_cost)
        n_index = len(costs.loc[start_date:end_date, :].index)
        costs.loc[start_date:end_date, :] = qis.np_array_to_df_index(a=instrument_costs.to_numpy(), n_index=n_index)
        start_date = end_date
    return costs


def generate_data() -> None:
    """
    regenerate the packaged dataset from bloomberg via the private data layer
    (maintainers only): prices, usd returns, volume costs, the 60/40 and sg trend
    benchmarks, and the instrument metadata
    """
    from futures_strats.data.universes.futures.bbg_futures import Universes
    from bbg_fetch import fetch_field_timeseries_per_tickers

    strategy_universe = Universes.BBG_FUTURES_INVESTABLE.load_universe_data(local_path=LOCAL_PATH)
    prices = strategy_universe.get_prices()
    usd_returns = strategy_universe.get_usd_returns()

    group_data = strategy_universe.get_ac_data(to_value=True)
    names = strategy_universe.get_instrument_names()
    descriptive_df = pd.concat([group_data.rename('group_data'), names.rename('names')], axis=1)
    volume_costs = get_costs(prices=prices, group_data=group_data)

    es_ty = qis.backtest_model_portfolio(prices=prices[['ES1 Index', 'TY1 Comdty']],
                                                    weights=np.array([0.6, 0.4]),
                                                    rebalancing_freq='QE').get_portfolio_nav().to_frame('60/40 Equity/Bond')

    benchmark_prices = fetch_field_timeseries_per_tickers(tickers={'NEIXCTAT Index': 'SG Trend'}, freq='B', field='PX_LAST').ffill()
    benchmark_prices = pd.concat([es_ty, benchmark_prices], axis=1)

    qis.save_df_dict_to_csv(datasets=dict(prices=prices,
                                          usd_returns=usd_returns,
                                          volume_costs=volume_costs,
                                          benchmark_prices=benchmark_prices,
                                          descriptive_df=descriptive_df,
                                          credit_df=credit_df),
                            file_name='tf_system_data',
                            local_path=LOCAL_PATH)


#@qis.timer
def load_data(time_period: TimePeriod = None,
              tickers: List[str] = None
              ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, List[str]]:

    """
    load the packaged futures dataset: prices, volume costs, benchmark prices,
    descriptive metadata, and the asset-group order, optionally restricted to a
    time period and a ticker list
    """
    dfs = qis.load_df_dict_from_csv(dataset_keys=['prices', 'volume_costs', 'benchmark_prices', 'descriptive_df'],
                                    file_name='tf_system_data', local_path=LOCAL_PATH)
    prices = dfs['prices']
    volume_costs = dfs['volume_costs']
    benchmark_prices = dfs['benchmark_prices']
    descriptive_df = dfs['descriptive_df']
    group_order = ['Equities', 'Bonds', 'STIR', 'FX', 'Energy', 'Metals', 'Agriculture']

    if time_period is not None:
        prices = time_period.locate(prices)
        volume_costs = time_period.locate(volume_costs)
        benchmark_prices = time_period.locate(benchmark_prices)
    if tickers is not None:
        prices = prices[tickers]
        volume_costs = volume_costs[tickers]
        descriptive_df = descriptive_df.loc[tickers]
    return prices, volume_costs, benchmark_prices, descriptive_df, group_order


# generate_data()
# print(load_data())
