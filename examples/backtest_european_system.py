"""
backtest the European long-short TF system LS(250,20) on the packaged futures
universe and report the portfolio performance

uses only the dataset packaged in trendfollowing/resources
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
# packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from enum import Enum
# qis / project
import qis as qis
from trendfollowing.universe import load_data
from trendfollowing.systems.european import run_european_tf_system
from trendfollowing.analytics.sharpe import compute_realized_sharpe

AF = 260.0  # annualization factor, the weekday count


def summarize_nav(nav: pd.Series) -> pd.Series:
    """annualized performance summary of a compounded nav"""
    returns = nav.pct_change().dropna()
    drawdown = nav / nav.cummax() - 1.0
    return pd.Series(dict(sharpe=float(compute_realized_sharpe(returns=returns, af=AF, ddof=1)),
                          an_vol=np.sqrt(AF) * returns.std(),
                          an_return=AF * returns.mean(),
                          max_dd=drawdown.min()),
                     name=nav.name)


class LocalTests(Enum):
    PORTFOLIO_BACKTEST = 1


def run_local_test(local_test: LocalTests) -> None:
    if local_test == LocalTests.PORTFOLIO_BACKTEST:
        prices, volume_costs, benchmark_prices, descriptive_df, group_order = load_data()
        outputs = run_european_tf_system(prices=prices,
                                         long_span=250,
                                         short_span=20,  # the LS(250,20) filter of the paper
                                         vol_span=33,  # volatility estimator span, days
                                         portfolio_covar_span=63,  # activates portfolio-level volatility targeting
                                         portfolio_target_vol=0.15,  # annualized portfolio volatility target
                                         volume_costs=volume_costs,
                                         warmup_period=250)
        nav = outputs.portfolio_pnl_net.rename('European LS(250,20)').dropna()
        nav = nav[nav.ne(nav.iloc[0]).cummax()]  # start at the first active day after the warmup
        print(summarize_nav(nav=nav).round(3))
        with plt.style.context('bmh'):
            fig, ax = plt.subplots(1, 1, figsize=(10, 5), tight_layout=True)
            nav.plot(ax=ax, logy=True, title='European LS(250,20), net of volume-based costs')
            fig.savefig('example_european_backtest.png', dpi=150)


if __name__ == '__main__':
    run_local_test(local_test=LocalTests.PORTFOLIO_BACKTEST)
