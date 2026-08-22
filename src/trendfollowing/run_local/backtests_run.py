"""Development runner for portfolio-level trend-following backtests."""

from enum import Enum

import matplotlib.pyplot as plt
import pandas as pd
import qis as qis

from trendfollowing.backtests import (
    TFstrategy,
    backtest_american_atr_multiplies_grid,
    backtest_tsmom_grid,
    joint_backtest,
    plot_backtest,
    plot_grid_backtest,
)
from trendfollowing.systems.american import run_american_system
from trendfollowing.systems.european import run_european_tf_system
from trendfollowing.systems.tsmom import run_tsmom_system
from trendfollowing.universe import load_data


class Locals(Enum):
    """Runnable portfolio-backtest development cases."""

    RUN_EUROPEAN = 1
    RUN_AMERICAN = 2
    RUN_TSMOM = 3
    JOINT_BACKTEST = 4
    GRID_BACKTEST = 5
    AMERICAN_MULTIPLIERS = 6
    TSMOM_GRID = 7


def run_local(local: Locals) -> None:
    """Run the selected local portfolio-backtest workflow."""
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    time_period = qis.TimePeriod(start='31Dec1998', end=None)
    perf_time_period = qis.TimePeriod(start='31Dec1999', end='25Apr2025')
    prices, volume_costs, benchmark_prices, group_data, group_order = load_data(
        time_period=time_period
    )

    if local == Locals.RUN_EUROPEAN:
        backtest_outputs = run_european_tf_system(
            prices=prices,
            long_span=250,
            short_span=20,
            vol_span=33,
            vol_target=0.05,
            portfolio_covar_span=250,
            portfolio_target_vol=0.15,
            volume_costs=volume_costs,
        )
        plot_backtest(
            backtest_outputs.portfolio_pnl,
            backtest_outputs.portfolio_pnl_net,
            backtest_outputs.portfolio_turnover,
            backtest_outputs.portfolio_cost,
            backtest_outputs.weights,
        )

    elif local == Locals.RUN_AMERICAN:
        pnl, net_pnl, turnover, costs, weights = run_american_system(
            prices=prices, risk_multiplier=0.0004, volume_costs=volume_costs
        )
        plot_backtest(pnl, net_pnl, turnover, costs, weights)

    elif local == Locals.RUN_TSMOM:
        backtest_outputs = run_tsmom_system(
            prices=prices,
            num_ra_returns=22,
            num_periods=12,
            vol_span=31,
            vol_target=0.05,
            portfolio_covar_span=250,
            portfolio_target_vol=0.15,
            volume_costs=volume_costs,
        )
        plot_backtest(
            backtest_outputs.portfolio_pnl,
            backtest_outputs.portfolio_pnl_net,
            backtest_outputs.portfolio_turnover,
            backtest_outputs.portfolio_cost,
            backtest_outputs.weights,
        )

    elif local == Locals.JOINT_BACKTEST:
        fig = joint_backtest(
            prices=prices,
            volume_costs=volume_costs,
            benchmark_prices=benchmark_prices,
            time_period=perf_time_period,
        )
        qis.save_figs_to_pdf(
            figs=[fig],
            file_name="tf_system",
            orientation='landscape',
            local_path=qis.get_output_path(),
        )

    elif local == Locals.GRID_BACKTEST:
        plot_grid_backtest(
            prices=prices,
            volume_costs=volume_costs,
            benchmark_prices=benchmark_prices,
            tf_strategy=TFstrategy.EUROPEAN,
        )

    elif local == Locals.AMERICAN_MULTIPLIERS:
        net_sharpes, bear_sharpes, costs = backtest_american_atr_multiplies_grid(
            prices=prices,
            volume_costs=volume_costs,
            benchmark_prices=benchmark_prices,
            risk_multiplier=0.0004,
        )
        qis.plot_heatmap(net_sharpes, var_format='{:.2f}')

    elif local == Locals.TSMOM_GRID:
        net_sharpes, bear_sharpes, costs = backtest_tsmom_grid(
            prices=prices, volume_costs=volume_costs, benchmark_prices=benchmark_prices
        )
        print(net_sharpes)
        qis.plot_heatmap(net_sharpes, var_format='{:.2f}')
        qis.plot_heatmap(bear_sharpes, var_format='{:.2f}')
        qis.plot_heatmap(costs, var_format='{:.2f}')

    plt.show()


if __name__ == '__main__':
    run_local(local=Locals.JOINT_BACKTEST)
