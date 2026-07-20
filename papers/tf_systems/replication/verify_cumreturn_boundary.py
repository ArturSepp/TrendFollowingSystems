"""
numerical verification of the boundary term R_T in the sample-path identity (proposition pr:cumreturn)
confirms: with a fully pre-sample-warmed filter, lhs - rhs(centered decomposition) equals
R_T = zbar*(1-nu)*sum_{m>=1} nu^m Delta_m to machine precision, with Delta_m the window-shift
difference, and the relative residual scales as O(span/T)
"""
# packages
import numpy as np

rng = np.random.default_rng(3)


def test(span: int, T: int, mu: float, n_pre: int = 8000):
    nu = 1.0 - 2.0 / (span + 1.0)
    z = mu + rng.standard_normal(n_pre + T)
    zs = z[n_pre:]
    zbar = zs.mean()
    ewma = np.empty(n_pre + T)
    ewma[0] = z[0]
    for t in range(1, n_pre + T):
        ewma[t] = (1.0 - nu) * z[t] + nu * ewma[t - 1]
    lhs = float(np.sum(nu * zs * ewma[n_pre - 1:n_pre + T - 1]))
    n_lags = 12 * span
    rhs = 0.0
    for m in range(n_lags):
        prods = (zs - zbar) * (z[n_pre - m:n_pre + T - m] - zbar)
        rhs += (1.0 - nu) * nu ** m * prods.sum()
    rhs += -(1.0 - nu) * np.sum((zs - zbar) ** 2) + nu * T * zbar ** 2
    resid = lhs - rhs
    r_t = 0.0
    for m in range(1, n_lags):
        delta_m = z[n_pre - m:n_pre + T - m].sum() - T * zbar
        r_t += (1.0 - nu) * nu ** m * delta_m
    r_t *= zbar
    return resid, r_t, abs(lhs)


if __name__ == '__main__':
    print("span=250, drift mu=0.03: residual vs closed-form R_T")
    for T in [5000, 30000, 120000]:
        resid, r_t, scale = test(250, T, mu=0.03)
        assert abs(resid - r_t) < 1e-8, "R_T closed form does not match"
        print(f"  T={T:>6}: resid {resid:+.4f} = R_T {r_t:+.4f}, relative {abs(resid)/scale:.1e}")
    resid, r_t, _ = test(250, 30000, mu=0.0)
    assert abs(resid - r_t) < 1e-8
    print(f"zero drift (finite-sample zbar): resid {resid:+.5f} = R_T {r_t:+.5f}")
    print("all checks passed: the identity with R_T is exact")
