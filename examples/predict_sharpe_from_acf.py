"""
predict the realized Sharpe ratio of the European TF system from the sample
autocorrelation function and drift of volatility-normalized returns

a per-instrument miniature of the attribution exercise of the paper: the
closed form applied to the sample moments reproduces the realized backtest
Sharpe ratio in-sample

uses only the dataset packaged in trendfollowing/resources
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
# packages
import numpy as np
import pandas as pd
from enum import Enum
from typing import List
# qis / project
import qis as qis
from trendfollowing.universe import load_data
from trendfollowing.systems.european import run_european_tf_system
from trendfollowing.analytics.sharpe import compute_annualised_sharpe, compute_realized_sharpe

AF = 260.0
VOL_SPAN = 33  # days
WARMUP = 250  # days
N_LAGS = 780


def predict_and_realize(tickers: List[str],
                        span: int = 63,  # signal span, days
                        ) -> pd.DataFrame:
    """closed-form prediction from sample moments against the realized gross backtest"""
    prices, volume_costs, benchmark_prices, descriptive_df, group_order = load_data()
    prices = prices[tickers].dropna(how='all')
    rows = {}
    for ticker in tickers:
        price = prices[ticker].dropna()
        returns = price.pct_change()
        vol = np.sqrt(qis.compute_ewm(data=np.square(returns), span=VOL_SPAN))
        z = (returns / vol.shift(1)).iloc[WARMUP:].dropna()
        # sample inputs of the closed form
        rho = np.array([1.0] + [z.autocorr(lag=m) for m in range(1, N_LAGS)])
        mu_an = np.sqrt(AF) * z.mean() / z.std()
        predicted = compute_annualised_sharpe(rho=rho, long_span=span, short_span=None,
                                              sr_underlying=mu_an, af=AF)
        # realized gross backtest on the same sample
        outputs = run_european_tf_system(prices=price.to_frame(), long_span=span, short_span=None,
                                         vol_span=VOL_SPAN, volume_costs=0.0, warmup_period=WARMUP)
        strategy_returns = outputs.portfolio_pnl.pct_change()  # portfolio_pnl is the compounded nav from 1.0
        strategy_returns = strategy_returns[strategy_returns != 0.0]  # drop the flat warmup segment
        realized = float(compute_realized_sharpe(returns=strategy_returns, af=AF, ddof=1))
        rows[ticker] = dict(predicted=predicted, realized=float(realized))
    return pd.DataFrame.from_dict(rows, orient='index')


class LocalTests(Enum):
    PREDICT_CORE_CONTRACTS = 1


def run_local_test(local_test: LocalTests) -> None:
    if local_test == LocalTests.PREDICT_CORE_CONTRACTS:
        table = predict_and_realize(tickers=['ES1 Index', 'TY1 Comdty', 'GC1 Comdty', 'C 1 Comdty'], span=63)
        print(table.round(3))


if __name__ == '__main__':
    run_local_test(local_test=LocalTests.PREDICT_CORE_CONTRACTS)
