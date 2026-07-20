"""
assemble the redesigned tab:t6 (ls(250,20), gross and net blocks) and every number quoted in the text
gates: analytic gross kappa=0 and kappa=3 must reproduce the printed table, mc gross already gated in the parts
"""
# packages
import sys
import pickle
import numpy as np
# project
# run from the repository root with the package installed
from trendfollowing.analytics.sharpe import compute_annualised_sharpe, compute_daily_moments
from trendfollowing.analytics.autocorrelation import population_acf, ma_weights
from trendfollowing.analytics.expected_return import expected_turnover
from papers.tf_systems.replication.mc_sharpe import sr_underlying_analytic

AF, C, VT = 260.0, 0.0020, 0.15
CONFIGS = [
    ('White noise, $\\mu^{z}_{an}=0.25$', 0.25, 0.0, 0.0), ('White noise, $\\mu^{z}_{an}=0.50$', 0.50, 0.0, 0.0),
    ('AR-1, $\\phi=+0.05$', 0.0, 0.05, 0.0), ('AR-1, $\\phi=-0.05$', 0.0, -0.05, 0.0),
    ('ARFIMA, $d=0.1$', 0.0, 0.0, 0.1), ('ARFIMA, $d=0.1$, $\\phi=-0.05$', 0.0, -0.05, 0.1),
    ('ARFIMA, $d=0.1$, $\\mu^{z}_{an}=0.50$', 0.50, 0.0, 0.1), ('ARFIMA, $d=0.1$, $\\phi=-0.05$, $\\mu^{z}_{an}=0.50$', 0.50, -0.05, 0.1),
]
PRINTED_AN = [0.062, 0.227, 0.001, 0.000, 0.696, 0.666, 0.809, 0.784]  # printed analytic (kappa=0 and kappa=3 identical); last row corrected with the sowell variance scale of sr_underlying_analytic
PRINTED_MC = [('0.065', '0.061'), ('0.234', '0.225'), ('-0.000', '-0.002'), ('0.002', '0.003'),
              ('0.670', '0.664'), ('0.640', '0.635'), ('0.781', '0.776'), ('0.763', '0.757')]

tur_ls = expected_turnover(long_span=250.0, short_span=20.0, annualization_factor=AF, vol_target=VT)
print(f"analytic signal-level turnover LS(250,20): {tur_ls:.1%}")

rows, derived = [], dict(max_gap_gross=0.0, max_gap_net=0.0, max_kdelta=0.0, max_tails_gross=0.0, max_cost=0.0)
for i, (name, mu_an, phi, d) in enumerate(CONFIGS):
    rho = population_acf(n_lags=2000, phi=phi, d=d)
    sr_z = sr_underlying_analytic(mu_an=mu_an, phi=phi, d=d)
    net_an, gross_an = {}, {}
    for kappa in (0.0, 3.0):
        kw = dict(kappa=kappa, ma_weights=ma_weights(phi=phi, d=d)) if kappa else {}
        g = compute_annualised_sharpe(rho=rho, long_span=250.0, short_span=20.0, sr_underlying=sr_z, af=AF, **kw)
        mean_f, var_f = compute_daily_moments(rho=rho, long_span=250.0, short_span=20.0, mean=sr_z / np.sqrt(AF), variance=1.0)
        if kappa:
            from trendfollowing.analytics.sharpe import compute_kurtosis_loading
            var_f = var_f + kappa * compute_kurtosis_loading(ma_weights=ma_weights(phi=phi, d=d), long_span=250.0, short_span=20.0)
        gross_an[kappa] = g
        net_an[kappa] = g - C * tur_ls / (VT * np.sqrt(var_f))
    assert abs(round(gross_an[0.0], 3) - PRINTED_AN[i]) < 1e-9, (name, gross_an[0.0])
    assert abs(round(gross_an[3.0], 3) - PRINTED_AN[i]) < 1e-9, (name, gross_an[3.0])
    derived['max_kdelta'] = max(derived['max_kdelta'], abs(gross_an[0.0] - gross_an[3.0]), abs(net_an[0.0] - net_an[3.0]))
    parts = {}
    for inn in ('g', 't'):
        with open(f'./results/t6_part_{i}_{inn}.pkl', 'rb') as fh:
            parts[inn] = pickle.load(fh)
        assert parts[inn]['gate_ok'], (i, inn)
    derived['max_gap_gross'] = max(derived['max_gap_gross'], abs(gross_an[0.0] - parts['t']['sr_gross']), abs(gross_an[0.0] - parts['g']['sr_gross']))
    derived['max_gap_net'] = max(derived['max_gap_net'], abs(net_an[0.0] - parts['t']['sr_net']), abs(net_an[0.0] - parts['g']['sr_net']))
    derived['max_tails_gross'] = max(derived['max_tails_gross'], abs(parts['g']['sr_gross'] - parts['t']['sr_gross']))
    derived['max_cost'] = max(derived['max_cost'], parts['g']['sr_gross'] - parts['g']['sr_net'], parts['t']['sr_gross'] - parts['t']['sr_net'])
    if i == 4:
        derived['be_d01'] = parts['g']['f_mean'] / parts['g']['u_mean']
        derived['aU_d01'] = parts['g']['a_turnover']
        derived['net_mc_d01'] = parts['g']['sr_net']
    rows.append(f"\t\t{name} & {gross_an[0.0]:.3f} & {PRINTED_MC[i][0]} & {PRINTED_MC[i][1]} & "
                f"{net_an[0.0]:.3f} & {parts['g']['sr_net']:.3f} & {parts['t']['sr_net']:.3f} \\\\")

print(f"gates passed: analytic kappa=0 and kappa=3 reproduce the printed values for all 8 rows; mc gates from parts hold")
for k, v in derived.items():
    print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
print("\n".join(rows))
with open('./results/t6_new_rows.pkl', 'wb') as fh:
    pickle.dump(dict(rows=rows, derived=derived, tur_ls=float(tur_ls)), fh)
