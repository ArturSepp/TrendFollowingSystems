"""
tests for tf_model.paper.sharpe: variance preservation, closed forms, consistency with expected-return formulas
"""
# packages
import numpy as np
# project
from trendfollowing.analytics.filters import span_to_nu
from trendfollowing.analytics.autocorrelation import population_acf, compute_psi_nu
from trendfollowing.analytics.sharpe import (compute_signal_moments, compute_annualised_sharpe,
                                             sharpe_white_noise, sharpe_white_noise_approx,
                                             sharpe_ar1, sharpe_ar1_approx, expected_annual_return)
from trendfollowing.analytics.expected_return import expected_pnl_white_noise, expected_pnl_ar1


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
        mine = expected_annual_return(rho=rho_wn, long_span=span, sr_underlying=0.5, vol_target=0.15)
        his = expected_pnl_white_noise(long_span=span, mean=0.5, vol_target=0.15)
        assert np.isclose(mine, his)
    rho_ar = population_acf(n_lags=3000, phi=0.05)
    for span in [21.0, 250.0]:
        mine = expected_annual_return(rho=rho_ar, long_span=span, sr_underlying=0.0, vol_target=0.15)
        his = expected_pnl_ar1(phi=0.05, long_span=span, mean=0.0, vol_target=0.15)
        assert np.isclose(mine, his)


def test_sharpe_independent_of_variance_scale_zero_drift():
    rho = population_acf(n_lags=2000, phi=0.05)
    sr1 = compute_annualised_sharpe(rho=rho, long_span=63.0, variance=1.0)
    sr2 = compute_annualised_sharpe(rho=rho, long_span=63.0, variance=1.5)
    assert np.isclose(sr1, sr2)


def test_approximations_close_to_exact():
    assert np.isclose(sharpe_ar1(phi=0.05, long_span=21.0), sharpe_ar1_approx(phi=0.05, long_span=21.0), atol=5e-3)
    assert np.isclose(sharpe_white_noise(long_span=21.0, sr_underlying=0.25),
                      sharpe_white_noise_approx(long_span=21.0, sr_underlying=0.25), atol=5e-3)
