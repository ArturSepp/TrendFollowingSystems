"""
robust test for the difference of two sharpe ratios following ledoit and wolf (2008)
delta = sr_1 - sr_2 with sr_i = mu_i / sigma_i and sigma_i^2 = gamma_i - mu_i^2, gamma_i = E[r_i^2]
the variance of the moment vector y_t = (r_1t, r_2t, r_1t^2, r_2t^2) is estimated with a
bartlett-kernel hac estimator, the standard error follows by the delta method,
and the two-sided p-value uses the normal limit of the studentised difference
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
# packages
import numpy as np
import pandas as pd
from typing import NamedTuple, Optional
from scipy.stats import norm


class SharpeDiffTest(NamedTuple):
    """
    annualised sharpe ratios and their difference, with the hac t-statistic and p-value
    """
    sr1_an: float
    sr2_an: float
    diff_an: float
    se_an: float
    t_stat: float
    p_value: float
    n_obs: int
    n_lags: int


def sharpe_difference_test(returns1: pd.Series,
                           returns2: pd.Series,
                           n_lags: Optional[int] = None,  # bartlett lags, default floor(4*(T/100)^(2/9))
                           af: float = 12.0  # annualisation factor of the return frequency
                           ) -> SharpeDiffTest:
    """
    test H0: sr(returns1) = sr(returns2) on paired return series

    Parameters
    ----------
    returns1, returns2: pd.Series
        periodic returns on a common calendar, joined on the index intersection with nans dropped
    n_lags: Optional[int]
        bartlett kernel truncation, the newey-west automatic rule when None
    af: float
        annualisation factor of the return frequency for reporting, the t-statistic is scale-invariant

    Returns
    -------
    SharpeDiffTest with annualised levels and the studentised difference

    Raises
    ------
    ValueError on misaligned inputs, short samples, or degenerate variances
    """
    if not isinstance(returns1, pd.Series) or not isinstance(returns2, pd.Series):
        raise ValueError(f"returns must be pd.Series, got {type(returns1)!r}, {type(returns2)!r}")
    joint = pd.concat([returns1.rename('r1'), returns2.rename('r2')], axis=1).dropna()
    n_obs = len(joint.index)
    if n_obs < 24:
        raise ValueError(f"joint sample must have at least 24 observations, got {n_obs!r}")
    r = joint.to_numpy()
    mu = np.mean(r, axis=0)
    gamma = np.mean(np.square(r), axis=0)
    var = gamma - np.square(mu)
    if np.any(var <= 1e-12 * gamma):
        raise ValueError(f"degenerate return variance relative to scale, got {var!r}")
    sigma = np.sqrt(var)
    sr = mu / sigma

    # delta-method gradient of sr_1 - sr_2 in (mu_1, mu_2, gamma_1, gamma_2)
    grad = np.array([gamma[0] / sigma[0] ** 3,
                     -gamma[1] / sigma[1] ** 3,
                     -0.5 * mu[0] / sigma[0] ** 3,
                     0.5 * mu[1] / sigma[1] ** 3])

    # hac covariance of the demeaned moment vector with a bartlett kernel
    y = np.column_stack([r[:, 0] - mu[0], r[:, 1] - mu[1],
                         np.square(r[:, 0]) - gamma[0], np.square(r[:, 1]) - gamma[1]])
    if n_lags is None:
        n_lags = int(np.floor(4.0 * (n_obs / 100.0) ** (2.0 / 9.0)))
    psi = y.T @ y / n_obs
    for lag in np.arange(1, n_lags + 1):
        weight = 1.0 - lag / (n_lags + 1.0)
        gamma_l = y[lag:].T @ y[:-lag] / n_obs
        psi = psi + weight * (gamma_l + gamma_l.T)

    se = float(np.sqrt(grad @ psi @ grad / n_obs))
    diff = float(sr[0] - sr[1])
    t_stat = diff / se
    p_value = float(2.0 * (1.0 - norm.cdf(np.abs(t_stat))))
    sqrt_af = np.sqrt(af)
    return SharpeDiffTest(sr1_an=float(sqrt_af * sr[0]), sr2_an=float(sqrt_af * sr[1]),
                          diff_an=float(sqrt_af * diff), se_an=float(sqrt_af * se),
                          t_stat=float(t_stat), p_value=p_value, n_obs=n_obs, n_lags=int(n_lags))
