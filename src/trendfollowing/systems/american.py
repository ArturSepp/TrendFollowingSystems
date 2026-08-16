"""
implementation of the american trend-following system: binary positions from the
crossover of two price ewma filters with an atr entry buffer and atr trailing
stop-losses, in the tradition of the turtle systems, with position size fixed at
trade inception
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
import numpy as np
import pandas as pd
import qis as qis
from qis.utils.df_ops import get_first_nonnan_values
from numba import njit
from typing import Union, Optional, Tuple

from trendfollowing.systems.backtest_utils import compute_pnl, compute_vol, BacktestOutputs


@njit
def run_american_on_instrument(price: np.ndarray,
                               long_ewma: np.ndarray,
                               short_ewma: np.ndarray,
                               true_range: np.ndarray,
                               risk_multiplier: float = 0.01,
                               stop_loss_atr_multiplier: float = 10.0,
                               signal_atr_multiplier: float = 5.0,
                               weight_abs_limit: float = 5.0,
                               warmup_period: int = 250
                               ) -> Tuple[np.ndarray, np.ndarray]:
    """
    american
    """
    assert warmup_period > 1
    current_weight = 0.0
    weights = np.zeros_like(price)
    stop_losses = np.zeros_like(price)
    stop_loss = 0.0
    t_after_nonan = 0
    for t, price_t in enumerate(price):
        if np.isfinite(price_t):  # price needs to be finite
            t_after_nonan += 1  # count days after first non nan
            if t_after_nonan > warmup_period:
                true_range_t_1 = true_range[t - 1]
                if true_range_t_1 > 0.0:
                    relative_size = risk_multiplier * price_t / true_range_t_1
                else:
                    relative_size = 0.0
                short_ewma_t = short_ewma[t]
                long_ewma_t = long_ewma[t]

                is_fast_above_slow = True if short_ewma_t > long_ewma_t + signal_atr_multiplier*true_range_t_1 else False
                is_fast_below_slow = True if short_ewma_t < long_ewma_t - signal_atr_multiplier*true_range_t_1 else False

                if current_weight == 0.0:
                    if is_fast_above_slow:  # open long
                        current_weight = np.minimum(relative_size, weight_abs_limit)
                        stop_loss = price_t - stop_loss_atr_multiplier * true_range_t_1
                    elif is_fast_below_slow:  # open short
                        current_weight = - np.minimum(relative_size, weight_abs_limit)
                        stop_loss = price_t + stop_loss_atr_multiplier * true_range_t_1
                else:  # check current position
                    if current_weight > 0.0:
                        # close
                        if price_t < stop_loss and not is_fast_above_slow:
                            current_weight = 0.0
                            stop_loss = 0.0
                        else:  # update stop loss
                            stop_loss = np.maximum(price_t - stop_loss_atr_multiplier * true_range_t_1, stop_loss)
                    elif current_weight < 0.0:
                        # close
                        if price_t > stop_loss and not is_fast_below_slow:
                            current_weight = 0.0
                            stop_loss = 0.0
                        else:  # update stop loss
                            stop_loss = np.minimum(price_t + stop_loss_atr_multiplier * true_range_t_1, stop_loss)
                weights[t] = current_weight
                stop_losses[t] = stop_loss
    return weights, stop_losses


def run_american_system(prices: Union[pd.Series, pd.DataFrame],
                        long_span: int = 250,
                        short_span: int = 20,
                        vol_span: int = 33,
                        risk_multiplier: float = 0.01,
                        weight_abs_limit: float = 10.0,
                        stop_loss_atr_multiplier: float = 5.0,
                        signal_atr_multiplier: float = 5.0,
                        annualization_factor: float = 260,
                        portfolio_covar_span: Optional[float] = None,
                        portfolio_target_vol: float = 0.15,
                        warmup_period: int = 250,
                        volume_costs: Union[float, pd.DataFrame] = 0.0020  # assume flat across contracts
                        ) -> BacktestOutputs:

    """
    backtest of the american system on a price panel: runs the per-instrument
    crossover state machine, applies optional portfolio-level volatility
    targeting and the warmup mask, and returns gross and net pnl with
    turnover and costs
    """
    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    returns_np = qis.to_returns(prices).to_numpy()
    #1 compute volatility
    vols = np.sqrt(annualization_factor)*compute_vol(returns=returns_np, vol_span=vol_span, is_lag1=False)
    # true_range = np.power(np.pi/8.0, -5) * np.sqrt(annualization_factor) * vol
    # true_range = np.sqrt(annualization_factor) * vol
    true_range = np.abs(prices.diff(1)).rolling(vol_span, min_periods=vol_span//2).mean().to_numpy()
    np_prices = prices.to_numpy()
    init_value = get_first_nonnan_values(np_prices)
    long_ewma = qis.ewm_recursion(a=np_prices, span=long_span, init_value=init_value)
    short_ewma = qis.ewm_recursion(a=np_prices, span=short_span, init_value=init_value)

    weights = np.zeros_like(np_prices)
    for idx, column in enumerate(prices.columns):
        weights[:, idx], stop_loss = run_american_on_instrument(price=np_prices[:, idx],
                                                                long_ewma=long_ewma[:, idx],
                                                                short_ewma=short_ewma[:, idx],
                                                                true_range=true_range[:, idx],
                                                                weight_abs_limit=weight_abs_limit,
                                                                risk_multiplier=risk_multiplier,
                                                                stop_loss_atr_multiplier=stop_loss_atr_multiplier,
                                                                signal_atr_multiplier=signal_atr_multiplier,
                                                                warmup_period=warmup_period)

    if portfolio_covar_span is not None:
        portfolio_var = qis.compute_portfolio_var_np(returns=returns_np, weights=weights, span=portfolio_covar_span)
        reciprocal_portfolio_var = np.reciprocal(annualization_factor*portfolio_var, where=portfolio_var > 0.0)
        leverage = portfolio_target_vol * np.sqrt(reciprocal_portfolio_var)
        weights = weights * qis.np_array_to_df_columns(a=leverage, ncols=len(prices.columns))

    if isinstance(volume_costs, float):
        volume_costs = volume_costs*np.ones_like(weights)
    elif isinstance(volume_costs, pd.DataFrame):
        volume_costs = volume_costs.to_numpy()
    else:
        raise NotImplementedError(f"{type(volume_costs)}")

    backtest_outputs = BacktestOutputs(*compute_pnl(weights=weights, returns=returns_np, volume_costs=volume_costs,
                                                    vols=vols))

    weights = pd.DataFrame(weights, index=prices.index, columns=prices.columns)
    backtest_outputs.np_arrays_to_frames(weights=weights, name='American')
    return backtest_outputs
