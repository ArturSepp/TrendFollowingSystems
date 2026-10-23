"""Causal volatility seeds, timing, and their use by the system backtests."""

from inspect import signature

import numpy as np
import pandas as pd
import pytest
import qis

from trendfollowing.systems.american import run_american_system
from trendfollowing.systems.backtest_utils import (
    _compute_causal_portfolio_var,
    compute_vol,
    compute_vol_norm_returns,
    compute_vol_target_weight,
)
from trendfollowing.systems.european import run_european_tf_system
from trendfollowing.systems.tsmom import run_tsmom_system


def _pandas_vol(returns: np.ndarray, span: float, lag: bool) -> np.ndarray:
    """Independent reference: uncentered EWMA, seeded at each column's first square."""
    values = pd.Series(returns) if returns.ndim == 1 else pd.DataFrame(returns)
    variance = values.pow(2).ewm(span=span, adjust=False, ignore_na=True).mean().to_numpy()
    if lag:
        # Keep the existing convention: row zero repeats rather than becoming NaN.
        variance = np.concatenate((variance[:1], variance[:-1]), axis=0)
    return np.sqrt(variance)


@pytest.fixture
def ragged_returns() -> np.ndarray:
    return np.array([
        [np.nan, 0.0, np.nan, 0.0, -0.01, np.inf],
        [np.nan, 0.02, np.nan, 0.0, 0.02, np.nan],
        [0.03, -0.01, np.nan, 0.0, np.nan, -0.04],
        [0.00, np.nan, np.nan, 0.0, -0.03, np.inf],
        [-0.02, 0.03, np.nan, 0.0, 0.01, np.nan],
        [np.nan, -0.02, np.nan, 0.0, 0.04, 0.01],
        [0.01, 0.00, np.nan, 0.0, -0.02, -np.inf],
    ])


@pytest.mark.parametrize('lag', [False, True])
@pytest.mark.parametrize('column', [None, 0, 1, 2, 3, 4, 5])
def test_volatility_matches_causal_pandas_reference(ragged_returns, column, lag):
    """Ragged starts, nonfinite gaps, zero seeds, and all-missing markets are retained."""
    returns = ragged_returns if column is None else ragged_returns[:, column].copy()
    original = returns.copy()
    expected = _pandas_vol(returns, span=5.5, lag=lag)
    actual = compute_vol(returns, vol_span=5.5, is_lag1=lag)
    np.testing.assert_allclose(actual, expected, rtol=1e-14, atol=0.0, equal_nan=True)
    np.testing.assert_array_equal(returns, original)


@pytest.mark.parametrize('lag', [False, True])
@pytest.mark.parametrize('ndim', [1, 2])
def test_volatility_does_not_use_future_returns(ndim, lag):
    rng = np.random.default_rng(313)
    returns = rng.normal(0.001, 0.01, size=(128, 3))
    returns[:4, 1] = np.nan
    returns[20, 2] = np.nan
    if ndim == 1:
        returns = returns[:, 0].copy()
    cut = 64
    changed = returns.copy()
    changed[cut:] *= 50.0
    original_vol = compute_vol(returns, vol_span=33, is_lag1=lag)
    changed_vol = compute_vol(changed, vol_span=33, is_lag1=lag)
    prefix_vol = compute_vol(returns[:cut].copy(), vol_span=33, is_lag1=lag)
    np.testing.assert_array_equal(original_vol[:cut], changed_vol[:cut])
    np.testing.assert_array_equal(original_vol[:cut], prefix_vol)


@pytest.mark.parametrize('ndim', [1, 2])
def test_normalization_is_lagged_but_target_sizing_uses_current_volatility(ndim):
    returns = np.array([[0.01, -0.02], [0.04, 0.01], [-0.03, 0.03], [0.02, -0.04]])
    if ndim == 1:
        returns = returns[:, 0].copy()
    lagged_vol = _pandas_vol(returns, span=5, lag=True)
    current_vol = _pandas_vol(returns, span=5, lag=False)
    actual_lagged = compute_vol(returns, vol_span=5, is_lag1=True)
    actual_current = compute_vol(returns, vol_span=5, is_lag1=False)
    np.testing.assert_array_equal(actual_lagged[0], actual_current[0])
    np.testing.assert_array_equal(actual_lagged[1:], actual_current[:-1])
    np.testing.assert_allclose(
        compute_vol_norm_returns(returns, vol_span=5), returns / lagged_vol, rtol=1e-14
    )
    weights, annual_vol = compute_vol_target_weight(
        returns, vol_span=5, vol_target=0.2, annualization_factor=252
    )
    np.testing.assert_allclose(annual_vol, np.sqrt(252) * current_vol, rtol=1e-14)
    np.testing.assert_allclose(weights, 0.2 / (np.sqrt(252) * current_vol), rtol=1e-14)


RUNNERS = {
    'european': (run_european_tf_system, {'long_span': 30, 'short_span': 5}),
    'american': (run_american_system, {'long_span': 30, 'short_span': 5}),
    'tsmom': (run_tsmom_system, {'num_ra_returns': 5, 'num_periods': 4}),
}


@pytest.fixture
def prices() -> pd.DataFrame:
    rng = np.random.default_rng(314)
    returns = rng.normal(0.001, 0.01, size=(360, 2))
    values = 100.0 * np.exp(np.cumsum(returns, axis=0))
    values[:12, 1] = np.nan
    return pd.DataFrame(
        values, index=pd.bdate_range('2000-01-03', periods=len(values)), columns=['A', 'B']
    )


