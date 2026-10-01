"""
regression tests for the optional portfolio volatility targeting of the system runners:
days with zero portfolio variance must get zero leverage, never the uninitialised values
np.reciprocal leaves in cells masked by where= when no out= array is passed
"""

# packages
import numpy as np
import pandas as pd
import pytest

# project
from trendfollowing.systems.american import run_american_system
from trendfollowing.systems.european import run_european_tf_system
from trendfollowing.systems.tsmom import run_tsmom_system

NUM_DAYS = 600
FLAT_START, FLAT_END = 450, 480  # prices are held constant over [FLAT_START, FLAT_END)

# span = 1 gives ewm_lambda = 1 - 2 / (span + 1) = 0, so the ewm covariance on day t is the
# outer product of that day's returns and the portfolio variance is exactly zero on every day
# with zero returns, while the positions opened before the flat stretch stay on
PORTFOLIO_COVAR_SPAN = 1

RUNNERS = {
    'american': run_american_system,
    'european': run_european_tf_system,
    'tsmom': run_tsmom_system,
}


def _flat_stretch_prices() -> pd.DataFrame:
    """trending random-walk prices for two instruments with a common constant stretch"""
    rng = np.random.default_rng(7)
    log_returns = 0.002 + 0.01 * rng.standard_normal((NUM_DAYS, 2))
    log_returns[0] = 0.0
    log_returns[FLAT_START:FLAT_END] = 0.0
    prices = 100.0 * np.exp(np.cumsum(log_returns, axis=0))
    # hold the stretch at the bitwise-identical price so every return there is exactly zero
    prices[FLAT_START:FLAT_END] = prices[FLAT_START - 1]
    index = pd.bdate_range('2000-01-03', periods=NUM_DAYS)
    return pd.DataFrame(prices, index=index, columns=['A', 'B'])


# uninitialised memory can happen to read as zero, so also fail on the warning recent numpy
# raises for where= without out=, which flags the defect independently of the memory contents
@pytest.mark.filterwarnings("error:'where' used without 'out':UserWarning")
@pytest.mark.parametrize('name', list(RUNNERS))
def test_zero_portfolio_variance_gives_zero_weights(name: str):
    prices = _flat_stretch_prices()
    flat_days = prices.index[FLAT_START:FLAT_END]
    run_system = RUNNERS[name]

    # without portfolio targeting the positions are open over the flat stretch, so a zero
    # weight there can only come from zero leverage
    raw_weights = run_system(prices=prices, portfolio_covar_span=None).weights.loc[flat_days]
    assert np.all(np.isfinite(raw_weights.to_numpy()))
    assert np.all(raw_weights.to_numpy() != 0.0)

    weights = run_system(prices=prices, portfolio_covar_span=PORTFOLIO_COVAR_SPAN).weights
    np.testing.assert_array_equal(weights.loc[flat_days].to_numpy(), 0.0)
    # the targeting is otherwise active: weights after the warmup and outside the stretch stay
    # finite and are not all zero
    after_flat = weights.iloc[FLAT_END + 1:].to_numpy()
    assert np.all(np.isfinite(after_flat))
    assert np.any(after_flat != 0.0)
