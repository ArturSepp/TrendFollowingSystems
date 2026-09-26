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

