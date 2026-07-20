"""
kappa=3 analytic column for the student-t comparison table tab:t6
gate: replicate every printed kappa=0 analytic value with the paper's own code path before computing the new column
kurtosis loading per row: K_sig = sum_{s>=1} psi_s^2 b_{s-1}^2 with b_u the signal loading on innovation eps_{t-1-u}
"""
# packages
import sys
import numpy as np
from scipy.signal import lfilter
from scipy.special import gamma as sp_gamma
from typing import Optional, Tuple, List, Dict
# project
# run from the repository root with the package installed
from trendfollowing.analytics.sharpe import compute_annualised_sharpe, compute_daily_moments
from trendfollowing.analytics.filters import span_to_nu, compute_ewm_long_short_weights
from trendfollowing.analytics.autocorrelation import population_acf
from papers.tf_systems.replication.mc_sharpe import sr_underlying_analytic

AF = 260.0
N_LAGS_ACF = 2000  # matches the paper's psi_nu truncation
N_MA = 8000  # ma-weight truncation for the kurtosis loading
KAPPA_T6 = 3.0  # excess kurtosis of standardised t(6) innovations

# printed values of tab:t6, (analytic_21, analytic_250, analytic_ls) per process row
TABLE_ROWS: List[Dict] = [
    dict(name='White noise, mu=0.25', mu_an=0.25, phi=0.0, d=0.0, printed=(0.018, 0.060, 0.062)),
    dict(name='White noise, mu=0.50', mu_an=0.50, phi=0.0, d=0.0, printed=(0.070, 0.220, 0.227)),
    dict(name='AR-1, phi=+0.05', mu_an=0.0, phi=0.05, d=0.0, printed=(0.336, 0.102, 0.001)),
    dict(name='AR-1, phi=-0.05', mu_an=0.0, phi=-0.05, d=0.0, printed=(-0.336, -0.102, 0.000)),
    dict(name='ARFIMA, d=0.1', mu_an=0.0, phi=0.0, d=0.1, printed=(1.876, 1.061, 0.696)),
    dict(name='ARFIMA, d=0.1, phi=-0.05', mu_an=0.0, phi=-0.05, d=0.1, printed=(1.562, 0.960, 0.666)),
    dict(name='ARFIMA, d=0.1, mu=0.50', mu_an=0.50, phi=0.0, d=0.1, printed=(1.916, 1.157, 0.809)),
    dict(name='ARFIMA, d=0.1, phi=-0.05, mu=0.50', mu_an=0.50, phi=-0.05, d=0.1, printed=(1.607, 1.062, 0.783)),
]


def ma_weights(phi: float, d: float, n_ma: int = N_MA) -> np.ndarray:
    """normalised moving-average weights of the arfima(1,d,0) process, sum psi^2 = 1
    fractional weights pi_j = Gamma(j+d)/(Gamma(j+1)Gamma(d)) by recursion, ar part via 1/(1-phi L)"""
    pi = np.ones(n_ma)
    for j in range(1, n_ma):
        pi[j] = pi[j - 1] * (j - 1.0 + d) / j
    psi = lfilter([1.0], [1.0, -phi], pi)
    return psi / np.sqrt(np.sum(psi ** 2))


def signal_innovation_loadings(psi: np.ndarray,
                               long_span: float,
                               short_span: Optional[float] = None,
                               ) -> np.ndarray:
    """loadings b_u of the variance-preserving (long-short) signal on the innovation eps_{t-1-u}"""
    l1, l2 = compute_ewm_long_short_weights(long_span=long_span, short_span=short_span)
    nu1 = span_to_nu(long_span)
    c1 = (1.0 - nu1) * lfilter([1.0], [1.0, -nu1], psi)
    if short_span is None:
        return l1 * c1
    nu2 = span_to_nu(short_span)
    c2 = (1.0 - nu2) * lfilter([1.0], [1.0, -nu2], psi)
    return l1 * c1 - l2 * c2


def kurtosis_loading(psi: np.ndarray,
                     long_span: float,
                     short_span: Optional[float] = None,
                     ) -> float:
    """K_sig = sum_{s>=1} psi_s^2 b_{s-1}^2 with the signal loadings b of eq sr_k, loadings included"""
    b = signal_innovation_loadings(psi=psi, long_span=long_span, short_span=short_span)
    return float(np.sum(psi[1:] ** 2 * b[:-1] ** 2))


def sr_kappa(mu_an: float, phi: float, d: float,
             long_span: float, short_span: Optional[float],
             kappa: float,
             ) -> Tuple[float, float]:
    """(sr at kappa=0 via the paper's code path, sr at the given kappa via the extended denominator)"""
    rho = population_acf(n_lags=N_LAGS_ACF, phi=phi, d=d)
    sr_z = sr_underlying_analytic(mu_an=mu_an, phi=phi, d=d)
    sr0 = compute_annualised_sharpe(rho=rho, long_span=long_span, short_span=short_span,
                                    sr_underlying=sr_z, af=AF)
    mean_f, var_f = compute_daily_moments(rho=rho, long_span=long_span, short_span=short_span,
                                          mean=sr_z / np.sqrt(AF), variance=1.0)
    k_sig = kurtosis_loading(psi=ma_weights(phi=phi, d=d), long_span=long_span, short_span=short_span)
    sr_k = float(np.sqrt(AF) * mean_f / np.sqrt(var_f + kappa * k_sig))
    return sr0, sr_k


