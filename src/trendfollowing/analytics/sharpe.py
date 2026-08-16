"""
analytical sharpe ratio of the european tf system
daily strategy return: f_t = (l*sigma_target/sqrt(af)) * S_{t-1} * z_t with signal S_{t-1} = filter of {z_{t-1}, z_{t-2}, ...}
we compute E[f_t] and Var[f_t] under jointly gaussian z with population mean mu, variance theta, acf rho(m),
using the isserlis theorem for Var[X*Y]: Var[XY] = sx^2*sy^2 + sxy^2 + mx^2*sy^2 + my^2*sx^2 + 2*mx*my*sxy
annualised sharpe: sr = sqrt(af) * E[f_t] / sqrt(Var[f_t])
key results: sr is independent of sigma_target and of the filter loading l
notation follows the paper: nu = 1 - 2/(span+1), psi_nu = sum_{m>=1} nu^m rho(m) = phi_nu - 1
kurtosis extension: Var[f] gains kappa*K_sig with K_sig = sum_{s>=1} psi_s^2 b_{s-1}^2 (paper eq sr_k), gaussian is kappa=0
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
# packages
import numpy as np
import pandas as pd
from scipy.signal import lfilter
from typing import Optional, Tuple, NamedTuple, Union
# project
from trendfollowing.analytics.filters import span_to_nu, compute_ewm_long_short_weights
from trendfollowing.analytics.autocorrelation import population_acf, compute_psi_nu


class SignalMoments(NamedTuple):
    """
    moments of the signal S_{t-1} relative to z: E[S] = mu*s_mean, Var[S] = theta*s_var, Cov(z_t, S_{t-1}) = theta*s_cov
    """
    s_mean: float
    s_var: float
    s_cov: float

def compute_signal_moments(rho: np.ndarray,
                           long_span: float = 250,
                           short_span: Optional[float] = None,  # None for single ewma filter
                           ) -> SignalMoments:
    """
    moments of the variance-preserving (long-short) ewma signal under population acf rho
    single filter with loading l: E[S] = l*mu, Var[S] = theta*l^2*(1-nu)(1+2*psi)/(1+nu), Cov = theta*l*(1-nu)*psi/nu
    long-short: S = l1*L1 - l2*L2 with cross-term Cov(L1,L2) = theta*(1-nu1)(1-nu2)(1+psi1+psi2)/(1-nu1*nu2)
    """
    l1, l2 = compute_ewm_long_short_weights(long_span=long_span, short_span=short_span)
    nu1 = span_to_nu(long_span)
    psi1 = compute_psi_nu(rho=rho, nu=nu1)
    v1 = (1.0 - nu1) * (1.0 + 2.0 * psi1) / (1.0 + nu1)
    c1 = (1.0 - nu1) * psi1 / nu1
    if short_span is None:
        s_mean = l1
        s_var = np.square(l1) * v1
        s_cov = l1 * c1
    else:
        nu2 = span_to_nu(short_span)
        psi2 = compute_psi_nu(rho=rho, nu=nu2)
        v2 = (1.0 - nu2) * (1.0 + 2.0 * psi2) / (1.0 + nu2)
        c2 = (1.0 - nu2) * psi2 / nu2
        cross = (1.0 - nu1) * (1.0 - nu2) * (1.0 + psi1 + psi2) / (1.0 - nu1 * nu2)
        s_mean = l1 - l2
        s_var = np.square(l1) * v1 + np.square(l2) * v2 - 2.0 * l1 * l2 * cross
        s_cov = l1 * c1 - l2 * c2
    return SignalMoments(s_mean=s_mean, s_var=s_var, s_cov=s_cov)

def compute_daily_moments(rho: np.ndarray,
                          long_span: float = 250,
                          short_span: Optional[float] = None,
                          mean: float = 0.0,  # daily mean mu of vol-normalised returns z
                          variance: float = 1.0,  # daily variance theta of z, close to one by construction
                          ) -> Tuple[float, float]:
    """
    daily mean and variance of f_t / c with c = l*sigma_target/sqrt(af), via the isserlis product-variance formula
    E[f/c] = theta*s_cov + mu^2*s_mean
    Var[f/c] = theta*(theta*(s_var + s_cov^2) + mu^2*(s_var + s_mean^2 + 2*s_mean*s_cov))
    """
    if variance <= 0.0:
        raise ValueError(f"variance must be positive, got {variance!r}")
    sm = compute_signal_moments(rho=rho, long_span=long_span, short_span=short_span)
    mean_f = variance * sm.s_cov + np.square(mean) * sm.s_mean
    var_f = variance * (variance * (sm.s_var + np.square(sm.s_cov))
                        + np.square(mean) * (sm.s_var + np.square(sm.s_mean) + 2.0 * sm.s_mean * sm.s_cov))
    return mean_f, var_f

def compute_annualised_sharpe(rho: np.ndarray,
                              long_span: float = 250,
                              short_span: Optional[float] = None,
                              sr_underlying: float = 0.0,  # annualised sharpe of z: sr = sqrt(af)*mu/sqrt(theta)
                              variance: float = 1.0,
                              kappa: float = 0.0,  # excess kurtosis of the innovations, 0 for gaussian
                              ma_weights: Optional[np.ndarray] = None,  # normalised ma weights psi, required when kappa != 0
                              af: float = 260.0,  # annualisation factor
                              ) -> float:
    """
    annualised sharpe of the european tf system: sr = sqrt(af)*E[f]/sqrt(Var[f])
    the scaling c = l*sigma_target/sqrt(af) cancels, so sr is independent of sigma_target and l
    for kappa != 0 the variance gains variance^2*kappa*K_sig with the loading of compute_kurtosis_loading
    """
    mean = sr_underlying * np.sqrt(variance) / np.sqrt(af)
    mean_f, var_f = compute_daily_moments(rho=rho,
                                          long_span=long_span,
                                          short_span=short_span,
                                          mean=mean,
                                          variance=variance)
    if kappa != 0.0:
        if ma_weights is None:
            raise ValueError(f"ma_weights is required for the kurtosis term, got kappa={kappa!r} and ma_weights=None")
        k_sig = compute_kurtosis_loading(ma_weights=ma_weights,
                                         long_span=long_span,
                                         short_span=short_span)
        var_f = var_f + np.square(variance) * kappa * k_sig
    return float(np.sqrt(af) * mean_f / np.sqrt(var_f))

def compute_kurtosis_loading(ma_weights: np.ndarray,
                             long_span: float = 250,
                             short_span: Optional[float] = None,  # None for single ewma filter
                             ) -> float:
    """
    kurtosis loading of the signal: K_sig = sum_{s>=1} psi_s^2 b_{s-1}^2 (paper eq sr_k with the loadings included)
    b_u = l1*c1_u - l2*c2_u with c_u = (1-nu) sum_{m<=u} nu^m psi_{u-m} the filter loading on innovation eps_{t-1-u}
    single filter: K_sig = l1^2 * K_nu with the unit-mass K_nu of eq sr_k

    Parameters
    ----------
    ma_weights: normalised moving-average weights psi of the returns, sum psi^2 = 1
    long_span, short_span: filter spans in days, short_span None for the single filter

    Returns
    -------
    the loading K_sig >= 0

    Raises
    ------
    ValueError if ma_weights is not a one-dimensional unit-norm array
    """
    if ma_weights.ndim != 1 or ma_weights.shape[0] < 2:
        raise ValueError(f"ma_weights must be a 1d array with at least two weights, got shape {ma_weights.shape!r}")
    norm = float(np.sum(np.square(ma_weights)))
    if np.abs(norm - 1.0) > 1e-3:
        raise ValueError(f"ma_weights must satisfy sum psi^2 = 1, got {norm!r}")
    l1, l2 = compute_ewm_long_short_weights(long_span=long_span, short_span=short_span)
    nu1 = span_to_nu(long_span)
    b = l1 * (1.0 - nu1) * lfilter([1.0], [1.0, -nu1], ma_weights)
    if short_span is not None:
        nu2 = span_to_nu(short_span)
        b = b - l2 * (1.0 - nu2) * lfilter([1.0], [1.0, -nu2], ma_weights)
    return float(np.sum(np.square(ma_weights[1:]) * np.square(b[:-1])))


def kurtosis_loading_ar1(phi: float,
                         long_span: float = 250,
                         ) -> float:
    """
    closed form of the unit-mass kurtosis loading K_nu for the ar-1 process (paper eq sr_ar1_k)
    K_nu = (1-nu)^2 (1-phi^2)^2/(phi-nu)^2 * (phi^4/(1-phi^4) - 2 nu phi^3/(1-nu phi^3) + nu^2 phi^2/(1-nu^2 phi^2))
    the signal-level loading of compute_kurtosis_loading equals l1^2 * K_nu for the single filter
    """
    if not np.abs(phi) < 1.0:
        raise ValueError(f"phi must satisfy |phi| < 1, got {phi!r}")
    nu = span_to_nu(long_span)
    bracket = (phi ** 4 / (1.0 - phi ** 4)
               - 2.0 * nu * phi ** 3 / (1.0 - nu * phi ** 3)
               + nu ** 2 * phi ** 2 / (1.0 - nu ** 2 * phi ** 2))
    return float((1.0 - nu) ** 2 * (1.0 - phi ** 2) ** 2 / (phi - nu) ** 2 * bracket)


def sharpe_white_noise(long_span: float = 250,
                       short_span: Optional[float] = None,
                       sr_underlying: float = 0.5,
                       af: float = 260.0
                       ) -> float:
    """
    exact tf sharpe under white noise with drift, from the generic formula with rho = delta_{m=0}
    single filter closed form: sr = sr_z^2*sqrt(span/af) / sqrt(1 + (sr_z^2/af)*(span+1))
    """
    rho = population_acf(n_lags=1)
    return compute_annualised_sharpe(rho=rho,
                                     long_span=long_span,
                                     short_span=short_span,
                                     sr_underlying=sr_underlying,
                                     af=af)

def sharpe_white_noise_approx(long_span: float = 250,
                              sr_underlying: float = 0.5,
                              af: float = 260.0
                              ) -> float:
    """
    leading-order tf sharpe under white noise: sr ~= sr_z^2 * sqrt(span/af)
    """
    return np.square(sr_underlying) * np.sqrt(long_span / af)

def sharpe_ar1(phi: float,
               long_span: float = 250,
               short_span: Optional[float] = None,
               sr_underlying: float = 0.0,
               af: float = 260.0,
               n_lags: int = 1000
               ) -> float:
    """
    exact tf sharpe under ar-1 with coefficient phi, psi_nu = nu*phi/(1-nu*phi)
    """
    rho = population_acf(n_lags=n_lags, phi=phi)
    return compute_annualised_sharpe(rho=rho,
                                     long_span=long_span,
                                     short_span=short_span,
                                     sr_underlying=sr_underlying,
                                     af=af)

def sharpe_ar1_approx(phi: float,
                      long_span: float = 250,
                      af: float = 260.0
                      ) -> float:
    """
    leading-order tf sharpe under zero-drift ar-1: sr ~= 2*phi*sqrt(af)*sqrt(span)/(span+1) ~= 2*phi*sqrt(af/span)
    """
    return 2.0 * phi * np.sqrt(af) * np.sqrt(long_span) / (long_span + 1.0)

def sharpe_arfima(d: float,
                  phi: float = 0.0,
                  long_span: float = 250,
                  short_span: Optional[float] = None,
                  sr_underlying: float = 0.0,
                  af: float = 260.0,
                  n_lags: int = 2000
                  ) -> float:
    """
    exact tf sharpe under arfima(1,d,0) using the sowell acf, truncated at n_lags
    """
    rho = population_acf(n_lags=n_lags, phi=phi, d=d)
    return compute_annualised_sharpe(rho=rho,
                                     long_span=long_span,
                                     short_span=short_span,
                                     sr_underlying=sr_underlying,
                                     af=af)

def expected_annual_return(rho: np.ndarray,
                           long_span: float = 250,
                           short_span: Optional[float] = None,
                           sr_underlying: float = 0.0,
                           vol_target: float = 0.15,
                           af: float = 260.0
                           ) -> float:
    """
    expected annual return af*c*E[f/c] with c = sigma_target/sqrt(af), loadings inside signal moments
    cross-checks the paper corollary: F_1y = c_1y*(phi_nu - 1) + (l*sigma_target/sqrt(af))*sr_z^2
    """
    mean = sr_underlying / np.sqrt(af)
    mean_f, _ = compute_daily_moments(rho=rho,
                                      long_span=long_span,
                                      short_span=short_span,
                                      mean=mean,
                                      variance=1.0)
    return float(af * (vol_target / np.sqrt(af)) * mean_f)


def compute_realized_sharpe(returns: Union[np.ndarray, pd.Series, pd.DataFrame],
                            af: float = 260.0,
                            ddof: int = 1
                            ) -> Union[float, pd.Series]:
    """
    canonical realized Sharpe estimator SR = sqrt(af) * E[f_t] / sqrt(Var[f_t]) on periodic
    simple excess returns, shared by every estimation layer of the papers
    mirrors qis.perfstats.perf_stats.compute_sharpe_arithmetic of the SharpeConvention
    proposal (sharpe_conventions.md section 7); the closed forms of this module are the
    population counterparts of this estimator
    ddof=1 is the sample-variance default; ddof=0 reproduces the population-variance
    estimates of the manuscript's committed attribution exhibits
    """
    if isinstance(returns, np.ndarray):
        return float(np.sqrt(af) * np.mean(returns) / np.std(returns, ddof=ddof))
    elif isinstance(returns, (pd.Series, pd.DataFrame)):
        return np.sqrt(af) * returns.mean() / returns.std(ddof=ddof)
    else:
        raise ValueError(f"returns must be np.ndarray, pd.Series, or pd.DataFrame, got {type(returns)!r}")
