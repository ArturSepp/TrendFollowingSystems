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
