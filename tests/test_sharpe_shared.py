"""
guards for the shared Sharpe estimator: the formula identity, bit-parity with the
expressions it replaced, and the cross-repo parity with the qis SharpeConvention
proposal when a patched qis is installed (skips on released qis)
"""
# packages
import numpy as np
import pandas as pd
import pytest
# project
from trendfollowing.analytics.sharpe import compute_realized_sharpe


def test_formula_identity_numpy_both_ddof():
    """the shared estimator is exactly sqrt(af)*mean/std for both variance conventions"""
    rng = np.random.RandomState(3)
    x = 0.001 + 0.01 * rng.randn(1560)
    for ddof in (0, 1):
        direct = float(np.sqrt(260.0) * np.mean(x) / np.std(x, ddof=ddof))
        shared = compute_realized_sharpe(returns=x, af=260.0, ddof=ddof)
        assert shared == direct  # bit-identical, same operations in the same order


def test_formula_identity_pandas():
    """pandas containers reproduce the pandas mean/std expression they replaced"""
    rng = np.random.RandomState(4)
    idx = pd.date_range('2000-12-31', periods=200, freq='QE')
    df = pd.DataFrame(0.01 + 0.05 * rng.randn(200, 2), index=idx, columns=['A', 'B'])
    direct = np.sqrt(4.0) * df.mean() / df.std(ddof=1)
    shared = compute_realized_sharpe(returns=df, af=4.0, ddof=1)
    pd.testing.assert_series_equal(shared, direct)


def test_parity_with_qis_canonical_estimator():
    """the trendfollowing estimator equals qis.compute_sharpe_arithmetic once the
    SharpeConvention proposal lands in qis (skips on released qis)"""
    perf_stats = pytest.importorskip("qis.perfstats.perf_stats")
    if not hasattr(perf_stats, "compute_sharpe_arithmetic"):
        pytest.skip("installed qis predates the SharpeConvention proposal")
    rng = np.random.RandomState(5)
    idx = pd.date_range('1990-12-31', periods=140, freq='QE')
    r = pd.Series(0.01 + 0.05 * rng.randn(140), index=idx)
    ours = float(compute_realized_sharpe(returns=r, af=4.0, ddof=1))
    theirs = float(perf_stats.compute_sharpe_arithmetic(returns=r, af=4.0, ddof=1))
    assert abs(ours - theirs) < 1e-14


def test_regime_decomposition_parity_with_patched_qis():
    """Paper B's arithmetic regime decomposition equals the qis ARITHMETIC regime branch
    at q = (0.16, 0.84) exactly (skips on released qis or without the companion folder)"""
    config = pytest.importorskip("qis.perfstats.config")
    if not hasattr(config, "SharpeConvention"):
        pytest.skip("installed qis predates the SharpeConvention proposal")
    gaussian_null = pytest.importorskip("papers.smart_diversification.replication.gaussian_null")
    import qis
    rng = np.random.RandomState(7)
    idx = pd.date_range('1990-12-31', periods=140, freq='QE')
    bench = pd.Series(0.015 + 0.05 * rng.randn(140), index=idx).add(1.0).cumprod().rename('Balanced')
    a1 = pd.Series(0.010 + 0.06 * rng.randn(140), index=idx).add(1.0).cumprod().rename('A1')
    prices = pd.concat([bench, a1], axis=1)
    sampled = prices.pct_change().dropna()
    paper = gaussian_null.compute_regime_sharpe_decomposition(strategy_returns=sampled['A1'],
                                                              benchmark_returns=sampled['Balanced'],
                                                              periods_per_year=4.0, tail_prob=0.16)
    perf_params = qis.PerfParams(freq='QE', sharpe_convention=config.SharpeConvention.ARITHMETIC)
    table = qis.compute_bnb_regimes_pa_perf_table(prices=prices, benchmark='Balanced', freq='QE',
                                                  q=np.array([0.0, 0.16, 0.84, 1.0]),
                                                  perf_params=perf_params)
    qis_row = table.loc['A1', [c for c in table.columns
                               if 'Sharpe' in c and any(r in c for r in ('Bear', 'Normal', 'Bull'))]]
    diff = np.abs(np.array([paper['bear'], paper['normal'], paper['bull']]) - qis_row.to_numpy())
    assert diff.max() < 1e-14


def test_local_fallback_equals_standalone():
    """the strict-inequality fallback and the qis 5.0.7 standalone agree on continuous
    data, so gaussian_null gives one answer whichever qis version is installed
    (skips when the installed qis predates the standalone)"""
    rc = pytest.importorskip("qis.perfstats.regime_classifier")
    if not hasattr(rc, "compute_regime_sharpe_decomposition"):
        pytest.skip("installed qis predates the returns-level standalone")
    rng = np.random.RandomState(13)
    idx = pd.date_range('1990-12-31', periods=140, freq='QE')
    r_b = pd.Series(0.015 + 0.05 * rng.randn(140), index=idx)
    r_a = pd.Series(0.010 + 0.06 * rng.randn(140), index=idx)
    tail = 0.16
    # the local strict-inequality construction
    q_low, q_high = r_b.quantile(tail), r_b.quantile(1.0 - tail)
    sigma = r_a.std(ddof=1)
    local = {'Bear-Sharpe': np.sqrt(4.0) * (r_b < q_low).mean() * r_a[r_b < q_low].mean() / sigma,
             'Bull-Sharpe': np.sqrt(4.0) * (r_b > q_high).mean() * r_a[r_b > q_high].mean() / sigma}
    standalone = rc.compute_regime_sharpe_decomposition(returns=r_a, benchmark_returns=r_b,
                                                        af=4.0, q=np.array([0.0, tail, 1.0 - tail, 1.0]))
    for key, value in local.items():
        assert abs(standalone[key] - value) < 1e-14
