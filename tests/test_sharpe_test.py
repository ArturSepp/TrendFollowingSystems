"""
tests for the ledoit-wolf sharpe difference test
"""
# packages
import numpy as np
import pandas as pd
import pytest
# project
from trendfollowing.analytics.sharpe_test import sharpe_difference_test


def test_null_holds_for_equal_sharpe():
    rng = np.random.default_rng(7)
    n_obs = 3000
    common = rng.standard_normal(n_obs)
    r1 = pd.Series(0.01 + 0.05 * (0.8 * common + 0.6 * rng.standard_normal(n_obs)))
    r2 = pd.Series(0.01 + 0.05 * (0.8 * common + 0.6 * rng.standard_normal(n_obs)))
    out = sharpe_difference_test(returns1=r1, returns2=r2, af=12.0)
    assert out.p_value > 0.05
    assert abs(out.diff_an) < 0.25


def test_detects_a_true_difference():
    rng = np.random.default_rng(11)
    n_obs = 3000
    r1 = pd.Series(0.02 + 0.05 * rng.standard_normal(n_obs))
    r2 = pd.Series(0.00 + 0.05 * rng.standard_normal(n_obs))
    out = sharpe_difference_test(returns1=r1, returns2=r2, af=12.0)
    assert out.p_value < 0.01
    assert out.diff_an > 0.0


def test_raises_on_short_or_degenerate_inputs():
    r1 = pd.Series(np.linspace(0.0, 0.01, 10))
    with pytest.raises(ValueError):
        sharpe_difference_test(returns1=r1, returns2=r1)
    r_const = pd.Series(np.full(100, 0.01))
    r_ok = pd.Series(np.random.default_rng(3).standard_normal(100))
    with pytest.raises(ValueError):
        sharpe_difference_test(returns1=r_const, returns2=r_ok)


def test_delegates_to_qis_and_preserves_namedtuple(monkeypatch):
    import qis
    from types import SimpleNamespace
    from trendfollowing.analytics.sharpe_test import SharpeDiffTest

    expected = SharpeDiffTest(0.8, 0.6, 0.2, 0.1, 2.0, 0.0455, 100, 3)
    r1, r2 = pd.Series([1.0]), pd.Series([2.0])

    def qis_test(**kwargs):
        assert kwargs['returns1'] is r1
        assert kwargs['returns2'] is r2
        assert kwargs['n_lags'] == 3
        assert kwargs['af'] == 260
        return SimpleNamespace(**expected._asdict())

    monkeypatch.setattr(qis, 'sharpe_difference_test', qis_test, raising=False)
    out = sharpe_difference_test(r1, r2, n_lags=3, af=260)
    assert isinstance(out, SharpeDiffTest)
    assert out == expected


def test_older_qis_compatibility(monkeypatch):
    import qis

    rng = np.random.default_rng(11)
    r1 = pd.Series(0.02 + 0.05 * rng.standard_normal(3000))
    r2 = pd.Series(0.05 * rng.standard_normal(3000))
    current_test = getattr(qis, 'sharpe_difference_test', None)
    reference = current_test(r1, r2, n_lags=None) if current_test is not None else None
    monkeypatch.delattr(qis, 'sharpe_difference_test', raising=False)
    legacy = sharpe_difference_test(r1, r2)
    assert legacy.p_value < 0.01
    assert legacy.diff_an > 0
    if reference is not None:
        np.testing.assert_allclose(legacy[:5], [getattr(reference, name)
                                               for name in legacy._fields[:5]], rtol=1e-12)
        assert legacy.p_value == pytest.approx(reference.p_value, abs=1e-15)
