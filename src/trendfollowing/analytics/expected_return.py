"""
expected annual return and turnover of the european tf system per process (paper corollaries)
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
# packages
import numpy as np
from typing import Optional
# project
from trendfollowing.analytics.filters import span_to_nu, compute_ewm_long_short_weights
from trendfollowing.analytics.autocorrelation import power_autocorr


def expected_pnl_white_noise(long_span: float,
                             short_span: Optional[float] = None,
                             mean: float = 0.0,
                             vol_target: float = 0.15,
                             annualization_factor: float = 260.0
                             ) -> float:
    """
    expected annual return of the european system under white noise (drift channel only)
    F = sigma_target/sqrt(a) * (w_l - w_s) * mu^2: the autocorrelation channel is zero
    """
    weight_long, weight_short = compute_ewm_long_short_weights(long_span=long_span, short_span=short_span)
    if short_span is not None:
        pnl = (weight_long - weight_short) * mean**2
    else:
        pnl = weight_long * mean**2
    pnl = vol_target * pnl / np.sqrt(annualization_factor)
    return pnl

def expected_pnl_ar1(phi: float,
                     long_span: float,
                     short_span: Optional[float] = None,
                     vol_target: float = 0.15,
                     mean: float = 0.0,
                     annualization_factor: float = 260.0
                     ) -> float:
    """
    expected annual return of the european system under ar-1 (paper corollary)
    per leg, the autocorrelation channel sums the geometric series:
    sum_m nu^m phi^m = nu*phi/(1-nu*phi), scaled by h = sqrt(a)*sigma_target*(1-nu)/nu,
    which reduces to sqrt(a)*sigma_target * w * phi*(1-nu)/(1-nu*phi) per unit loading;
    the drift channel adds the white-noise term when mean > 0
    """
    weight_long, weight_short = compute_ewm_long_short_weights(long_span=long_span, short_span=short_span)
    long_nu = span_to_nu(span=long_span)
    if short_span is not None:
        short_nu = span_to_nu(span=short_span)
        pnl_long = phi*(1.0-long_nu) / (1.0-long_nu*phi)
        pnl_short = phi*(1.0-short_nu) / (1.0-short_nu*phi)
        pnl = weight_long * pnl_long - weight_short * pnl_short
    else:
        pnl = weight_long * phi*(1.0-long_nu) / (1.0-long_nu*phi)
    pnl = np.sqrt(annualization_factor)*vol_target * pnl
    if mean > 0.0:
        mean_pnl = expected_pnl_white_noise(long_span=long_span,
                                            short_span=short_span,
                                            mean=mean,
                                            vol_target=vol_target,
                                            annualization_factor=annualization_factor)
        pnl += mean_pnl
    return pnl

def expected_pnl_ma1(phi: float,
                     long_span: float,
                     short_span: Optional[float] = None,
                     vol_target: float = 0.15,
                     mean: float = 0.0,
                     annualization_factor: float = 260.0
                     ) -> float:
    """
    expected annual return of the european system under ma-1
    only the first autocorrelation is non-zero, rho(1) = phi/(1+phi^2), so the
    autocorrelation channel per leg is w * nu*rho(1) * (1-nu)/nu = w * phi*(1-nu)/(1+phi^2)
    """
    weight_long, weight_short = compute_ewm_long_short_weights(long_span=long_span, short_span=short_span)
    long_nu = span_to_nu(span=long_span)
    if short_span is not None:
        short_nu = span_to_nu(span=short_span)
        pnl_long = phi*(1.0-long_nu) / (1.0+phi*phi)
        pnl_short = phi*(1.0-short_nu) / (1.0+phi*phi)
        pnl = weight_long * pnl_long - weight_short * pnl_short
    else:
        pnl = weight_long * phi*(1.0-long_nu) / (1.0+phi*phi)
    pnl = np.sqrt(annualization_factor)*vol_target * pnl
    if mean > 0.0:
        mean_pnl = expected_pnl_white_noise(long_span=long_span,
                                            short_span=short_span,
                                            mean=mean,
                                            vol_target=vol_target,
                                            annualization_factor=annualization_factor)
        pnl += mean_pnl
    return pnl

def expected_pnl_arfima(delta: float,
                        long_span: float,
                        short_span: Optional[float] = None,
                        phi: float = 0.0,
                        vol_target: float = 0.15,
                        mean: float = 0.0,
                        annualization_factor: float = 260.0
                        ) -> float:
    """
    expected annual return of the european system under arfima(1,delta,0)
    the autocorrelation channel evaluates h * sum_m nu^m gamma(m) on the sowell
    autocovariances from power_autocorr (truncated at 150 lags), per filter leg,
    with h = (1-nu)/nu scaling; the drift channel adds the white-noise term when mean > 0
    """
    pk = power_autocorr(delta=delta, phi=phi, n=150)

    def compute_nu_filter(span: float) -> float:
        nu = span_to_nu(span=span)
        pnl = 0.0
        nu_m = 1.0
        for pk_ in pk:
            pnl += nu_m*pk_
            nu_m *= nu
        norm = (1.0-nu) / nu
        return norm*pnl

    weight_long, weight_short = compute_ewm_long_short_weights(long_span=long_span, short_span=short_span)

    if short_span is not None:
        pnl_long = compute_nu_filter(span=long_span)
        pnl_short = compute_nu_filter(span=short_span)
        pnl = weight_long*pnl_long - weight_short*pnl_short
    else:
        pnl = weight_long * compute_nu_filter(span=long_span)

    pnl = (np.sqrt(annualization_factor)*vol_target)*pnl

    if mean > 0.0:
        mean_pnl = expected_pnl_white_noise(long_span=long_span,
                                            short_span=short_span,
                                            mean=mean,
                                            vol_target=vol_target,
                                            annualization_factor=annualization_factor)
        pnl += mean_pnl

    return pnl

def expected_turnover(long_span: float,
                      short_span: Optional[float] = None,
                      annualization_factor: float = 260.0,
                      vol_target: float = 0.15
                      ) -> float:
    """
    expected annualised turnover of the european system under serial independence
    U = 2*a*sigma_target*sqrt(zeta/pi) with zeta the variance of the one-step signal
    increment: zeta = 1 - nu for the single filter, and the q-normalised raw-filter
    difference variance for the long-short filter (paper eq tur_ls)
    """
    nu_long = span_to_nu(span=long_span)
    coeff = 2.0*annualization_factor*vol_target*np.sqrt(1.0/np.pi)
    if short_span is None:
        turnover = coeff*np.sqrt(1.0 - nu_long)
    else:
        nu_short = span_to_nu(span=short_span)
        # variance-preserving normalization q = D^{-1/2} of the raw-filter difference
        d_norm = 1.0/(1.0-nu_long**2) + 1.0/(1.0-nu_short**2) - 2.0/(1.0-nu_long*nu_short)
        q = d_norm ** -0.5
        # signal increment variance: the z_t terms cancel, leaving q^2 * var of the raw-filter difference
        zeta = 0.5 * q**2 * ((1.0-nu_long)/(1.0+nu_long) + (1.0-nu_short)/(1.0+nu_short)
                             - 2.0*(1.0-nu_long)*(1.0-nu_short)/(1.0-nu_long*nu_short))
        turnover = coeff * np.sqrt(zeta)


    return turnover
