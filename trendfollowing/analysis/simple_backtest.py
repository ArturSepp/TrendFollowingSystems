"""
illustration of backtest using QuantInvestStrats (qis) reporting analytics
"""
import qis as qis
from trendfollowing.systems.european import run_european_tf_system
from trendfollowing.universe import load_data


if __name__ == '__main__':
    # load universe prices and volume costs
    prices, volume_costs, benchmark_prices, descriptive_df, group_order = load_data()
    # compute weights of the trend-following strategy
    backtest_outputs = run_european_tf_system(prices=prices,
                                              long_span=250,
                                              short_span=20,
                                              vol_span=33,
                                              vol_target=0.0035,
                                              portfolio_covar_span=250,
                                              portfolio_target_vol=0.15,
                                              volume_costs=volume_costs)
    # compute executions of system portfolio
    system_portfolio = qis.backtest_model_portfolio(prices=prices,
                                                   weights=backtest_outputs.weights)
    # generate report
    figs = qis.generate_strategy_factsheet(portfolio_data=system_portfolio,
                                           benchmark_prices=benchmark_prices)
