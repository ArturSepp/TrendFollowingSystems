"""
verification of the arfima(1,d,0) variance scale used by sr_underlying_analytic:
(a) the sowell closed form V_{phi,d} = gamma0_tilde * F(1, 1+d; 1-d; phi) / (1+phi)
    matches the direct acf double sum of Var(x_t), x_t = phi x_{t-1} + rtilde_t
(b) the previous expression c0*(2F(1,d,1-d;phi)-1)/((1-phi)*F(1,1+d,1-d;phi)) reduces
    identically to c0 by the identity 2F(1,d,1-d;x)-1 = (1-x)F(1,1+d,1-d;x),
    so it silently ignored phi (analytic table row 8 erratum: 0.783 -> 0.784 gross,
    0.776 -> 0.777 net)
"""
# packages
import numpy as np
from scipy.special import gamma as sp_gamma, gammaln, hyp2f1
# project
import sys
sys.path.insert(0, '../../..')
from papers.tf_systems.replication.mc_sharpe import sr_underlying_analytic


def var_direct_sum(phi: float, d: float, n_lags: int = 200_000) -> float:
    """direct double sum Var(x) = gamma0_tilde * (1 + 2 sum_m phi^m rho_m) / (1 - phi^2)"""
    gamma0 = sp_gamma(1.0 - 2.0 * d) / np.square(sp_gamma(1.0 - d))
    m = np.arange(1, n_lags)
    rho = np.exp(gammaln(1.0 - d) - gammaln(d) + gammaln(m + d) - gammaln(m + 1.0 - d))
    return gamma0 * (1.0 + 2.0 * np.sum(np.power(phi, m) * rho)) / (1.0 - phi ** 2)


def variance_scale_check() -> None:
    for phi, d in [(-0.05, 0.1), (0.05, 0.1), (-0.05, 0.02), (0.3, 0.1)]:
        v_true = var_direct_sum(phi=phi, d=d)
        v_sowell = (sp_gamma(1.0 - 2.0 * d) / np.square(sp_gamma(1.0 - d))
                    * hyp2f1(1.0, 1.0 + d, 1.0 - d, phi) / (1.0 + phi))
        sr = sr_underlying_analytic(mu_an=1.0, phi=phi, d=d)
        print(f"phi={phi:+.2f}, d={d}: direct {v_true:.9f}, sowell {v_sowell:.9f}, "
              f"sr_underlying {sr:.9f}")
        assert abs(v_sowell - v_true) < 1e-9
        assert abs(sr - 1.0 / np.sqrt(v_true)) < 1e-9


def identity_check() -> None:
    """the identity that collapsed the previous expression to the phi=0 value"""
    d = 0.1
    for phi in [-0.3, -0.05, 0.05, 0.3]:
        lhs = 2.0 * hyp2f1(1.0, d, 1.0 - d, phi) - 1.0
        rhs = (1.0 - phi) * hyp2f1(1.0, 1.0 + d, 1.0 - d, phi)
        assert abs(lhs - rhs) < 1e-12, (phi, lhs, rhs)
    print("identity 2F(1,d,1-d;x)-1 = (1-x)F(1,1+d,1-d;x) confirmed")


if __name__ == '__main__':
    identity_check()
    variance_scale_check()
    print("all checks passed")
