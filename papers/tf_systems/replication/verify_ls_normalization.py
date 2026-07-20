"""
unit test for the long-short filter normalization and turnover (proposition 2 and proposition 4.6)
monte carlo checks that would have caught the q-exponent inversion and the zeta formula error:
(a) the variance-preserving LS(250,20) signal has unit variance under iid gaussian innovations
(b) the annualized signal-level turnover matches the closed form (2a/sqrt(pi))*sigma*sqrt(zeta)
run from this directory with the trendfollowing package installed
"""
# packages
import numpy as np
# project
import sys
sys.path.insert(0, '../../..')
from trendfollowing.analytics.expected_return import expected_turnover

A, SIGMA_TARGET = 260.0, 0.15
LONG_SPAN, SHORT_SPAN = 250, 20
N_OBS, SEED = 4_000_000, 7


def simulate_ls_signal(long_span: int, short_span: int, n_obs: int, seed: int) -> np.ndarray:
    """variance-preserving long-short signal S = q * (raw_long - raw_short) on iid gaussian z"""
    rng = np.random.default_rng(seed)
    nu1, nu2 = 1.0 - 2.0/(long_span + 1.0), 1.0 - 2.0/(short_span + 1.0)
    d_norm = 1.0/(1.0 - nu1**2) + 1.0/(1.0 - nu2**2) - 2.0/(1.0 - nu1*nu2)
    q = d_norm ** -0.5
    z = rng.standard_normal(n_obs)
    ewma1, ewma2 = np.empty(n_obs), np.empty(n_obs)
    ewma1[0] = ewma2[0] = z[0]
    for t in range(1, n_obs):
        ewma1[t] = (1.0 - nu1)*z[t] + nu1*ewma1[t-1]
        ewma2[t] = (1.0 - nu2)*z[t] + nu2*ewma2[t-1]
    return q * (ewma1/(1.0 - nu1) - ewma2/(1.0 - nu2))


if __name__ == '__main__':
    signal = simulate_ls_signal(LONG_SPAN, SHORT_SPAN, N_OBS, SEED)[5000:]
    var_signal = float(signal.var())
    print(f"(a) LS({LONG_SPAN},{SHORT_SPAN}) signal variance: {var_signal:.4f} (target 1.0)")
    assert abs(var_signal - 1.0) < 0.01, "variance preservation failed: check the q exponent"

    turnover_mc = A * SIGMA_TARGET * float(np.mean(np.abs(np.diff(signal))))
    turnover_an = expected_turnover(long_span=LONG_SPAN, short_span=SHORT_SPAN,
                                    annualization_factor=A, vol_target=SIGMA_TARGET)
    print(f"(b) signal turnover: MC {turnover_mc:.1%} vs closed form {turnover_an:.1%}")
    assert abs(turnover_mc - turnover_an) < 0.01, "turnover closed form does not match the monte carlo"
    print("all checks passed: the normalization and the turnover formula are consistent")
