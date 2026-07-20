"""
paper figures tf_prediction_scatter and tf_prediction_medians: the european closed-form sharpe
predicted from the sample acf and drift of z_t against the realized gross backtests of the
european, american, and tsmom systems at matched lookbacks
american short span = 2 days and tsmom period length L = 1 day with M = span periods are the
closest discretized counterparts of the european filter (grid search in papers/tf_systems/replication/results/grid_search_systems.py)
"""
# packages
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from enum import Enum
from typing import Dict, Optional, Tuple
# qis / project
import qis as qis
from trendfollowing.universe import load_data
from papers.tf_systems.replication.autocorr_attribution import (compute_attribution_tables,
                                                                       SPANS, WARMUP, MIN_OBS, AF)
from trendfollowing.systems.american import run_american_system
from trendfollowing.systems.tsmom import compute_tsmom_signal_weight

AM_SHORT_SPAN: int = 2   # american fast leg, days
TSMOM_L: int = 1         # tsmom period length, days; M = span periods
SLOW_SPAN_MIN: int = 42  # threshold for the slow-span fit lines

PANELS = [('eu', '(A) European TF'), ('am', '(B) American TF'), ('ts', '(C) TSMOM TF')]


def compute_cross_system_tables(prices: pd.DataFrame,
                                cache_file: Optional[str] = None,  # pickle with precomputed tables
                                ) -> Dict[str, pd.DataFrame]:
    """
    predicted (total and autocorrelation-only) sharpe tables from the european closed form and
    realized gross sharpe tables of the three systems, instruments x spans
    the full computation runs the american and tsmom backtests at all spans and takes ~15 minutes
    """
    if cache_file is not None:
        with open(cache_file, 'rb') as f:
            cache = pickle.load(f)
        tables = dict(predicted=cache['predicted'], predicted_ac=cache['predicted_ac'],
                      realized_eu=cache['realised_eu'])
        for tag, prm in [('am', AM_SHORT_SPAN), ('ts', TSMOM_L)]:
            cols = {span: pd.Series(cache[(tag, prm, span)]) for span in SPANS}
            tables[f"realized_{tag}"] = pd.DataFrame(cols)
        return tables

    predicted, predicted_ac, realized_eu, _ = compute_attribution_tables(prices=prices, spans=SPANS,
                                                                         long_short_pairs=None)
    returns = qis.to_returns(prices, is_log_returns=True, is_first_zero=False)
    returns_np = returns.to_numpy()

    def realized_sr_table(pnl_by_span: Dict[int, np.ndarray]) -> pd.DataFrame:
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
                row[span] = float(np.sqrt(AF) * np.mean(f_i) / np.std(f_i)) \
                    if len(f_i) > MIN_OBS and np.std(f_i) > 0 else np.nan
            out[ticker] = row
        return pd.DataFrame.from_dict(out, orient='index')

    am_pnls, ts_pnls = {}, {}
    for span in SPANS:
        out = run_american_system(prices=prices, long_span=span, short_span=AM_SHORT_SPAN, volume_costs=0.0)
        am = out.instrument_pnl
        am_pnls[span] = am.to_numpy() if isinstance(am, pd.DataFrame) else am
        w, _, _ = compute_tsmom_signal_weight(returns=returns, num_ra_returns=TSMOM_L, num_periods=span)
        ts_pnls[span] = (w.shift(1) * returns).to_numpy()
        print(f"span {span}: american and tsmom backtests done", flush=True)
    return dict(predicted=predicted, predicted_ac=predicted_ac, realized_eu=realized_eu,
                realized_am=realized_sr_table(am_pnls), realized_ts=realized_sr_table(ts_pnls))


def _panel_data(tables: Dict[str, pd.DataFrame], tag: str) -> np.ndarray:
    """long-form array (pred_total, pred_ac, realized, span_index) over matched instrument-span points"""
    predicted, predicted_ac = tables['predicted'], tables['predicted_ac']
    realized = tables[f"realized_{tag}"]
    rows = []
    for si, span in enumerate(SPANS):
        for tkr in realized.index:
            if tkr in predicted.index and span in realized.columns:
                rows.append((predicted.loc[tkr, span], predicted_ac.loc[tkr, span],
                             realized.loc[tkr, span], si))
    a = np.array(rows, dtype=float)
    return a[np.isfinite(a[:, 0]) & np.isfinite(a[:, 2])]


