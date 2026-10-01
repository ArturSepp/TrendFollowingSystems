"""
tests for tf_model.paper.sharpe: variance preservation, closed forms, and
consistency with expected-return formulas
"""

# packages
import numpy as np
import pytest

# project
from trendfollowing.analytics.filters import span_to_nu
from trendfollowing.analytics.autocorrelation import population_acf, compute_psi_nu
from trendfollowing.analytics.sharpe import (
    compute_signal_moments,
    compute_annualised_sharpe,
    sharpe_white_noise,
    sharpe_white_noise_approx,
    sharpe_ar1,
    sharpe_ar1_approx,
    expected_annual_return,
)
from trendfollowing.analytics.expected_return import (
    expected_pnl_white_noise,
    expected_pnl_ar1,
    expected_pnl_ma1,
    expected_pnl_arfima,
)


def test_variance_preservation_white_noise():
    rho = population_acf(n_lags=5)
    for span in [5.0, 21.0, 250.0]:
        sm = compute_signal_moments(rho=rho, long_span=span)
        assert np.isclose(sm.s_var, 1.0)
    sm_ls = compute_signal_moments(rho=rho, long_span=250.0, short_span=20.0)
    assert np.isclose(sm_ls.s_var, 1.0)


def test_psi_nu_ar1_closed_form():
    phi, span = 0.05, 63.0
    nu = span_to_nu(span)
    rho = population_acf(n_lags=2000, phi=phi)
    assert np.isclose(compute_psi_nu(rho=rho, nu=nu), nu * phi / (1.0 - nu * phi))


def test_arfima_acf_lag_one():
    d = 0.1
    rho = population_acf(n_lags=3, d=d)
    assert np.isclose(rho[1], d / (1.0 - d))


def test_sowell_acf_finite_and_normalised():
    rho = population_acf(n_lags=2000, phi=-0.05, d=0.1)
    assert np.isfinite(rho).all()
    assert np.isclose(rho[0], 1.0)


def test_expected_return_matches_formulas():
    rho_wn = population_acf(n_lags=5)
    for span in [21.0, 250.0]:
        mine = expected_annual_return(
            rho=rho_wn, long_span=span, sr_underlying=0.5, vol_target=0.15
        )
        his = expected_pnl_white_noise(long_span=span, mean=0.5, vol_target=0.15)
        assert np.isclose(mine, his)
    rho_ar = population_acf(n_lags=3000, phi=0.05)
    for span in [21.0, 250.0]:
        mine = expected_annual_return(
            rho=rho_ar, long_span=span, sr_underlying=0.0, vol_target=0.15
        )
        his = expected_pnl_ar1(phi=0.05, long_span=span, mean=0.0, vol_target=0.15)
        assert np.isclose(mine, his)


@pytest.mark.parametrize("short_span", [None, 20.0])
@pytest.mark.parametrize("mean", [-0.5, 0.5])
def test_drift_channel_either_sign(short_span, mean):
    """the drift channel adds (l*sigma_target/sqrt(af))*mu_an^2 for either sign of the drift"""

    def generic(rho):
        return expected_annual_return(
            rho=rho, long_span=250.0, short_span=short_span, sr_underlying=mean
        )

    kwargs = dict(long_span=250.0, short_span=short_span, mean=mean)
    rho_ar = population_acf(n_lags=2000, phi=0.05)
    rho_ma = np.array([1.0, 0.3 / (1.0 + 0.3**2)])
    rho_fr = population_acf(n_lags=2000, phi=-0.05, d=0.02)
    assert np.isclose(expected_pnl_ar1(phi=0.05, **kwargs), generic(rho_ar), rtol=1e-12)
    assert np.isclose(expected_pnl_ma1(phi=0.3, **kwargs), generic(rho_ma), rtol=1e-12)
    assert np.isclose(
        expected_pnl_arfima(delta=0.02, phi=-0.05, **kwargs), generic(rho_fr), rtol=1e-12
    )


def test_arfima_expected_return_uses_2000_lag_acf():
    """paper section 5.1: psi_nu on the arfima autocorrelations truncated at 2000 lags"""
    for d, phi in [(0.1, 0.0), (0.02, 0.0), (0.02, 0.05), (0.02, -0.05)]:
        rho = population_acf(n_lags=2000, phi=phi, d=d)
        for long_span, short_span in [(5.0, None), (500.0, None), (250.0, 20.0)]:
            mine = expected_annual_return(rho=rho, long_span=long_span, short_span=short_span)
            his = expected_pnl_arfima(
                delta=d, phi=phi, long_span=long_span, short_span=short_span
            )
            assert np.isclose(his, mine, rtol=1e-12, atol=0.0)


def test_arfima_without_long_memory_reduces_to_ar1():
    for phi in [-0.05, 0.0, 0.05]:
        assert np.isclose(
            expected_pnl_arfima(delta=0.0, phi=phi, long_span=63.0),
            expected_pnl_ar1(phi=phi, long_span=63.0),
            rtol=1e-10,
        )


def test_sharpe_independent_of_variance_scale_zero_drift():
    rho = population_acf(n_lags=2000, phi=0.05)
    sr1 = compute_annualised_sharpe(rho=rho, long_span=63.0, variance=1.0)
    sr2 = compute_annualised_sharpe(rho=rho, long_span=63.0, variance=1.5)
    assert np.isclose(sr1, sr2)


def test_approximations_close_to_exact():
    assert np.isclose(
        sharpe_ar1(phi=0.05, long_span=21.0), sharpe_ar1_approx(phi=0.05, long_span=21.0), atol=5e-3
    )
    assert np.isclose(
        sharpe_white_noise(long_span=21.0, sr_underlying=0.25),
        sharpe_white_noise_approx(long_span=21.0, sr_underlying=0.25),
        atol=5e-3,
    )
