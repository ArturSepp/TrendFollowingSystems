"""
tests for the packaged futures dataset: shapes, benchmarks, and metadata alignment
"""
# packages
import pandas as pd
# project
from trendfollowing.universe import load_data


def test_packaged_universe_loads():
    prices, volume_costs, benchmark_prices, descriptive_df, group_order = load_data()
    assert prices.shape[1] == 84  # universe of the paper (Table 7.1)
    assert str(prices.index[0].date()) == '1959-07-02'
    assert list(benchmark_prices.columns) == ['60/40 Equity/Bond', 'SG Trend']
    assert volume_costs.shape == prices.shape
    assert descriptive_df.index.equals(prices.columns)
    assert group_order[0] == 'Equities'


def test_packaged_ohlc_loads():
    from papers.tf_systems.replication.atr_vs_vol import get_ohlc_data
    for ticker in ['ES1 Index', 'TY1 Comdty', 'GC1 Comdty']:
        df = get_ohlc_data(ticker=ticker)
        assert list(df.columns) == ['PX_OPEN', 'PX_HIGH', 'PX_LOW', 'PX_LAST']
        assert len(df) > 7000
