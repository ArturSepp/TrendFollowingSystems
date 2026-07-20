"""
ewma filter parameters: span-to-nu mapping and variance-preserving long-short loadings
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
# packages
import numpy as np
from typing import Optional, Tuple


def span_to_nu(span: float) -> float:
    """
    ewma smoothing parameter from span: nu = 1 - 2/(span+1)
    """
    if span <= 0.0:
        raise ValueError(f"span must be positive, got {span!r}")
    return 1.0 - 2.0 / (span + 1.0)

def compute_ewm_long_short_weights(long_span: float = 63,
                                   short_span: Optional[float] = None  # None for the single-filter system
                                   ) -> Tuple[float, float]:
    """
    variance-preserving loadings of the (long-short) ewma filter
    single filter: w_l = sqrt((1+nu)/(1-nu)), w_s = 0; long-short: the raw-filter
    difference is normalised by q = D^{-1/2} with D = 1/(1-nu_l^2) + 1/(1-nu_s^2)
    - 2/(1-nu_l*nu_s), then each leg carries its unit-variance loading
    """
    long_lambda = span_to_nu(span=long_span)
    if short_span is not None:  # use short + long filter
        short_lambda = span_to_nu(span=short_span)
        short_lambda2 = np.square(short_lambda)
        long_lambda2 = np.square(long_lambda)
        covar = np.sqrt(1.0 / (1.0 - long_lambda2) + 1.0 / (1.0 - short_lambda2) - 2.0 / (1.0 - long_lambda * short_lambda))
        weight_long = 1.0 / (np.sqrt(1.0 - long_lambda2) * covar)
        weight_short = 1.0 / (np.sqrt(1.0 - short_lambda2) * covar)
        load_long = np.sqrt((1.0 + long_lambda) / (1.0 - long_lambda))
        load_short = np.sqrt((1.0 + short_lambda) / (1.0 - short_lambda))
        weight_long = weight_long * load_long
        weight_short = weight_short * load_short
    else:
        weight_long = np.sqrt((1.0 + long_lambda) / (1.0 - long_lambda))
        weight_short = 0.0
    return weight_long, weight_short
