"""grid search: american short span and tsmom period length that best reproduce the european attribution"""
# packages
import sys, time, pickle, os
import numpy as np
import pandas as pd
# project
# run from the repository root with the package installed
import qis
from trendfollowing.universe import load_data
from papers.tf_systems.replication.autocorr_attribution import compute_attribution_tables, SPANS, WARMUP, MIN_OBS, AF
from trendfollowing.systems.american import run_american_system
from trendfollowing.systems.tsmom import compute_tsmom_signal_weight

CACHE = './results/grid_cache.pkl'
cache = pickle.load(open(CACHE, 'rb')) if os.path.exists(CACHE) else {}

prices = load_data()[0]
returns = qis.to_returns(prices, is_log_returns=True, is_first_zero=False)
returns_np = returns.to_numpy()

if 'predicted' not in cache:
    cache['predicted'], _, _, _ = compute_attribution_tables(prices=prices, spans=SPANS, long_short_pairs=None)
    pickle.dump(cache, open(CACHE, 'wb'))
predicted = cache['predicted']

def realized_row(pnl: np.ndarray) -> dict:
    out = {}
    for idx, ticker in enumerate(returns.columns):
        valid = np.where(np.isfinite(returns_np[:, idx]))[0]
        if len(valid) < WARMUP + MIN_OBS:
            continue
        f = pnl[valid[WARMUP:], idx]
        f = f[np.isfinite(f)]
        out[ticker] = float(np.sqrt(AF)*np.mean(f)/np.std(f)) if len(f) > MIN_OBS and np.std(f) > 0 else np.nan
    return out

def fit(pred_cells, real_cells):
    x = np.array(pred_cells); y = np.array(real_cells)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    b, a = np.polyfit(x, y, 1)
    return b, float(np.corrcoef(x, y)[0, 1]), len(x)

which = sys.argv[1]
if which == 'american':
    shorts = [int(s) for s in sys.argv[2:]]
    for short in shorts:
        for span in SPANS:
            key = ('am', short, span)
            if key in cache or short >= span / 2:
                continue
            t0 = time.time()
            out = run_american_system(prices=prices, long_span=span, short_span=short, volume_costs=0.0)
            pnl = out.instrument_pnl.to_numpy() if isinstance(out.instrument_pnl, pd.DataFrame) else out.instrument_pnl
            cache[key] = realized_row(pnl)
            pickle.dump(cache, open(CACHE, 'wb'))
            print(f"american short={short} span={span}: {time.time()-t0:.0f}s", flush=True)
elif which == 'tsmom':
    for L in [int(s) for s in sys.argv[2:]]:
        for span in SPANS:
            key = ('ts', L, span)
            m = max(1, int(round(span / L)))
            if key in cache or m < 2:
                continue
            t0 = time.time()
            w, _, _ = compute_tsmom_signal_weight(returns=returns, num_ra_returns=L, num_periods=m)
            cache[key] = realized_row((w.shift(1)*returns).to_numpy())
    

            pickle.dump(cache, open(CACHE, 'wb'))
            print(f"tsmom L={L} span={span} (M={m}): {time.time()-t0:.0f}s", flush=True)
elif which == 'report':
    print(f"{'system':>10} {'param':>6} {'slope':>7} {'corr':>6} {'n':>5}")
    for sysname, tag, params in [('american', 'am', [2, 3, 5, 10, 20]), ('tsmom', 'ts', [1, 2, 3, 5, 10, 21])]:
        for prm in params:
            xs, ys = [], []
            for span in SPANS:
                key = (tag, prm, span)
                if key not in cache:
                    continue
                r = cache[key]
                for tkr, v in r.items():
                    if tkr in predicted.index:
                        xs.append(predicted.loc[tkr, span]); ys.append(v)
            if xs:
                b, c, n = fit(xs, ys)
                print(f"{sysname:>10} {prm:>6} {b:7.3f} {c:6.3f} {n:>5}")