@pytest.fixture(params=['installed', 'legacy'])
def covariance_backend(request, monkeypatch):
    """Exercise old QIS's seed-less API even when the installed default is causal."""
    if request.param == 'legacy':
        installed = qis.compute_portfolio_var_np

        def legacy(returns, weights, span=None, ewm_lambda=0.94):
            # QIS 5.0.9 starts from an EWMA covariance fitted to the entire input.
            # Keep its old signature: passing a newer keyword must not be required.
            if 'covar0' in signature(installed).parameters:
                seed = qis.compute_ewm_covar(a=returns, span=span)
                return installed(returns=returns, weights=weights, span=span,
                                 ewm_lambda=ewm_lambda, covar0=seed)
            return installed(returns=returns, weights=weights, span=span,
                             ewm_lambda=ewm_lambda)

        monkeypatch.setattr(qis, 'compute_portfolio_var_np', legacy)
    return request.param


@pytest.mark.parametrize('span', [1.0, 5.5, 30.0])
def test_portfolio_variance_matches_independent_zero_seed_reference(covariance_backend, span):
    """Pandas EWM of pair products verifies the seed, gap decay and current-weight timing."""
    returns = np.array([
        [np.nan, np.nan], [0.02, np.nan], [-0.01, 0.03],
        [np.nan, -0.02], [np.inf, 0.01], [0.0, 0.0], [0.04, -0.03],
    ])
    weights = np.array([
        [1.0, 1.0], [2.0, np.nan], [0.5, -1.0],
        [1.5, 0.4], [np.inf, -0.3], [0.0, 0.0], [-2.0, 1.0],
    ])
    with np.errstate(invalid='ignore'):
        products = returns[:, :, None] * returns[:, None, :]
    products = np.where(np.isfinite(products), products, 0.0)
    # Prepend the zero state before asking pandas for its adjust=False recursion.
    covariance = pd.DataFrame(np.vstack((np.zeros(4), products.reshape(-1, 4))))
    covariance = covariance.ewm(span=span, adjust=False).mean().iloc[1:].to_numpy()
    covariance = covariance.reshape(-1, 2, 2)
    finite_weights = np.where(np.isfinite(weights), weights, 0.0)
    expected = np.einsum('ti,tij,tj->t', finite_weights, covariance, finite_weights)
    actual = _compute_causal_portfolio_var(returns, weights, span)
    np.testing.assert_allclose(actual, expected, rtol=2e-14, atol=1e-18)
    np.testing.assert_array_equal(actual[[0, 5]], 0.0)
    np.testing.assert_array_equal(
        actual[:4], _compute_causal_portfolio_var(returns[:4], weights[:4], span)
    )


@pytest.mark.parametrize('name', list(RUNNERS))
@pytest.mark.parametrize('portfolio_span', [None, 30])
def test_system_history_is_unchanged_by_future_prices(
    prices, name, portfolio_span, covariance_backend
):
    run_system, parameters = RUNNERS[name]
    cut = 180
    changed = prices.copy()
    phase = np.arange(len(prices) - cut)[:, None]
    changed.iloc[cut:] *= np.exp(0.2 * np.sin(phase * np.array([[0.73, 1.13]])))
    kwargs = dict(
        **parameters, vol_span=80, warmup_period=40,
        volume_costs=0.001, portfolio_covar_span=portfolio_span,
    )
    # Retain the full date grid: TSMOM's block sampling is anchored to the final date.
    original = run_system(prices=prices, **kwargs)
    shocked = run_system(prices=changed, **kwargs)
    assert np.any(original.weights.iloc[80:cut].fillna(0.0).to_numpy() != 0.0)
    for attribute in (
        'weights', 'portfolio_pnl', 'portfolio_pnl_net', 'portfolio_cost',
        'portfolio_turnover', 'portfolio_vol_turnover',
    ):
        np.testing.assert_array_equal(
            getattr(original, attribute).iloc[:cut].to_numpy(),
            getattr(shocked, attribute).iloc[:cut].to_numpy(),
            err_msg=f'{name}: {attribute} depends on future prices',
        )


@pytest.mark.parametrize('name', ['european', 'tsmom'])
@pytest.mark.parametrize('portfolio_span', [None, 30])
def test_warmup_still_counts_finite_weights_per_market(prices, name, portfolio_span):
    run_system, parameters = RUNNERS[name]
    kwargs = dict(**parameters, vol_span=33, portfolio_covar_span=portfolio_span)
    raw = run_system(prices=prices, warmup_period=None, **kwargs).weights.to_numpy()
    warmup = 13
    masked = run_system(prices=prices, warmup_period=warmup, **kwargs).weights.to_numpy()
    expected = raw.copy()
    for column in range(raw.shape[1]):
        finite_rows = np.flatnonzero(np.isfinite(raw[:, column]))
        assert len(finite_rows) > warmup
        expected[:finite_rows[warmup], column] = np.nan
    np.testing.assert_array_equal(masked, expected)


@pytest.mark.parametrize('portfolio_span', [None, 30])
def test_american_warmup_still_counts_finite_prices(portfolio_span):
    values = np.column_stack((100.0 + np.arange(40), 200.0 + np.arange(40)))
    values[:7, 1] = np.nan
    prices = pd.DataFrame(values, index=pd.bdate_range('2000-01-03', periods=40))
    warmup = 8
    weights = run_american_system(
        prices=prices, long_span=7, short_span=2, vol_span=4,
        signal_atr_multiplier=0.0, warmup_period=warmup,
        portfolio_covar_span=portfolio_span,
    ).weights.to_numpy()
    for column, start in enumerate([0, 7]):
        np.testing.assert_array_equal(weights[:start + warmup, column], 0.0)
        assert weights[start + warmup, column] > 0.0
