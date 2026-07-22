"""
implementation of the european trend-following system: continuous positions from a
variance-preserving ewma filter (single or long-short) of volatility-normalized
returns, with volatility-targeted sizing per instrument and optional portfolio-level
volatility targeting
the system behind the paper's closed forms for the expected return, the sharpe
ratio, and the skewness of aggregated returns
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
import numpy as np
import pandas as pd
import qis as qis
from qis.utils.np_ops import set_nans_for_warmup_period
from numba import njit
from typing import Optional, Union, Tuple
from trendfollowing.systems.backtest_utils import compute_pnl, compute_vol_norm_returns, BacktestOutputs, \
    compute_vol_target_weight


@njit
def compute_tf_signal(returns: np.ndarray,
                      vol_norm_returns: np.ndarray = None,
                      long_span: float = 33,
                      short_span: Optional[int] = None,
                      vol_span: float = 33
                      ) -> np.ndarray:
    """
    ewma signal of volatility-normalized returns: the single filter for
    short_span None and the long-short raw-filter difference otherwise
    """
    if vol_norm_returns is None:
        vol_norm_returns = compute_vol_norm_returns(returns=returns, vol_span=vol_span)
    if returns.ndim == 1:
        init_value = 0.0
    else:
        init_value = np.zeros(vol_norm_returns.shape[1])
    signal = qis.compute_ewm_long_short(a=vol_norm_returns,
                                        long_span=long_span,
                                        short_span=short_span,
                                        init_value=init_value)
    # signal[np.isnan(vol_norm_returns)] = np.nan  # make nans - necessary when using init_value
    signal = np.where(np.isnan(vol_norm_returns) == False, signal, np.nan)
    return signal


@njit
def compute_tf_signal_weight(returns: np.ndarray,
                             long_span: float = 31.0,
                             short_span: Optional[float] = None,
                             vol_span: int = 33,
                             vol_target: float = 0.30,
                             annualization_factor: float = 260,
                             signal_cap: Optional[float] = None
                             ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    signal and per-instrument weights of the european system:
    weight_t = (vol_target / vol_t) * signal_t, with an optional cap on the signal
    """
    signal = compute_tf_signal(returns=returns,
                               long_span=long_span,
                               short_span=short_span,
                               vol_span=vol_span)
    if signal_cap is not None:
        signal = np.clip(signal, -signal_cap, signal_cap)
    vol_target_weight, vols = compute_vol_target_weight(returns=returns, vol_span=vol_span, vol_target=vol_target, annualization_factor=annualization_factor)
    weights = vol_target_weight * signal
    return weights, signal, vols


#@njit  # cannot work
def compute_tf_strat_pnl(returns: np.ndarray,
                         long_span: float = 31.0,
                         short_span: Optional[float] = None,
                         vol_span: int = 33,
                         vol_target: float = 0.15,
                         annualization_factor: float = 260
                         ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    compute pnl of weight = (vol_target /  vol_{t}) * signal t
    """
    weights, signals, vols = compute_tf_signal_weight(returns=returns,
                                                      long_span=long_span,
                                                      short_span=short_span,
                                                      vol_span=vol_span,
                                                      vol_target=vol_target,
                                                      annualization_factor=annualization_factor)
    # add zero row so that dim[0] equals to dim[0] of returns
    if weights.ndim == 1:
        pnl = weights[:-1] * returns[1:]
        pnl = np.append([np.nan], pnl)  # add nan row
    else:
        pnl = weights[:-1, :] * returns[1:, :]
        pnl = np.concatenate((np.nan*np.ones((1, weights.shape[1])), pnl), axis=0)

    return pnl, weights, vols


def run_european_tf_system(prices: pd.DataFrame,
                           long_span: int = 31,
                           short_span: Optional[int] = None,
                           vol_span: int = 33,
                           vol_target: float = 0.3,
                           portfolio_covar_span: Optional[int] = None,
                           portfolio_target_vol: float = 0.15,
                           annualization_factor: float = 260.0,
                           volume_costs: Union[float, pd.DataFrame] = 0.0020,  # assume flat across contracts
                           warmup_period: Optional[int] = 250,
                           signal_cap: Optional[float] = 3.0,
                           weight_cap: Optional[float] = 5.0
                           ) -> BacktestOutputs:

    """
    backtest of the european system on a price panel: builds the signal and
    volatility-target weights, applies optional portfolio-level volatility
    targeting and the warmup mask, and returns gross and net pnl with
    turnover and costs
    """
    returns_np = qis.to_returns(prices, is_log_returns=True, is_first_zero=False).to_numpy()
    weights, signals, vols = compute_tf_signal_weight(returns=returns_np,
                                                      long_span=long_span,
                                                      short_span=short_span,
                                                      vol_span=vol_span,
                                                      vol_target=vol_target,
                                                      signal_cap=signal_cap)
    if weight_cap is not None:
        weights = np.clip(weights, -weight_cap, weight_cap)

    if portfolio_covar_span is not None:
        portfolio_var = qis.compute_portfolio_var_np(returns=returns_np, weights=weights, span=portfolio_covar_span)
        # np.reciprocal with where= but no out= leaves the masked cells uninitialised (undefined
        # behaviour); pass an initialised zero out so non-positive-variance days get zero leverage
        reciprocal_portfolio_var = np.zeros_like(portfolio_var)
        np.reciprocal(annualization_factor*portfolio_var, where=portfolio_var > 0.0, out=reciprocal_portfolio_var)
        leverage = portfolio_target_vol * np.sqrt(reciprocal_portfolio_var)
        weights = weights * qis.np_array_to_df_columns(a=leverage, ncols=len(prices.columns))

    if warmup_period is not None:
        weights = set_nans_for_warmup_period(a=weights, warmup_period=warmup_period)

    if isinstance(volume_costs, float):
        volume_costs = volume_costs*np.ones_like(weights)
    elif isinstance(volume_costs, pd.DataFrame):
        volume_costs = volume_costs.to_numpy()
    else:
        raise NotImplementedError(f"{type(volume_costs)}")

    backtest_outputs = BacktestOutputs(*compute_pnl(weights=weights, returns=returns_np,
                                                    volume_costs=volume_costs, vols=vols))
    weights = pd.DataFrame(weights, index=prices.index, columns=prices.columns)
    backtest_outputs.np_arrays_to_frames(weights=weights, signals=signals, name='European')

    return backtest_outputs