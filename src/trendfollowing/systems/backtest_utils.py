"""
shared utilities of the tf system backtests: volatility-normalized returns,
volatility-target weights, pnl with volume-based costs, and the container for
backtest outputs
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""

import numpy as np
import pandas as pd
import qis as qis
from qis.utils.np_ops import np_cumsum, np_nanstd, np_nansum
from dataclasses import dataclass
from inspect import signature
from numba import njit
from typing import Tuple, Union


@dataclass
class BacktestOutputs:
    """
    pandas wrapper for outputs from compute_pnl
    """

    portfolio_pnl: Union[np.ndarray, pd.Series]
    portfolio_pnl_net: Union[np.ndarray, pd.Series]
    portfolio_turnover: Union[np.ndarray, pd.Series]
    portfolio_vol_turnover: Union[np.ndarray, pd.Series]
    portfolio_cost: Union[np.ndarray, pd.Series]
    instrument_pnl: Union[np.ndarray, pd.DataFrame]
    instrument_pnl_net: Union[np.ndarray, pd.DataFrame]
    weights: Union[np.ndarray, pd.DataFrame] = None
    signals: Union[np.ndarray, pd.DataFrame] = None

    def np_arrays_to_frames(
        self, weights: pd.DataFrame, signals: np.ndarray = None, name: str = 'European'
    ) -> None:
        """
        map numpy arrays to dataframe using weights index and columns
        """
        self.weights = weights
        self.portfolio_pnl = pd.Series(self.portfolio_pnl, index=weights.index, name=name)
        self.portfolio_pnl_net = pd.Series(self.portfolio_pnl_net, index=weights.index, name=name)
        self.portfolio_turnover = pd.Series(self.portfolio_turnover, index=weights.index, name=name)
        self.portfolio_vol_turnover = pd.Series(
            self.portfolio_vol_turnover, index=weights.index, name=name
        )
        self.portfolio_cost = pd.Series(self.portfolio_cost, index=weights.index, name=name)
        self.instrument_pnl = pd.DataFrame(
            self.instrument_pnl, index=weights.index, columns=weights.columns
        )
        self.instrument_pnl_net = pd.DataFrame(
            self.instrument_pnl_net, index=weights.index, columns=weights.columns
        )
        if signals is not None:
            self.signals = pd.DataFrame(signals, index=weights.index, columns=weights.columns)


@njit
def compute_pnl(
    weights: np.ndarray, returns: np.ndarray, volume_costs: np.ndarray, vols: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    compute p&l of weights
    weights, returns, volume_costs must have same dimension
    """
    if weights.ndim == 1:
        instrument_pnl = weights[:-1] * returns[1:]
        instrument_pnl = np.append([np.nan], instrument_pnl)  # add zero row

        abs_weight_change = np.abs(weights[1:] - weights[:-1])
        abs_weight_change = np.append([np.nan], abs_weight_change)  # add zero row
        vol_abs_weight_change = abs_weight_change * vols

        instrument_costs = abs_weight_change * volume_costs
        instrument_pnl_net = instrument_pnl - instrument_costs

        portfolio_pnl = instrument_pnl
        portfolio_pnl_net = instrument_pnl_net
        portfolio_turnover = abs_weight_change
        portfolio_vol_turnover = vol_abs_weight_change
        portfolio_cost = portfolio_turnover * volume_costs
    else:
        instrument_pnl = weights[:-1, :] * returns[1:, :]  # add zero row
        instrument_pnl = np.concatenate(
            (np.nan * np.ones((1, weights.shape[1])), instrument_pnl), axis=0
        )

        abs_weight_change = np.abs(weights[1:, :] - weights[:-1, :])
        abs_weight_change = np.concatenate(
            (np.nan * np.ones((1, weights.shape[1])), abs_weight_change), axis=0
        )
        vol_abs_weight_change = abs_weight_change * vols

        instrument_costs = abs_weight_change * volume_costs
        instrument_pnl_net = instrument_pnl - instrument_costs

        portfolio_pnl = np_nansum(instrument_pnl, axis=1, keep_dim=False)[0]
        portfolio_pnl_net = np_nansum(instrument_pnl_net, axis=1, keep_dim=False)[0]

        portfolio_turnover = np_nansum(abs_weight_change, axis=1, keep_dim=False)[0]
        portfolio_vol_turnover = np_nansum(vol_abs_weight_change, axis=1, keep_dim=False)[0]
        portfolio_cost = np_nansum(instrument_costs, axis=1, keep_dim=False)[0]

    # pnl = np.cumsum(pnl_paths)
    portfolio_pnl = np.cumprod(1.0 + portfolio_pnl)
    portfolio_pnl_net = np.cumprod(1.0 + portfolio_pnl_net)

    return (
        portfolio_pnl,
        portfolio_pnl_net,
        portfolio_turnover,
        portfolio_vol_turnover,
        portfolio_cost,
        instrument_pnl,
        instrument_pnl_net,
    )


