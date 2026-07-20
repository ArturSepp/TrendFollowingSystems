"""
closed-form skewness of aggregated european tf returns under white noise
daily return f_t = S_{t-1} * z_t with the unit-variance signal S_{t-1} = sum_j w_j z_{t-j}
and z_t iid N(0,1); skewness is invariant to the loading l and to sigma_target
key lemma: E[f_t^2 f_{t-h}] = 2 w_h R_S(h) with R_S the signal autocorrelation, so the
third moment of the T-period return F_T = sum_t f_t is 6 sum_h (T-h) w_h R_S(h), while
Var[F_T] = T exactly (strategy returns are serially uncorrelated under white noise)
ewma filter (w_h = sqrt(1-nu^2) nu^{h-1}, R_S(h) = nu^h) gives the closed form
skew(T) = 6 nu [T(1-nu^2) - 1 + nu^{2T}] / ((1-nu^2)^{3/2} T^{3/2})
master curve: skew ~ 6 nu u(x) with x = (1-nu^2) T and u(x) = (x-1+exp(-x))/x^{3/2},
peak at x* = 2.1491 (root of 2x(1-exp(-x)) = 3(x-1+exp(-x))), ceiling 6 u(x*) = 2.4143
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
# packages
import numpy as np
from scipy.optimize import brentq
from typing import Union
# project
from trendfollowing.analytics.filters import span_to_nu


def aggregated_third_moment_white_noise(signal_weights: np.ndarray,
                                        signal_acf: np.ndarray,
                                        horizon: int
                                        ) -> float:
    """
    third moment of the T-period return for a generic unit-variance linear signal
    E[F_T^3] = 6 sum_{h=1}^{T-1} (T-h) w_h R_S(h) from the lemma E[f_t^2 f_{t-h}] = 2 w_h R_S(h)
    signal_weights are w_1, w_2, ... and signal_acf is R_S(1), R_S(2), ...
    """
    if horizon < 1:
        raise ValueError(f"horizon must be at least 1, got {horizon!r}")
    if len(signal_weights) != len(signal_acf):
        raise ValueError(f"signal_weights and signal_acf must have equal length, "
                         f"got {len(signal_weights)!r} and {len(signal_acf)!r}")
    n_lags = min(horizon - 1, len(signal_weights))
    if n_lags < 1:
        return 0.0
    h = np.arange(1, n_lags + 1)
    return float(6.0 * np.sum((horizon - h) * signal_weights[:n_lags] * signal_acf[:n_lags]))


def skewness_white_noise(horizon: Union[int, np.ndarray],
                         span: float
                         ) -> Union[float, np.ndarray]:
    """
    closed-form skewness of the T-period return of the single-filter european system
    skew(T) = 6 nu [T(1-nu^2) - 1 + nu^{2T}] / ((1-nu^2)^{3/2} T^{3/2}), zero at T=1,
    positive for T >= 2, decaying as 6 nu / sqrt((1-nu^2) T)
    """
    nu = span_to_nu(span=span)
    t = np.asarray(horizon, dtype=float)
    if np.any(t < 1):
        raise ValueError(f"horizon must be at least 1, got {horizon!r}")
    one_m_nu2 = 1.0 - nu * nu
    skew = 6.0 * nu * (t * one_m_nu2 - 1.0 + nu ** (2.0 * t)) / (one_m_nu2 ** 1.5 * t ** 1.5)
    return float(skew) if np.isscalar(horizon) else skew


def skewness_master_curve(x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    large-span master curve u(x) = (x - 1 + exp(-x)) / x^{3/2} with x = (1-nu^2) T,
    so skew(T) ~ 6 nu u((1-nu^2) T): one curve for all spans
    """
    x = np.asarray(x, dtype=float)
    if np.any(x <= 0.0):
        raise ValueError(f"x must be positive, got {x!r}")
    return (x - 1.0 + np.exp(-x)) / x ** 1.5


def skewness_peak_horizon(span: float) -> float:
    """
    horizon of the maximal skewness in the large-span limit, T* = x*/(1-nu^2) with
    x* = 2.1491 the root of 2x(1-exp(-x)) = 3(x-1+exp(-x)); T* is about 0.54 span
    """
    nu = span_to_nu(span=span)
    x_star = brentq(lambda x: 2.0 * x * (1.0 - np.exp(-x)) - 3.0 * (x - 1.0 + np.exp(-x)), 1.0, 4.0)
    return float(x_star / (1.0 - nu * nu))
