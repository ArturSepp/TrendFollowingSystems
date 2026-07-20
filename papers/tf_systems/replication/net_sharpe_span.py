"""
net sharpe ratio sr_net = sqrt(a)(E[f] - c E[U])/sqrt(V[f]) over spans and cost levels
gross moments from the paper's code path, turnover from eq tur2, sigma_target cancels
gate: var_f = 1 under zero-drift white noise, so the drag normalisation is verified before use
"""
# packages
import sys
import numpy as np
# project
# run from the repository root with the package installed
from trendfollowing.analytics.sharpe import compute_daily_moments
from trendfollowing.analytics.filters import span_to_nu
from trendfollowing.analytics.autocorrelation import population_acf
from papers.tf_systems.replication.mc_sharpe import sr_underlying_analytic

AF = 260.0
SPANS = np.array([2, 3, 5, 10, 15, 21, 42, 63, 125, 250, 520], dtype=float)
COSTS_BP = [0.0, 2.0, 5.0, 10.0, 20.0, 50.0]  # cost per unit of volatility-normalised turnover
PROCS = [
    ('WN mu=0.50', dict(mu_an=0.50, phi=0.0, d=0.0)),
    ('AR-1 phi=+0.05', dict(mu_an=0.0, phi=0.05, d=0.0)),
    ('ARFIMA d=0.1', dict(mu_an=0.0, phi=0.0, d=0.1)),
    ('ARFIMA d=0.1 phi=-0.05', dict(mu_an=0.0, phi=-0.05, d=0.1)),
]


def moments(mu_an: float, phi: float, d: float, span: float):
    rho = population_acf(n_lags=2000, phi=phi, d=d)
    sr_z = sr_underlying_analytic(mu_an=mu_an, phi=phi, d=d)
    return compute_daily_moments(rho=rho, long_span=span, short_span=None,
                                 mean=sr_z / np.sqrt(AF), variance=1.0)


def sr_net(mu_an: float, phi: float, d: float, span: float, c: float):
    mean_f, var_f = moments(mu_an, phi, d, span)
    nu = span_to_nu(span)
    drag = 2.0 * AF * c / np.sqrt(np.pi) * np.sqrt(1.0 - nu)
    return float((np.sqrt(AF) * mean_f - drag) / np.sqrt(var_f)), float(np.sqrt(AF) * mean_f / np.sqrt(var_f))


# gate: zero-drift white noise has var_f = 1 at every span (drag normalisation)
for s in SPANS:
    _, v = moments(0.0, 0.0, 0.0, s)
    assert abs(v - 1.0) < 1e-9, (s, v)
print("gate passed: var_f = 1 under zero-drift white noise at all spans\n")

for name, cfg in PROCS:
    print(f"=== {name} ===")
    header = 'span     gross ' + ''.join(f"  c={int(b):>2d}bp" for b in COSTS_BP[1:])
    print(header)
    table = {}
    for s in SPANS:
        row = []
        for bp in COSTS_BP:
            net, gross = sr_net(**cfg, span=s, c=bp / 1e4)
            row.append(net)
        table[s] = row
        print(f"{int(s):>4d}  {row[0]:>8.3f}" + ''.join(f"  {x:>7.3f}" for x in row[1:]))
    for j, bp in enumerate(COSTS_BP):
        vals = {s: table[s][j] for s in SPANS}
        s_star = max(vals, key=vals.get)
        tag = 'no trade' if vals[s_star] <= 0 else f"span*={int(s_star)}, net={vals[s_star]:.3f}"
        print(f"  optimum at c={int(bp):>2d}bp: {tag}")
    # break-even cost per span: c*(span) with sr_net = 0
    cbe = {}
    for s in SPANS:
        mean_f, var_f = moments(**cfg, span=s)
        nu = span_to_nu(s)
        cbe[s] = float(np.sqrt(AF) * mean_f * np.sqrt(np.pi) / (2.0 * AF * np.sqrt(1.0 - nu)))
    print('  break-even c* (bp): ' + '  '.join(f"{int(s)}:{1e4 * cbe[s]:.1f}" for s in SPANS) + '\n')
