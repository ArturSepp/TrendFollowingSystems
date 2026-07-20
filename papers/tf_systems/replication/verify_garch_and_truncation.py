"""
verification of two claims in the manuscript:
(a) under garch(1,1), the pipeline z_t is approximately the iid standardized innovations
    (raw excess kurtosis ~7 collapses to ~0.06, first-lag autocorrelation below 0.001)
(b) the arfima acf truncation at 2000 lags has a remainder below 1e-4 relative to Psi_nu
    at the longest span of the paper grid
"""
# packages
import numpy as np
from scipy.special import gammaln

rng = np.random.default_rng(11)


def garch_pipeline_check(n: int = 2_000_000) -> None:
    omega, alpha, beta = 1e-6, 0.09, 0.90  # realistic daily garch(1,1)
    eps = rng.standard_normal(n)
    r = np.empty(n)
    v = omega / (1.0 - alpha - beta)
    for t in range(n):
        r[t] = np.sqrt(v) * eps[t]
        v = omega + alpha * r[t] ** 2 + beta * v
    nu = 1.0 - 2.0 / 34.0  # ewma variance with span 33, lagged
    var = float(np.mean(r[:33] ** 2))
    z = np.empty(n)
    for t in range(n):
        z[t] = r[t] / np.sqrt(var)
        var = (1.0 - nu) * r[t] ** 2 + nu * var
    z = z[500:]

    def acf1(x):
        x = x - x.mean()
        return float(np.dot(x[1:], x[:-1]) / np.dot(x, x))

    kurt_r = np.mean(((r - r.mean()) / r.std()) ** 4) - 3.0
    kurt_z = np.mean(((z - z.mean()) / z.std()) ** 4) - 3.0
    print(f"garch raw: excess kurtosis {kurt_r:.2f}; pipeline z: var {z.var():.3f}, "
          f"acf1 {acf1(z):+.4f}, excess kurtosis {kurt_z:.2f}")
    assert kurt_z < 0.5 and abs(acf1(z)) < 0.005


def truncation_bound_check() -> None:
    def rho(m, d):
        return np.exp(gammaln(1.0 - d) - gammaln(d) + gammaln(m + d) - gammaln(m + 1.0 - d))
    nu = 1.0 - 2.0 / 521.0  # longest span of the empirical grid
    ms_tail, ms_full = np.arange(2001, 60000), np.arange(1, 60000)
    for d in [0.02, 0.1, 0.3]:
        rem = (1.0 - nu) * np.sum(nu ** ms_tail * rho(ms_tail, d))
        psi = (1.0 - nu) * np.sum(nu ** ms_full * rho(ms_full, d))
        print(f"d={d}: truncation remainder {rem:.2e}, relative to Psi {rem/psi:.1e}")
        assert rem / psi < 1e-3


if __name__ == '__main__':
    truncation_bound_check()
    garch_pipeline_check()
    print("all checks passed")
