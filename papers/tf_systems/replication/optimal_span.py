"""
validate the optimal-span asymptotics for the net sharpe ratio
exact sr_net on fine span grids via the paper's moments, compared with the derived closed forms
"""
# packages
import sys
import numpy as np
# project
# run from the repository root with the package installed
from trendfollowing.analytics.sharpe import compute_daily_moments
from trendfollowing.analytics.filters import span_to_nu
from trendfollowing.analytics.autocorrelation import population_acf

AF = 260.0


def rho_arfima(d: float, n_lags: int) -> np.ndarray:
    """acf of arfima(0,d,0) by the exact gamma-ratio recursion, rho(m) = rho(m-1)*(m-1+d)/(m-d)"""
    rho = np.ones(n_lags)
    for m in range(1, n_lags):
        rho[m] = rho[m - 1] * (m - 1.0 + d) / (m - d)
    return rho


def sr_net_exact(rho: np.ndarray, span: float, c: float) -> tuple:
    mean_f, var_f = compute_daily_moments(rho=rho, long_span=span, short_span=None, mean=0.0, variance=1.0)
    nu = span_to_nu(span)
    gross = np.sqrt(AF) * mean_f / np.sqrt(var_f)
    drag = 2.0 * AF * c / np.sqrt(np.pi) * np.sqrt(1.0 - nu) / np.sqrt(var_f)
    return gross - drag, gross, drag


def argmax_span(rho: np.ndarray, c: float, s_lo: float = 2.0, s_hi: float = 20000.0, n: int = 500) -> tuple:
    spans = np.geomspace(s_lo, s_hi, n)
    vals = np.array([sr_net_exact(rho, s, c)[0] for s in spans])
    i = int(np.argmax(vals))
    return spans[i], vals[i], i in (0, n - 1)


# ============ ar-1: span* ~ (4 phi/(1-phi) + x)/(1-x), x = c/c*_inf ============
phi = 0.05
c_star = np.sqrt(np.pi / (2.0 * AF)) * phi / (1.0 - phi)
rho_ar = population_acf(n_lags=2000, phi=phi, d=0.0)
print(f"AR-1 phi={phi}: c*_inf = {1e4*c_star:.1f}bp")
print(f"{'x=c/c*':>7s} {'span* exact':>12s} {'span* formula':>14s} {'net at opt':>11s} {'corner?':>8s}")
for x in [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98]:
    c = x * c_star
    s_star, v_star, corner = argmax_span(rho_ar, c)
    s_pred = (4.0 * phi / (1.0 - phi) + x) / (1.0 - x)
    print(f"{x:7.2f} {s_star:12.1f} {s_pred:14.1f} {v_star:11.4f} {str(corner):>8s}")

# ============ arfima: span* ~ c^(1/2d) and the 4d/(1+2d) invariant ============
for d in [0.1, 0.2, 0.3]:
    n_lags = 400000
    rho = rho_arfima(d=d, n_lags=n_lags)
    cs = np.geomspace(2e-4, 30e-4, 7)
    rows = []
    for c in cs:
        s_star, v_star, corner = argmax_span(rho, c, s_lo=2.0, s_hi=15000.0, n=400)
        net, gross, drag = sr_net_exact(rho, s_star, c)
        rows.append((c, s_star, net / gross, drag / gross, corner))
    lc = np.log([r[0] for r in rows]); ls = np.log([r[1] for r in rows])
    slope = np.polyfit(lc, ls, 1)[0]
    print(f"\nARFIMA d={d}: elasticity of span* to c: fitted {slope:.2f} vs 1/(2d) = {1/(2*d):.2f}")
    print(f"  invariant SR_net/SR at optimum: predicted 4d/(1+2d) = {4*d/(1+2*d):.3f}")
    print(f"  {'c (bp)':>7s} {'span*':>8s} {'net/gross':>10s} {'drag/gross':>11s}  target drag/gross = {(1-2*d)/(1+2*d):.3f}")
    for c, s, ng, dg, corner in rows:
        flag = ' corner' if corner else ''
        print(f"  {1e4*c:7.1f} {s:8.1f} {ng:10.3f} {dg:11.3f}{flag}")

# ============ white noise with drift: monotone, limit mu_an ============
mu_an = 0.5
rho_wn = population_acf(n_lags=2000, phi=0.0, d=0.0)


def sr_net_wn(span: float, c: float) -> float:
    mean_f, var_f = compute_daily_moments(rho=rho_wn, long_span=span, short_span=None,
                                          mean=mu_an / np.sqrt(AF), variance=1.0)
    nu = span_to_nu(span)
    return float((np.sqrt(AF) * mean_f - 2.0 * AF * c / np.sqrt(np.pi) * np.sqrt(1.0 - nu)) / np.sqrt(var_f))


spans = np.geomspace(2, 2e5, 200)
vals = np.array([sr_net_wn(s, 0.0020) for s in spans])
assert np.all(np.diff(vals) > 0), "wn net sharpe not monotone"
print(f"\nWN mu_an={mu_an}, c=20bp: monotone increasing; net at span 2e5 = {vals[-1]:.4f} -> limit mu_an = {mu_an}")
