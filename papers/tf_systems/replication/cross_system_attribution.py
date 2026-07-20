"""
cross-system attribution: predicted sharpe from the european closed form vs realized sharpe
of the american and tsmom systems at matched lookbacks
american: (long=span, short=5), paper defaults for buffer and stops, gross
tsmom: L=5 daily returns per period, M=round(span/5) periods, gross
"""
# packages
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# project
# run from the repository root with the package installed
import qis
from trendfollowing.universe import load_data
from papers.tf_systems.replication.autocorr_attribution import compute_attribution_tables, SPANS, WARMUP, MIN_OBS, AF
from trendfollowing.systems.american import run_american_system
from trendfollowing.systems.tsmom import compute_tsmom_signal_weight

prices = load_data()[0]
returns = qis.to_returns(prices, is_log_returns=True, is_first_zero=False)
returns_np = returns.to_numpy()
print(f"universe: {prices.shape[1]} instruments, {prices.index[0].date()} to {prices.index[-1].date()}")

predicted, _, _, _ = compute_attribution_tables(prices=prices, spans=SPANS, long_short_pairs=None)
print(f"predicted table: {predicted.shape}")

def realized_sr_table(pnl_by_span: dict) -> pd.DataFrame:
    out = {}
    for ticker_idx, ticker in enumerate(returns.columns):
        valid = np.where(np.isfinite(returns_np[:, ticker_idx]))[0]
        if len(valid) < WARMUP + MIN_OBS:
            continue
        sample = valid[WARMUP:]
        row = {}
        for span, pnl in pnl_by_span.items():
            f_i = pnl[sample, ticker_idx]
            f_i = f_i[np.isfinite(f_i)]
            row[span] = float(np.sqrt(AF) * np.mean(f_i) / np.std(f_i)) if len(f_i) > MIN_OBS and np.std(f_i) > 0 else np.nan
        out[ticker] = row
    return pd.DataFrame.from_dict(out, orient='index')

am_pnls, ts_pnls = {}, {}
for span in SPANS:
    out = run_american_system(prices=prices, long_span=span, short_span=5, volume_costs=0.0)
    am = out.instrument_pnl
    am_pnls[span] = am.to_numpy() if isinstance(am, pd.DataFrame) else am
    m = max(1, int(round(span / 5)))
    w, _, _ = compute_tsmom_signal_weight(returns=returns, num_ra_returns=5, num_periods=m)
    ts_pnls[span] = (w.shift(1) * returns).to_numpy()
    print(f"span {span}: american and tsmom(M={m}) done", flush=True)

realized_am = realized_sr_table(am_pnls)
realized_ts = realized_sr_table(ts_pnls)

fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.6), tight_layout=True)
for ax, realized, title in [(axes[0], realized_am, '(A) American TF (span, 5)'),
                            (axes[1], realized_ts, '(B) TSMOM (L=5, M=span/5)')]:
    common = predicted.index.intersection(realized.index)
    x = predicted.loc[common, SPANS].to_numpy().ravel()
    y = realized.loc[common, SPANS].to_numpy().ravel()
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    b, a = np.polyfit(x, y, 1)
    corr = float(np.corrcoef(x, y)[0, 1])
    lim = [min(x.min(), y.min()) - 0.1, max(x.max(), y.max()) + 0.1]
    ax.scatter(x, y, s=12, alpha=0.5, color='steelblue')
    ax.plot(lim, lim, 'k--', lw=1.0, label='diagonal')
    xs = np.linspace(lim[0], lim[1], 10)
    ax.plot(xs, a + b*xs, color='firebrick', lw=1.5, label=f'fit: slope {b:.2f}, corr {corr:.2f}')
    ax.set_xlabel('Predicted Sharpe ratio (European closed form)')
    ax.set_ylabel('Realized Sharpe ratio')
    ax.set_title(f'{title}: n={len(x)}')
    ax.legend(loc='upper left', frameon=False)
    ax.set_xlim(lim); ax.set_ylim(lim)
    print(f"{title}: slope {b:.3f}, intercept {a:.3f}, corr {corr:.3f}, n {len(x)}")
fig.suptitle('European closed form predicts American and TSMOM performance', fontsize=12)
fig.savefig('./cross_system_attribution.png', dpi=200)
print("figure saved")
