"""
guards for the closed-form skewness of aggregated white-noise returns:
exact equality with brute-force Isserlis enumeration, the general lemma,
positivity, and the peak location
"""
# packages
import numpy as np
import pytest
# project
from trendfollowing.analytics.filters import span_to_nu
from trendfollowing.analytics.skewness import (aggregated_third_moment_white_noise,
                                               skewness_white_noise,
                                               skewness_master_curve,
                                               skewness_peak_horizon)


def brute_force_third_moment(horizon: int, nu: float) -> float:
    """E[F_T^3] by exact Isserlis enumeration over the joint Gaussian of signals and returns"""
    t_n = horizon
    dim = 2 * t_n
    cov = np.zeros((dim, dim))
    for a in range(t_n):
        for b in range(t_n):
            cov[a, b] = nu ** abs(a - b)
    for a in range(t_n):
        for b in range(1, t_n + 1):
            if b <= a:
                cov[a, t_n + b - 1] = cov[t_n + b - 1, a] = np.sqrt(1 - nu * nu) * nu ** (a - b)
    for b in range(t_n):
        cov[t_n + b, t_n + b] = 1.0

    def pairings(idx):
        if not idx:
            yield []
            return
        first = idx[0]
        for i in range(1, len(idx)):
            for rest in pairings(idx[1:i] + idx[i + 1:]):
                yield [(first, idx[i])] + rest

    total = 0.0
    for t in range(1, t_n + 1):
        for s in range(1, t_n + 1):
            for u in range(1, t_n + 1):
                six = tuple([t - 1, t_n + t - 1, s - 1, t_n + s - 1, u - 1, t_n + u - 1])
                total += sum(np.prod([cov[i, j] for i, j in p]) for p in pairings(six))
    return total


@pytest.mark.parametrize("horizon,span", [(2, 20.0), (3, 20.0), (4, 5.0), (5, 20.0)])
def test_closed_form_equals_brute_force_isserlis(horizon, span):
    """the closed form matches exact Isserlis enumeration to machine precision"""
    nu = span_to_nu(span=span)
    closed = skewness_white_noise(horizon=horizon, span=span) * horizon ** 1.5
    brute = brute_force_third_moment(horizon=horizon, nu=nu)
    assert abs(closed - brute) < 1e-10


def test_general_lemma_reduces_to_ewma_closed_form():
    """6 sum (T-h) w_h R_S(h) with ewma weights equals the closed form"""
    span, horizon = 63.0, 500
    nu = span_to_nu(span=span)
    h = np.arange(1, 5001)
    w = np.sqrt(1 - nu * nu) * nu ** (h - 1)
    r_s = nu ** h.astype(float)
    general = aggregated_third_moment_white_noise(signal_weights=w, signal_acf=r_s, horizon=horizon)
    closed = skewness_white_noise(horizon=horizon, span=span) * horizon ** 1.5
    assert abs(general - closed) < 1e-8


def test_zero_at_one_period_and_positive_after():
    """skew(1) = 0 and skew(T) > 0 for T >= 2, for a range of spans"""
    for span in [2.0, 5.0, 20.0, 63.0, 250.0]:
        assert abs(skewness_white_noise(horizon=1, span=span)) < 1e-14
        skews = skewness_white_noise(horizon=np.arange(2, 60), span=span)
        assert np.all(skews > 0.0)


def test_peak_location_matches_argmax():
    """the continuous peak horizon tracks the argmax of the closed form"""
    for span in [20.0, 63.0, 250.0]:
        horizons = np.arange(1, int(20 * span))
        skews = skewness_white_noise(horizon=horizons, span=span)
        t_argmax = horizons[np.argmax(skews)]
        t_star = skewness_peak_horizon(span=span)
        assert abs(t_star - t_argmax) <= max(2.0, 0.06 * span)


def test_master_curve_collapse():
    """skew(T)/(6 nu) approaches u((1-nu^2) T) for large spans: the collapse error is
    O(1/span) from the exponent mismatch of nu^{2T} against exp(-(1-nu^2)T)"""
    span = 250.0
    nu = span_to_nu(span=span)
    horizons = np.array([20, 60, 130, 250, 500, 1000])
    exact = skewness_white_noise(horizon=horizons, span=span) / (6.0 * nu)
    master = skewness_master_curve(x=(1.0 - nu * nu) * horizons)
    assert np.max(np.abs(exact - master)) < 2e-2
    # and the collapse tightens with the span
    span2 = 1000.0
    nu2 = span_to_nu(span=span2)
    horizons2 = (horizons * span2 / span).astype(int)
    exact2 = skewness_white_noise(horizon=horizons2, span=span2) / (6.0 * nu2)
    master2 = skewness_master_curve(x=(1.0 - nu2 * nu2) * horizons2)
    assert np.max(np.abs(exact2 - master2)) < np.max(np.abs(exact - master))
