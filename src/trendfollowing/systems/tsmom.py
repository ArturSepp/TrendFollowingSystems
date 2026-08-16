"""
implementation of the time series momentum (tsmom) system: the normalized sum of
signs of volatility-normalized period returns over a lookback of periods,
generalizing moskowitz-ooi-pedersen momentum, with volatility-targeted sizing
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
import numpy as np
import pandas as pd
import qis as qis
from qis.utils.df_freq import df_resample_at_int_index
from qis.utils.np_ops import set_nans_for_warmup_period
from typing import Optional, Union, Tuple
from trendfollowing.systems.backtest_utils import (compute_pnl,
                                             compute_vol_norm_returns,
                                             BacktestOutputs,
                                             compute_vol_target_weight)


def compute_tsmom_signal_weight(returns: pd.DataFrame,
                                num_ra_returns: int = 22,
                                num_periods: int = 12,
                                vol_span: int = 33,
                                vol_target: float = 0.15,
                                annualization_factor: float = 260
                                ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    tsmom signal and weights: the signs of period returns averaged over
    num_periods with sqrt normalization, scaled by the volatility-target
    weight (vol_target / vol_t)
    """
    vol_norm_returns = compute_vol_norm_returns(returns=returns.to_numpy(), vol_span=vol_span)
    vol_norm_returns = pd.DataFrame(vol_norm_returns, index=returns.index, columns=returns.columns)
    signals = np.sqrt(num_ra_returns)*df_resample_at_int_index(df=np.sign(vol_norm_returns), func=np.nanmean, sample_size=num_ra_returns)
    signals = np.sqrt(num_periods)*signals.rolling(num_periods).mean()
    vol_target_weight, vols = compute_vol_target_weight(returns=returns.to_numpy(), vol_span=vol_span,
                                                        vol_target=vol_target, annualization_factor=annualization_factor)
    # need to reindex at singal index
    vol_target_weight = pd.DataFrame(vol_target_weight, index=returns.index, columns=returns.columns).reindex(index=signals.index, method='ffill')
    vols = pd.DataFrame(vols, index=returns.index, columns=returns.columns).reindex(index=signals.index, method='ffill')

    weights = vol_target_weight.multiply(signals)

    # ffill weights at returns index
    weights = weights.reindex(index=returns.index, method='ffill')
    signals = signals.reindex(index=returns.index, method='ffill')
    vols = vols.reindex(index=returns.index, method='ffill')
    return weights, signals, vols


def run_tsmom_system(prices: pd.DataFrame,
                     num_ra_returns: int = 10,
                     num_periods: int = 10,
                     vol_span: int = 33,
                     vol_target: float = 0.00435,
                     portfolio_covar_span: Optional[int] = None,
                     portfolio_target_vol: float = 0.15,
                     annualization_factor: float = 260.0,
                     volume_costs: Union[float, pd.DataFrame] = 0.0020,  # assume flat across contracts
                     warmup_period: Optional[int] = 250 # monthly basis
                     ) -> BacktestOutputs:

    """
    backtest of the tsmom system on a price panel with optional portfolio-level
    volatility targeting, warmup masking, and volume-based costs
    """
    returns = qis.to_returns(prices, is_first_zero=False)
    weights, signal, vols = compute_tsmom_signal_weight(returns=returns,
                                                num_ra_returns=num_ra_returns,
                                                num_periods=num_periods,
                                                vol_span=vol_span,
                                                vol_target=vol_target,
                                                annualization_factor=annualization_factor)

    if portfolio_covar_span is not None:
        portfolio_var = qis.compute_portfolio_var_np(returns=returns.to_numpy(),
                                                     weights=weights.to_numpy(),
                                                     span=portfolio_covar_span)
        reciprocal_portfolio_var = np.reciprocal(annualization_factor*portfolio_var, where=portfolio_var > 0.0)
        leverage = portfolio_target_vol * np.sqrt(reciprocal_portfolio_var)
        weights = weights * qis.np_array_to_df_columns(a=leverage, ncols=len(prices.columns))

    if warmup_period is not None:
        weights = set_nans_for_warmup_period(a=weights, warmup_period=warmup_period)

    if isinstance(volume_costs, float):
        volume_costs = volume_costs*np.ones_like(weights)
    elif isinstance(volume_costs, pd.DataFrame):
        volume_costs = volume_costs.reindex(index=weights.index, method='ffill')
        volume_costs = volume_costs.to_numpy()
    else:
        raise NotImplementedError(f"{type(volume_costs)}")

    backtest_outputs = BacktestOutputs(*compute_pnl(weights=weights.to_numpy(), returns=returns.to_numpy(),
                                                    volume_costs=volume_costs, vols=vols.to_numpy()))
    weights = pd.DataFrame(weights, index=prices.index, columns=prices.columns)
    backtest_outputs.np_arrays_to_frames(weights=weights, name='TSMOM')

    return backtest_outputs
