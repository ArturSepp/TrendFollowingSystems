"""cross-system attribution at the grid-search winners: american (span, 2) and tsmom (L=1, M=span)"""
# packages
import pickle
import numpy as np
import matplotlib.pyplot as plt

cache = pickle.load(open('./results/grid_cache.pkl', 'rb'))
predicted = cache['predicted']
SPANS = [5, 10, 21, 42, 63, 125, 250, 520]

fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.6), tight_layout=True)
cmap = plt.cm.viridis
for ax, tag, prm, title in [(axes[0], 'am', 2, '(A) American TF (span, 2)'),
                            (axes[1], 'ts', 1, '(B) TSMOM (L=1, M=span)')]:
    xs, ys, cs = [], [], []
    for si, span in enumerate(SPANS):
        key = (tag, prm, span)
        if key not in cache:
            continue
        for tkr, v in cache[key].items():
            if tkr in predicted.index:
                xs.append(predicted.loc[tkr, span]); ys.append(v); cs.append(si)
    x, y, c = np.array(xs), np.array(ys), np.array(cs)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y, c = x[ok], y[ok], c[ok]
    b, a = np.polyfit(x, y, 1)
    corr = float(np.corrcoef(x, y)[0, 1])
    slow = c >= 3  # spans >= 42
    b2, a2 = np.polyfit(x[slow], y[slow], 1)
    corr2 = float(np.corrcoef(x[slow], y[slow])[0, 1])
    lim = [min(x.min(), y.min()) - 0.1, max(x.max(), y.max()) + 0.1]
    sc = ax.scatter(x, y, s=12, alpha=0.6, c=c, cmap=cmap)
    ax.plot(lim, lim, 'k--', lw=1.0, label='diagonal')
    xg = np.linspace(lim[0], lim[1], 10)
    ax.plot(xg, a + b*xg, color='firebrick', lw=1.5,
            label=f'all spans: slope {b:.2f}, corr {corr:.2f}')
    ax.plot(xg, a2 + b2*xg, color='darkorange', lw=1.5, ls='-.',
            label=f'spans $\\geq$ 42: slope {b2:.2f}, corr {corr2:.2f}')
    ax.set_xlabel('Predicted Sharpe ratio (European closed form)')
    ax.set_ylabel('Realized Sharpe ratio')
    ax.set_title(f'{title}: n={len(x)}')
    ax.legend(loc='upper left', frameon=False, fontsize=9)
    ax.set_xlim(lim); ax.set_ylim(lim)
    print(f"{title}: all-spans slope {b:.3f} corr {corr:.3f} n={len(x)}; slow-spans slope {b2:.3f} corr {corr2:.3f} n={int(slow.sum())}")
cbar = fig.colorbar(sc, ax=axes, shrink=0.85, ticks=range(len(SPANS)))
cbar.ax.set_yticklabels([str(s) for s in SPANS])
cbar.set_label('filter span (days)')
fig.suptitle('European closed form predicts American and TSMOM performance at the best-matching parameters', fontsize=12)
fig.savefig('./cross_system_attribution_best.png', dpi=200, bbox_inches='tight')
print("figure saved")
