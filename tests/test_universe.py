"""
tests for the packaged futures dataset: shapes, benchmarks, and metadata alignment
"""
# packages
import pandas as pd
import pytest
from pathlib import Path
# project
from trendfollowing.universe import load_data, get_universe_data_path


@pytest.fixture(autouse=True)
def require_boolean_csv_dayfirst(monkeypatch):
    """Keep the pandas 3.1 CSV contract covered even with older locked pandas."""
    read_csv = pd.read_csv

    def strict_read_csv(*args, **kwargs):
        if not isinstance(kwargs.get('dayfirst', False), bool):
            raise ValueError('dayfirst must be bool, not None')
        return read_csv(*args, **kwargs)

    monkeypatch.setattr(pd, 'read_csv', strict_read_csv)


def test_packaged_universe_loads():
    prices, volume_costs, benchmark_prices, descriptive_df, group_order = load_data()
    assert prices.shape[1] == 84  # universe of the paper (Table 7.1)
    assert str(prices.index[0].date()) == '1959-07-02'
    assert list(benchmark_prices.columns) == ['60/40 Equity/Bond', 'SG Trend']
    assert volume_costs.shape == prices.shape
    assert descriptive_df.index.equals(prices.columns)
    assert group_order[0] == 'Equities'
    for key, frame in [('prices', prices), ('volume_costs', volume_costs),
                       ('benchmark_prices', benchmark_prices)]:
        dates = pd.read_csv(
            Path(get_universe_data_path()) / f'tf_system_data_{key}.csv',
            usecols=[0], dtype=str,
        ).iloc[:, 0]
        assert frame.index.strftime('%Y-%m-%d').tolist() == dates.tolist()


def test_packaged_ohlc_loads():
    from papers.tf_systems.replication.atr_vs_vol import get_ohlc_data
    for ticker in ['ES1 Index', 'TY1 Comdty', 'GC1 Comdty']:
        df = get_ohlc_data(ticker=ticker)
        assert list(df.columns) == ['PX_OPEN', 'PX_HIGH', 'PX_LOW', 'PX_LAST']
        assert len(df) > 7000
        dates = pd.read_csv(
            Path(get_universe_data_path()) / f'tf_system_data_ohlc_{ticker.split()[0].lower()}.csv',
            usecols=[0], dtype=str,
        ).iloc[:, 0]
        assert df.index.strftime('%Y-%m-%d').tolist() == dates.tolist()
