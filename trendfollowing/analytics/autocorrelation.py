"""
population autocorrelation functions of white noise, ar-1, and arfima processes
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
# packages
import numpy as np
from scipy.signal import lfilter
from scipy.special import gamma as sp_gamma, hyp2f1


def population_acf(n_lags: int = 250,
                   phi: float = 0.0,  # ar-1 coefficient, |phi| < 1
                   d: float = 0.0,  # arfima fractional order, |d| < 0.5
                   ) -> np.ndarray:
    """
    population autocorrelation rho(m), m = 0..n_lags, with rho(0) = 1
    white noise: rho(m) = delta_{m=0}; ar-1: rho(m) = phi^m
    arfima(0,d,0): rho(m) = prod_{k=1..m} (k-1+d)/(k-d) (hosking 1981)
    arfima(1,d,0): sowell (1992) closed form via hyp2f1, normalised by gamma(0)
    """
    if not np.abs(phi) < 1.0:
        raise ValueError(f"phi must satisfy |phi| < 1, got {phi!r}")
    if not np.abs(d) < 0.5:
        raise ValueError(f"d must satisfy |d| < 0.5, got {d!r}")
    lags = np.arange(n_lags + 1)
    if np.isclose(d, 0.0):
        if np.isclose(phi, 0.0):
            rho = np.zeros(n_lags + 1)
            rho[0] = 1.0
        else:
            rho = np.power(phi, lags)
    elif np.isclose(phi, 0.0):
        # stable recursion rho(m) = rho(m-1) * (m-1+d) / (m-d)
        rho = np.ones(n_lags + 1)
        for m in np.arange(1, n_lags + 1):
            rho[m] = rho[m - 1] * (m - 1.0 + d) / (m - d)
    else:
        # sowell (1992) autocovariance of arfima(1,d,0) with unit innovation variance
        # the gamma-function ratio is computed by the stable recursion ratio0(h) = ratio0(h-1)*(h-1+d)/(h-d)
        c0 = sp_gamma(1.0 - 2.0 * d) / np.square(sp_gamma(1.0 - d))
        ratio1 = 1.0 / ((1.0 - phi) * hyp2f1(1.0, 1.0 + d, 1.0 - d, phi))
        gammas = np.zeros(n_lags + 1)
        ratio0 = 1.0  # = gamma(1-d)/gamma(d) * gamma(h+d)/gamma(1+h-d) at h = 0
        for h in lags:
            if h > 0:
                ratio0 = ratio0 * (h - 1.0 + d) / (h - d)
            enumerator = hyp2f1(1.0, d + h, 1.0 - d + h, phi) + hyp2f1(1.0, d - h, 1.0 - d - h, phi) - 1.0
            gammas[h] = c0 * ratio1 * ratio0 * enumerator
        rho = gammas / gammas[0]
    return rho

def compute_psi_nu(rho: np.ndarray,
                   nu: float
                   ) -> float:
    """
    psi_nu = sum_{m>=1} nu^m rho(m) = phi_nu - 1, truncated at len(rho)-1 lags
    """
    if not 0.0 < nu < 1.0:
        raise ValueError(f"nu must be in (0, 1), got {nu!r}")
    if not np.isclose(rho[0], 1.0):
        raise ValueError(f"rho[0] must equal 1, got {rho[0]!r}")
    nu_powers = np.power(nu, np.arange(1, len(rho)))
    return float(np.sum(nu_powers * rho[1:]))

def power_autocorr(delta: float,  # arfima fractional order, |delta| < 0.5; 0 selects the ar-1 branch
                   phi: float = 0.0,  # ar-1 coefficient, |phi| < 1
                   n: int = 100  # number of lags
                   ) -> np.ndarray:
    """
    ar-1 branch (delta=0) returns autocorrelation powers phi^h with lag 0 equal to one
    arfima branches return the autocovariance gamma(h) with lag 0 set to zero, the convention used by expected_pnl_arfima
    """
    if not np.abs(phi) < 1.0:
        raise ValueError(f"phi must satisfy |phi| < 1, got {phi!r}")
    if not np.abs(delta) < 0.5:
        raise ValueError(f"delta must satisfy |delta| < 0.5, got {delta!r}")
    if n < 1:
        raise ValueError(f"n must be at least 1, got {n!r}")
    if delta == 0.0:  # ar-1
        acf = np.cumprod(phi * np.ones(n)) / phi  # = 1, phi, phi^2,...
    else:
        acf = np.zeros(n)
        sigma0 = sp_gamma(1.0 - 2.0 * delta) / (sp_gamma(1.0 - delta)**2)
        ratio = sp_gamma(1. - delta) / sp_gamma(delta)
        if np.isclose(phi, 0.0):
            for h in np.arange(n):
                acf[h] = ratio * sp_gamma(h+delta) / sp_gamma(1.0+h-delta)
            acf[0] = 0.0
        else:
            ratio1 = 1.0 / ((1.0 - phi) * hyp2f1(1.0, 1.0 + delta, 1.0 - delta, phi))

            def arfima_1d(k):
                ratio0 = ratio * sp_gamma(k+delta) / sp_gamma(1.0+k-delta)
                enumerator = (hyp2f1(1, k+delta, 1.0-delta+k, phi) + hyp2f1(1, delta-k, 1.0-delta-k, phi) -1.0)
                return ratio0 *ratio1 * enumerator

            for h in np.arange(n):
                acf[h] = arfima_1d(k=h)
            acf[0] = 0.0
        acf = sigma0*acf
    return acf


def ma_weights(phi: float = 0.0,  # ar-1 coefficient, |phi| < 1
               d: float = 0.0,  # arfima fractional order, |d| < 0.5
               n_lags: int = 8000,  # truncation of the ma expansion
               ) -> np.ndarray:
    """
    normalised moving-average weights of the arfima(1,d,0) process, sum psi^2 = 1
    fractional weights pi_j = Gamma(j+d)/(Gamma(j+1)Gamma(d)) by the recursion pi_j = pi_{j-1}*(j-1+d)/j with pi_0 = 1
    the ar part applies 1/(1 - phi*L), so psi = pi convolved with phi^k, normalised to a unit sum of squares
    """
    if not np.abs(phi) < 1.0:
        raise ValueError(f"phi must satisfy |phi| < 1, got {phi!r}")
    if not np.abs(d) < 0.5:
        raise ValueError(f"d must satisfy |d| < 0.5, got {d!r}")
    pi = np.ones(n_lags)
    for j in range(1, n_lags):
        pi[j] = pi[j - 1] * (j - 1.0 + d) / j
    psi = lfilter([1.0], [1.0, -phi], pi)
    return psi / np.sqrt(np.sum(np.square(psi)))