def plot_prediction_scatter(tables: Dict[str, pd.DataFrame]) -> plt.Figure:
    """paper figure tf_prediction_scatter: predicted vs realized sharpe per instrument and span"""
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(1, 3, figsize=(18, 5.5), tight_layout=True)
        cmap = plt.get_cmap('viridis', len(SPANS))
        for ax, (tag, title) in zip(axs, PANELS):
            d = _panel_data(tables, tag)
            x, y, si = d[:, 0], d[:, 2], d[:, 3].astype(int)
            for i, span in enumerate(SPANS):
                m = si == i
                ax.scatter(x[m], y[m], s=14, alpha=0.65, color=cmap(i),
                           label=f"span={span}" if tag == 'eu' else None)
            b, a0 = np.polyfit(x, y, 1)
            corr = float(np.corrcoef(x, y)[0, 1])
            slow = si >= SPANS.index(SLOW_SPAN_MIN)
            b2, a2 = np.polyfit(x[slow], y[slow], 1)
            corr2 = float(np.corrcoef(x[slow], y[slow])[0, 1])
            lims = np.array([min(x.min(), y.min()), max(x.max(), y.max())])
            ax.plot(lims, lims, color='black', linestyle='dashed', linewidth=1)
            xg = np.linspace(*lims, 10)
            ax.plot(xg, a0 + b * xg, color='red', linewidth=1.2,
                    label=f'all spans: slope={b:.2f}, corr={corr:.2f}')
            ax.plot(xg, a2 + b2 * xg, color='darkorange', linewidth=1.2, linestyle='-.',
                    label=f'spans$\\geq${SLOW_SPAN_MIN}: slope={b2:.2f}, corr={corr2:.2f}')
            ax.set_xlabel('Predicted Sharpe ratio from sample ACF and drift')
            ax.set_ylabel('Realized Sharpe ratio, gross')
            ax.set_title(title, fontsize=12, color='darkblue')
            ax.legend(loc='upper left', fontsize=7, ncol=2 if tag == 'eu' else 1)
            print(f"scatter {title}: all {b:.2f}/{corr:.2f} n={len(x)}; slow {b2:.2f}/{corr2:.2f}")
    return fig


def plot_prediction_medians(tables: Dict[str, pd.DataFrame]) -> plt.Figure:
    """paper figure tf_prediction_medians: cross-sectional medians by span with the prediction decomposition"""
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(1, 3, figsize=(18, 5.5), tight_layout=True)
        xticks = np.arange(len(SPANS))
        for ax, (tag, title) in zip(axs, PANELS):
            d = _panel_data(tables, tag)
            m_a, m_t, m_r, q1, q3 = [], [], [], [], []
            for i in range(len(SPANS)):
                m = d[:, 3].astype(int) == i
                m_a.append(np.nanmedian(d[m, 1]))
                m_t.append(np.nanmedian(d[m, 0]))
                m_r.append(np.nanmedian(d[m, 2]))
                q1.append(np.nanpercentile(d[m, 2], 25))
                q3.append(np.nanpercentile(d[m, 2], 75))
            ax.plot(xticks, m_a, marker='o', label='Predicted, autocorrelation only')
            ax.plot(xticks, m_t, marker='o', label='Predicted, autocorrelation and drift')
            ax.plot(xticks, m_r, marker='s', color='black', label='Realized, gross')
            ax.fill_between(xticks, q1, q3, alpha=0.2, color='black', label='Realized interquartile range')
            ax.set_xticks(xticks)
            ax.set_xticklabels([str(s) for s in SPANS])
            ax.axhline(0.0, color='grey', linewidth=0.5)
            ax.set_xlabel('EWMA filter span in days')
            ax.set_ylabel('Annualized Sharpe ratio')
            ax.set_title(title, fontsize=12, color='darkblue')
            ax.legend(loc='lower left', fontsize=8)
    return fig


class LocalTests(Enum):
    COMPUTE_AND_PLOT = 1   # full computation from the packaged dataset (~15 minutes)
    PLOT_FROM_CACHE = 2    # plot from papers/tf_systems/replication/results/grid_cache.pkl if present


def run_local_test(local_test: LocalTests) -> None:
    local_path = qis.local_path.get_output_path()
    if local_test == LocalTests.PLOT_FROM_CACHE:
        tables = compute_cross_system_tables(prices=None, cache_file='papers/tf_systems/replication/results/grid_cache.pkl')
    else:
        prices = load_data()[0]
        tables = compute_cross_system_tables(prices=prices)
    fig1 = plot_prediction_scatter(tables)
    fig2 = plot_prediction_medians(tables)
    qis.save_fig(fig1, file_name='tf_prediction_scatter', local_path=local_path)
    qis.save_fig(fig2, file_name='tf_prediction_medians', local_path=local_path)
    print(f"figures saved to {local_path}")


if __name__ == '__main__':
    run_local_test(LocalTests.PLOT_FROM_CACHE)
