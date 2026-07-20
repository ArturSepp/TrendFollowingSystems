"""panel (c) analogue for the best-spec american and tsmom systems:
cross-sectional medians of predicted (european closed form) and realized sharpe ratios by span,
with the interquartile band of the realized values"""
# packages
import pickle
import numpy as np
import matplotlib.pyplot as plt

cache = pickle.load(open('./results/grid_cache.pkl', 'rb'))
predicted = cache['predicted']
SPANS = [5, 10, 21, 42, 63, 125, 250, 520]

fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.2), tight_layout=True)
for ax, tag, prm, title in [(axes[0], 'am', 2, '(A) American TF (span, 2)'),
                            (axes[1], 'ts', 1, '(B) TSMOM (L=1, M=span)')]:
    med_pred, med_real, q1, q3, xs = [], [], [], [], []
    for span in SPANS:
        key = (tag, prm, span)
        if key not in cache:
            continue
        pairs = [(predicted.loc[t, span], v) for t, v in cache[key].items()
                 if t in predicted.index and np.isfinite(v) and np.isfinite(predicted.loc[t, span])]
        if len(pairs) < 10:
            continue
        p, r = np.array(pairs).T
        xs.append(span)
        med_pred.append(np.median(p)); med_real.append(np.median(r))
        q1.append(np.percentile(r, 25)); q3.append(np.percentile(r, 75))
    xs = np.array(xs)
    ax.fill_between(xs, q1, q3, color='steelblue', alpha=0.25, label='realized interquartile band')
    ax.plot(xs, med_real, color='steelblue', lw=1.8, marker='o', ms=4, label='realized median')
    ax.plot(xs, med_pred, color='firebrick', lw=1.8, marker='s', ms=4, ls='--', label='predicted median (European closed form)')
    ax.set_xscale('log')
    ax.set_xticks(SPANS); ax.set_xticklabels([str(s) for s in SPANS])
    ax.minorticks_off()
    ax.axhline(0.0, color='gray', lw=0.8)
    ax.set_xlabel('filter span (days)')
    ax.set_ylabel('Sharpe ratio')
    ax.set_title(f'{title}: n per span = {min(len(cache[(tag, prm, s)]) for s in xs)}-{max(len(cache[(tag, prm, s)]) for s in xs)}')
    ax.legend(loc='upper right', frameon=False, fontsize=9)
    print(f"{title}: spans {list(xs)}, realized medians {[f'{v:.2f}' for v in med_real]}, predicted medians {[f'{v:.2f}' for v in med_pred]}")
fig.suptitle('Cross-sectional medians by span: European prediction vs realized American and TSMOM performance', fontsize=12)
fig.savefig('./cross_system_panel_c.png', dpi=200)
print("figure saved")