@njit
def compute_vol(returns: np.ndarray, vol_span: float = 31.0, is_lag1: bool = True) -> np.ndarray:
    """
    daily EWMA volatility, seeded with the first finite squared return of each column

    Zero is a valid seed; no volatility floor is applied. Missing observations follow
    the QIS forward-fill rule. The optional one-row lag repeats the first estimate
    at row zero. Warmup masking remains the responsibility of the system runners.
    """
    ewm_lambda = 1.0 - 2.0 / (vol_span + 1.0)
    squared_returns = np.square(returns)
    # qis.compute_ewm_vol and set_init_dim1 are Python wrappers, unavailable inside njit.
    # Select their X0 seed here; the EWMA recursion itself remains delegated to QIS.
    if returns.ndim == 1:
        init_value = 0.0
        for value in squared_returns:
            if np.isfinite(value):
                init_value = value
                break
    else:
        init_value = np.zeros(returns.shape[1])
        for column in range(returns.shape[1]):
            for row in range(returns.shape[0]):
                if np.isfinite(squared_returns[row, column]):
                    init_value[column] = squared_returns[row, column]
                    break
    vols = qis.ewm_recursion(a=squared_returns, ewm_lambda=ewm_lambda, init_value=init_value)

    if is_lag1:
        if returns.ndim == 1:  # add extra row 0
            vols = np.concatenate((np.array([vols[0]]), vols[:-1]))
        else:
            # vols = np.concatenate((vols[0, :].reshape(1, -1), vols[:-1, :]), axis=0)
            vols = vols.copy()  # to fix numba
            vols = np.append(vols[0, :].reshape(1, -1), vols[:-1, :], axis=0)

    vols = np.sqrt(vols)
    return vols


@njit
def compute_vol_norm_returns(returns: np.ndarray, vol_span: float = 31.0) -> np.ndarray:
    """
    compute return_t / ewma_vol_{t-1}
    """
    vols_1 = compute_vol(returns=returns, vol_span=vol_span, is_lag1=True)
    vol_norm_returns = returns / vols_1
    return vol_norm_returns


@njit
def compute_vol_target_weight(
    returns: np.ndarray,
    vol_span: int = 33,
    vol_target: float = 0.15,
    annualization_factor: float = 260,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    compute pnl of weight = (vol_target /  vol_{t}) * signal t
    """
    vols = np.sqrt(annualization_factor) * compute_vol(
        returns=returns, vol_span=vol_span, is_lag1=False
    )
    weights = vol_target / vols
    return weights, vols


# QIS compute_portfolio_var_np before covar0 cannot accept a causal seed; its pandas
# wrapper also calls that noncausal kernel. RiskModel is absent at the supported floor.
# This bounded-memory compatibility kernel follows QIS's MIT-licensed recursion
# (see NOTICE), changing only its initial covariance. Newer QIS uses its own kernel below.
@njit
def _compute_portfolio_var_zero_seed(
    returns: np.ndarray, weights: np.ndarray, span: float
) -> np.ndarray:
    """Compatibility for the seed-less QIS API, with its existing gap/weight rules."""
    ewm_lambda = 1.0 - 2.0 / (span + 1.0)
    ewm_lambda_1 = 1.0 - ewm_lambda
    last_covar = np.zeros((returns.shape[1], returns.shape[1]))
    finite_weights = np.where(np.isfinite(weights), weights, 0.0)
    portfolio_var = np.zeros(returns.shape[0])
    for idx in range(returns.shape[0]):
        row = returns[idx]
        covar = ewm_lambda_1 * np.outer(row, row) + ewm_lambda * last_covar
        covar = np.where(np.isfinite(covar), covar, ewm_lambda * last_covar)
        last_covar = covar
        weights_t = np.ascontiguousarray(finite_weights[idx])
        portfolio_var[idx] = weights_t.T @ covar @ weights_t
    return portfolio_var


def _compute_causal_portfolio_var(
    returns: np.ndarray, weights: np.ndarray, span: float
) -> np.ndarray:
    """Current-weight portfolio variance, explicitly zero-seeded on every QIS version.

    Keep the existing same-row covariance/weight pairing and missing-data decay.
    Detect the seed argument rather than relying on a QIS version or default.
    """
    if 'covar0' in signature(qis.compute_portfolio_var_np).parameters:
        return qis.compute_portfolio_var_np(
            returns=returns, weights=weights, span=span,
            covar0=np.zeros((returns.shape[1], returns.shape[1])),
        )
    return _compute_portfolio_var_zero_seed(returns=returns, weights=weights, span=span)


# @njit
def compute_path_stats(
    pnl_paths: np.ndarray, annualization_factor: float = 260.0
) -> Tuple[np.ndarray, ...]:
    """
    compute cumulative pnl
    """
    pnl_paths0 = pnl_paths.copy()
    pnl_paths0[np.isnan(pnl_paths)] = 0.0  # fill nans
    cum_pnl = np_cumsum(pnl_paths0, axis=0)
    total_pnl = cum_pnl[-1, :]
    nonnan_years = np.sum(~np.isnan(pnl_paths), axis=0) / annualization_factor
    pnl_an = total_pnl / nonnan_years
    vol_an = (
        np.sqrt(annualization_factor) * np_nanstd(pnl_paths, axis=0).flatten()
    )  # vol of original paths with nans
    sharpe = pnl_an / vol_an
    return total_pnl, pnl_an, vol_an, sharpe