def run_checks_and_table() -> None:
    # check 1: ma weights reproduce the population acf for every process
    for phi, d in [(0.05, 0.0), (-0.05, 0.0), (0.0, 0.1), (-0.05, 0.1)]:
        psi = ma_weights(phi=phi, d=d)
        acf_psi = np.array([np.sum(psi[:-m] * psi[m:]) for m in range(1, 51)])
        acf_pop = population_acf(n_lags=51, phi=phi, d=d)[1:51]
        err = np.max(np.abs(acf_psi - acf_pop))
        assert err < 2e-4, f"acf mismatch phi={phi}, d={d}: {err:.2e}"
        print(f"acf check phi={phi:+.2f} d={d:.1f}: max |dACF| lags 1-50 = {err:.1e}")
    # check 2: arfima variance identity
    pi = np.ones(N_MA)
    for j in range(1, N_MA):
        pi[j] = pi[j - 1] * (j - 1.0 + 0.1) / j
    gamma0 = float(np.sum(pi ** 2))
    gamma0_cf = sp_gamma(1.0 - 0.2) / sp_gamma(1.0 - 0.1) ** 2
    print(f"arfima gamma0: sum pi^2 = {gamma0:.5f}, closed form = {gamma0_cf:.5f}")
    # check 3: single-filter ar-1 loading equals l1^2 times the closed form of eq sr_ar1_k
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location('evc', './ewma_variance_check.py')
    # closed form inline to avoid importing the mc module
    def k_ar1_closed(nu: float, phi: float) -> float:
        br = (phi ** 4 / (1 - phi ** 4) - 2 * nu * phi ** 3 / (1 - nu * phi ** 3)
              + nu ** 2 * phi ** 2 / (1 - nu ** 2 * phi ** 2))
        return (1 - nu) ** 2 * (1 - phi ** 2) ** 2 / (phi - nu) ** 2 * br
    for span in [21.0, 250.0]:
        nu = span_to_nu(span)
        l1, _ = compute_ewm_long_short_weights(long_span=span, short_span=None)
        k_num = kurtosis_loading(psi=ma_weights(phi=0.05, d=0.0), long_span=span)
        k_cf = l1 ** 2 * k_ar1_closed(nu=nu, phi=0.05)
        assert abs(k_num - k_cf) < 1e-8, f"ar1 loading mismatch span {span}"
        print(f"ar-1 K_sig span {span:.0f}: numeric = {k_num:.3e}, l1^2 x closed form = {k_cf:.3e}")
    # gate + new column
    print(f"\n{'process':36s} {'a21':>7s} {'k21':>7s} {'a250':>7s} {'k250':>7s} {'aLS':>7s} {'kLS':>7s}")
    latex_cells = []
    max_corr = 0.0
    for row in TABLE_ROWS:
        vals = {}
        for key, (ls, ss) in dict(s21=(21.0, None), s250=(250.0, None), ls=(250.0, 20.0)).items():
            sr0, sr_k = sr_kappa(mu_an=row['mu_an'], phi=row['phi'], d=row['d'],
                                 long_span=ls, short_span=ss, kappa=KAPPA_T6)
            vals[key] = (sr0, sr_k)
        printed = row['printed']
        for got, want, tag in zip((vals['s21'][0], vals['s250'][0], vals['ls'][0]), printed, ('21', '250', 'LS')):
            assert abs(round(got, 3) - want) < 1e-9, f"{row['name']} span {tag}: got {got:.3f}, printed {want:.3f}"
        max_corr = max(max_corr, *(abs(v[0] - v[1]) for v in vals.values()))
        print(f"{row['name']:36s} {vals['s21'][0]:7.3f} {vals['s21'][1]:7.3f} "
              f"{vals['s250'][0]:7.3f} {vals['s250'][1]:7.3f} {vals['ls'][0]:7.3f} {vals['ls'][1]:7.3f}")
        latex_cells.append(dict(name=row['name'],
                                k21=f"{vals['s21'][1]:.3f}", k250=f"{vals['s250'][1]:.3f}", kls=f"{vals['ls'][1]:.3f}"))
    print(f"\ngate passed: all 24 printed kappa=0 values replicated to 3 decimals")
    print(f"max |kappa=3 correction| across all cells: {max_corr:.4f}")
    np.save('./t6_kappa_cells.npy', latex_cells, allow_pickle=True)


if __name__ == '__main__':
    run_checks_and_table()
