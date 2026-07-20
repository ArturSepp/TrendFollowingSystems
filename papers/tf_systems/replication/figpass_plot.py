"""restyle the three process figures: okabe-ito cvd-safe palette, print-legible fonts, template conventions"""
# packages
import pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import sys
# run from the repository root with the package installed
import qis

SPANS = ['1w', '2w', '1m', '3m', '6m', '1y', '2y']
NET_COST = 0.0020
OUT = './{name}.PNG'
FIGS = {
    'expected_return_white_noise': dict(parts='results/wn_part_{k}.pkl', ks=3, labels=[('drift', -0.5), ('drift', 0.0), ('drift', 0.5)],
                                        colors=['#D55E00', '#000000', '#0072B2']),
    'expected_return_ar': dict(parts='results/ar_part_{k}.pkl', ks=2, labels=[('phi', 0.05), ('phi', -0.05)],
                               colors=['#0072B2', '#D55E00']),
    'expected_return_arfima1': dict(parts='results/arfima_part_{k}.pkl', ks=3, labels=[('phi', 0.05), ('phi', 0.0), ('phi', -0.05)],
                                    colors=['#0072B2', '#000000', '#D55E00']),
}

def frames_for(cfg):
    parts = [pickle.load(open(cfg['parts'].format(k=k), 'rb')) for k in range(cfg['ks'])]
    out = {}
    for field in ['mc', 'mc_std', 'sr', 'sr_std', 'srn', 'srn_std', 'an', 'sr_an', 'srn_an']:
        cols = {}
        for k, part in enumerate(parts):
            tag = 'Analytic' if field.endswith('_an') or field == 'an' else 'Monte-Carlo'
            pname, pval = cfg['labels'][k]
            cols[f"{tag}, {pname}={pval:0.2f}"] = pd.Series(part[field]).reindex(SPANS)
        out[field] = pd.DataFrame.from_dict(cols, orient='columns')
    return out

def style_axes(axs):
    for ax in axs:
        ax.title.set_fontsize(21)
        ax.title.set_color('darkblue')
        ax.tick_params(labelsize=17)
        ax.xaxis.label.set_size(18)
        ax.yaxis.label.set_size(18)
        leg = ax.get_legend()
        if leg is not None:
            for txt in leg.get_texts():
                txt.set_fontsize(15)
        for line in ax.get_lines():
            line.set_linewidth(2.2)

# value gates against the numbers quoted in the manuscript
gates = []
for name, cfg in FIGS.items():
    f = frames_for(cfg)
    if name == 'expected_return_white_noise':
        gates += [(abs(f['srn_an'].loc['1w', 'Analytic, drift=0.00'] + 0.339) < 0.01, 'wn drag 1w'),
                  (abs(f['srn_an'].loc['2y', 'Analytic, drift=0.00'] + 0.037) < 0.01, 'wn drag 2y'),
                  (abs(f['srn_an'].loc['2y', 'Analytic, drift=0.50'] - 0.254) < 0.01, 'wn net 2y')]
    if name == 'expected_return_arfima1':
        gates += [(abs(f['srn_an'].loc['1w', 'Analytic, phi=0.05'] - 0.68) < 0.01, 'arfima net 1w'),
                  (abs(f['srn_an'][['Analytic, phi=0.00']].max().iloc[0] - 0.192) < 0.01, 'arfima interior max')]
    with sns.axes_style('darkgrid'):
        kwargs = dict(ncols=2 if cfg['ks'] == 3 else 1, legend_loc='upper center', capsize=12,
                      exact_colors=cfg['colors'], colors=cfg['colors'], fontsize=17, framealpha=0.9,
                      size=8, marker='_', exact_marker='o')
        fig, axs = plt.subplots(1, 3, figsize=(18, 5.5), tight_layout=True)
        qis.plot_errorbar(df=f['mc'], y_std_errors=f['mc_std'], exact=f['an'],
                          title="(A) Expected annual return of TF system", var_format='{:.1%}',
                          xlabel='Signal span', ax=axs[0], **kwargs)
        qis.plot_errorbar(df=f['sr'], y_std_errors=f['sr_std'], exact=f['sr_an'],
                          title="(B) Sharpe ratio of TF system", var_format='{:.2f}',
                          xlabel='Signal span', ax=axs[1], **kwargs)
        qis.plot_errorbar(df=f['srn'], y_std_errors=f['srn_std'], exact=f['srn_an'],
                          title=f"(C) Net Sharpe ratio at cost of {1e4*NET_COST:0.0f}bp per unit turnover",
                          var_format='{:.2f}', xlabel='Signal span', ax=axs[2], **kwargs)
        axs[2].axhline(0.0, color='black', lw=1.2, ls='--', alpha=0.6)
        style_axes(axs)
    fig.savefig(OUT.format(name=name), dpi=300)
    plt.close(fig)
    print(f"{name}: saved")

for ok, label in gates:
    assert ok, f"GATE FAILED: {label}"
print("all value gates passed")
