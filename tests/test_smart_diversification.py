import pytest
pytest.importorskip('papers.smart_diversification.replication.gaussian_null',
                    reason='companion-paper folder not present in this checkout')
"""
tests for the smart diversification analytics: kappa constants, null values, additivity, aggregation, frontier
"""
# packages
import numpy as np
import pandas as pd
# project
from papers.smart_diversification.replication.gaussian_null import (compute_kappa,
                                                                           compute_null_regime_contributions,
                                                                           compute_convexity_premium,
                                                                           compute_regime_sharpe_decomposition,
                                                                           compute_portfolio_bear_sharpe,
                                                                           compute_blend_frontier)


def test_kappa_constants():
    assert np.isclose(compute_kappa(periods_per_year=4.0), 0.4866, atol=1e-4)
    assert np.isclose(compute_kappa(periods_per_year=12.0), 0.8429, atol=1e-4)


def test_null_contributions_sum_to_sr():
    for sr, rho in [(0.63, 0.0), (0.5, 1.0), (0.45, -0.6)]:
        bear, normal, bull = compute_null_regime_contributions(sr=sr, rho=rho)
        assert np.isclose(bear + normal + bull, sr)
    bear, _, _ = compute_null_regime_contributions(sr=0.63, rho=0.0)
    assert np.isclose(bear, 0.16 * 0.63)


def test_convexity_premium_zero_under_null():
    bear, _, _ = compute_null_regime_contributions(sr=0.5, rho=0.9)
    assert np.isclose(compute_convexity_premium(sr_bear=bear, sr=0.5, rho=0.9), 0.0)


def test_decomposition_additivity_on_random_sample():
    rng = np.random.default_rng(11)
    r_b = pd.Series(rng.standard_normal(200))
    r_a = pd.Series(0.02 + 0.3 * r_b.to_numpy() + rng.standard_normal(200))
    decomposition = compute_regime_sharpe_decomposition(strategy_returns=r_a, benchmark_returns=r_b)
    assert np.isclose(decomposition[['bear', 'normal', 'bull']].sum(), decomposition['total'])


def test_portfolio_aggregation_identity():
    weights = np.array([0.4, 0.6])
    vols = np.array([0.10, 0.15])
    srs = np.array([0.50, 0.63])
    rhos = np.array([1.0, 0.0])
    cps = np.array([0.0, 0.30])
    rho_assets = 0.0
    cov = np.outer(weights * vols, weights * vols) * np.array([[1.0, rho_assets], [rho_assets, 1.0]])
    portfolio_vol = float(np.sqrt(cov.sum()))
    bear_p = compute_portfolio_bear_sharpe(weights=weights, vols=vols, srs=srs, rhos=rhos, cps=cps,
                                           portfolio_vol=portfolio_vol)
    # direct evaluation of the same identity
    kappa = compute_kappa()
    rw = weights * vols / portfolio_vol
    direct = 0.16 * float(np.sum(rw * srs)) - kappa * float(np.sum(rw * rhos)) + float(np.sum(rw * cps))
    assert np.isclose(bear_p, direct)


def test_blend_frontier_endpoints_and_improvement():
    frontier = compute_blend_frontier(sr_b=0.5, vol_b=0.10, sr_a=0.63, vol_a=0.15, rho=0.0, cp_a=0.30)
    assert np.isclose(frontier['sharpe'].iloc[0], 0.5)
    assert np.isclose(frontier['sharpe'].iloc[-1], 0.63)
    assert np.isclose(frontier['sharpe'].max(), np.hypot(0.5, 0.63), atol=5e-3)
    # improvement condition sr_a > rho*sr_b holds, so the sharpe ratio rises at x=0
    assert frontier['sharpe'].iloc[1] > frontier['sharpe'].iloc[0]


def test_regime_states_frequencies():
    import numpy as np, pandas as pd
    from papers.smart_diversification.replication.regime_analysis import compute_regime_states
    rng = np.random.default_rng(3)
    nav = pd.Series(100.0 * np.exp(np.cumsum(0.0002 + 0.01 * rng.standard_normal(6000))),
                    index=pd.bdate_range('2000-01-03', periods=6000))
    states = compute_regime_states(benchmark_nav=nav, freq='QE')
    shares = states.value_counts(normalize=True)
    assert abs(shares['bear'] - 0.16) < 0.05 and abs(shares['bull'] - 0.16) < 0.05


def test_block_bootstrap_cp_runs():
    import numpy as np, pandas as pd
    from papers.smart_diversification.replication.regime_analysis import block_bootstrap_cp
    rng = np.random.default_rng(5)
    r_b = pd.Series(rng.standard_normal(120))
    r_a = pd.Series(0.03 + 0.1 * r_b + rng.standard_normal(120))
    boot = block_bootstrap_cp(strategy_returns=r_a, benchmark_returns=r_b, n_boot=300)
    assert boot['cp_ci_low'] < boot['cp_ci_high'] and boot['cp_se'] > 0.0


def test_realized_blend_frontier_endpoints():
    import numpy as np, pandas as pd
    from papers.smart_diversification.replication.regime_analysis import (compute_realized_blend_frontier,
                                                                                 compute_regime_sharpe_decomposition,
                                                                                 to_periodic_returns)
    rng = np.random.default_rng(9)
    idx = pd.bdate_range('2000-01-03', periods=6000)
    nav_b = pd.Series(100.0 * np.exp(np.cumsum(0.0002 + 0.01 * rng.standard_normal(6000))), index=idx)
    nav_o = pd.Series(100.0 * np.exp(np.cumsum(0.0003 + 0.01 * rng.standard_normal(6000))), index=idx)
    frontier = compute_realized_blend_frontier(benchmark_nav=nav_b, overlay_nav=nav_o)
    joint = to_periodic_returns(pd.concat([nav_b, nav_o], axis=1))
    d0 = compute_regime_sharpe_decomposition(strategy_returns=joint.iloc[:, 0], benchmark_returns=joint.iloc[:, 0])
    assert abs(frontier['sharpe'].iloc[0] - d0['total']) < 1e-10
