"""
verify the four new proof-level claims before writing the appendix
v1: ar-1 break-even closed form c*(eps) is exact at every span
v2: (1-x) span*(x) -> 6 phi/(1-phi) + 3/2 as x -> 1
v3: exact hypergeometric decomposition Phi = Cpsi eps^(-2d) (1-eps)^d + Cg 2F1(d,1;1+2d;eps)
v4: arfima scaling constant K_d and the drag-share invariant (1-2d)/(1+2d)
"""
# packages
import sys
import numpy as np
from scipy.special import hyp2f1, gamma
from scipy.optimize import brentq
# project
# run from the repository root with the package installed
from trendfollowing.analytics.sharpe import compute_daily_moments
from trendfollowing.analytics.filters import span_to_nu
from trendfollowing.analytics.autocorrelation import population_acf

AF = 260.0


def rho_arfima(d, n):
    r = np.ones(n)
    for m in range(1, n):
        r[m] = r[m - 1] * (m - 1.0 + d) / (m - d)
    return r


def srn(rho, s, c):
    mf, vf = compute_daily_moments(rho=rho, long_span=s, short_span=None, mean=0.0, variance=1.0)
    nu = span_to_nu(s)
    g = np.sqrt(AF) * mf / np.sqrt(vf)
    dr = 2.0 * AF * c / np.sqrt(np.pi) * np.sqrt(1.0 - nu) / np.sqrt(vf)
    return g - dr, g, dr


# ============ v1: exact break-even closed form ============
phi = 0.05
rho_ar = population_acf(n_lags=2000, phi=phi, d=0.0)
print("V1: c*(eps) = sqrt(pi/(2a)) * phi * sqrt(1-eps/2) / (1-phi+eps*phi)")
for span in [2.0, 5.0, 21.0, 63.0, 250.0]:
    eps = 1.0 - span_to_nu(span)
    c_formula = np.sqrt(np.pi / (2.0 * AF)) * phi * np.sqrt(1.0 - eps / 2.0) / (1.0 - phi + eps * phi)
    c_numeric = brentq(lambda c: srn(rho_ar, span, c)[0], 1e-6, 1e-2, xtol=1e-14)
    assert abs(c_formula - c_numeric) < 1e-10, (span, c_formula, c_numeric)
    print(f"  span {span:>5.0f}: formula {1e4*c_formula:.3f}bp = numeric {1e4*c_numeric:.3f}bp")

# ============ v2: the (1-x) span limit ============
c_star = np.sqrt(np.pi / (2.0 * AF)) * phi / (1.0 - phi)
target = 6.0 * phi / (1.0 - phi) + 1.5
print(f"\nV2: (1-x) span*(x) -> 6 phi/(1-phi) + 3/2 = {target:.4f}")
for x in [0.98, 0.99, 0.995]:
    spans = np.geomspace(2, 200000, 1200)
    vals = np.array([srn(rho_ar, s, x * c_star)[0] for s in spans])
    s_star = spans[int(np.argmax(vals))]
    print(f"  x={x}: (1-x) span* = {(1.0 - x) * s_star:.4f}")

# ============ v3: exact hypergeometric decomposition ============
print("\nV3: Phi = Cpsi eps^(-2d)(1-eps)^d + Cg 2F1(d,1;1+2d;eps), machine-exact")
for d in [0.1, 0.3]:
    Cpsi = gamma(1.0 - d) * gamma(2.0 * d) / gamma(d)
    Cg = gamma(1.0 - d) * gamma(-2.0 * d) / (gamma(1.0 - 2.0 * d) * gamma(-d))
    for span in [21.0, 250.0]:
        nu = span_to_nu(span)
        eps = 1.0 - nu
        lhs = float(hyp2f1(d, 1.0, 1.0 - d, nu))
        rhs = float(Cpsi * eps ** (-2.0 * d) * (1.0 - eps) ** d + Cg * hyp2f1(d, 1.0, 1.0 + 2.0 * d, eps))
        assert abs(lhs - rhs) < 1e-9 * abs(lhs), (d, span, lhs, rhs)
        print(f"  d={d}, span {span:>4.0f}: {lhs:.8f} = {rhs:.8f}")

# ============ v4: arfima scaling constant and invariant ============
d = 0.3
Cpsi = gamma(1.0 - d) * gamma(2.0 * d) / gamma(d)
K = (np.sqrt(2.0 * AF / np.pi) * (1.0 + 2.0 * d) / (Cpsi * (1.0 - 2.0 * d))) ** (1.0 / (2.0 * d))
rho = rho_arfima(d, 600000)
print(f"\nV4: d={d}, span* / (2 K c^(1/2d)) -> 1 and drag/gross -> {(1-2*d)/(1+2*d):.3f}")
for cbp in [400.0, 1600.0, 6400.0]:
    c = cbp / 1e4
    pred = 2.0 * K * c ** (1.0 / (2.0 * d))
    spans = np.geomspace(2, 25000, 500)
    vals = np.array([srn(rho, s, c)[0] for s in spans])
    i = int(np.argmax(vals))
    s_star = spans[i]
    _, g, dr = srn(rho, s_star, c)
    print(f"  c={cbp:>6.0f}bp: span* {s_star:8.0f}, prediction {pred:8.0f}, ratio {s_star/pred:.3f}, drag/gross {dr/g:.3f}")
