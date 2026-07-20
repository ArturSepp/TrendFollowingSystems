"""
paper figures expected_return_{white_noise, ar, arfima1} in the print style of the manuscript:
okabe-ito colorblind-safe palette, enlarged fonts, seaborn darkgrid, darkblue titles
data are computed in resumable per-configuration parts with the identical rng stream (seed 8)
as the original module mc_expected_return_figs.py, so all values reproduce the manuscript
usage: run_local_test(COMPUTE_<FIG>) to build the parts, then run_local_test(PLOT) to render
"""
# packages
import gc
import os
import pickle
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from enum import Enum
from typing import Dict, List
# qis / project
import qis as qis
from papers.tf_systems.replication import mc_expected_return_figs as mf
from trendfollowing.systems.european import compute_tf_strat_pnl
from trendfollowing.systems.backtest_utils import compute_path_stats
from trendfollowing.analytics.expected_return import (expected_pnl_white_noise, expected_pnl_ar1,
                                                      expected_pnl_arfima, expected_turnover)
from trendfollowing.analytics.sharpe import sharpe_white_noise, sharpe_ar1, sharpe_arfima

SPANS: Dict[str, int] = {'1w': 5, '2w': 10, '1m': 21, '3m': 63, '6m': 125, '1y': 250, '2y': 500}
N_PATH, N_YEARS, AF = 1000, 50, 260
VOL_TARGET, VOL_SPAN, NET_COST = 0.15, 33, 0.0020  # net cost per unit of volatility-normalized turnover

# okabe-ito colorblind-safe palette per configuration, in the rng generation order
FIGS = {
    'expected_return_white_noise': dict(process=None, variables=[-0.5, 0.0, 0.5], delta=0.0,
                                        label='drift', colors=['#D55E00', '#000000', '#0072B2']),
    'expected_return_ar': dict(process='AR_P', variables=[0.05, -0.05], delta=0.0,
                               label='phi', colors=['#0072B2', '#D55E00']),
    'expected_return_arfima1': dict(process='ARFIMA', variables=[0.05, 0.0, -0.05], delta=0.02,
                                    label='phi', colors=['#0072B2', '#000000', '#D55E00']),
}


def _part_file(parts_path: str, fig_name: str, k: int) -> str:
    return os.path.join(parts_path, f"{fig_name}_part_{k}.pkl")


def compute_parts(fig_name: str,
                  parts_path: str,
                  ) -> None:
    """
    one generation pass over all configurations in rng order (seed 8), computing each part as its
    paths arrive; existing parts are skipped but their generation is consumed to keep the stream
    """
    cfg = FIGS[fig_name]
    m_times = N_YEARS * AF
    mf.pe.set_seed(8)
    os.makedirs(parts_path, exist_ok=True)
    for i, pv in enumerate(cfg['variables']):
        if cfg['process'] is None:
            returns = mf.pe.generate_paths(process_type=mf.pe.ProcessType.WHITE_NOISE,
                                           phi=np.array([0.0]), ar_params=[0.0], x0=np.array([0.0]),
                                           n_path=N_PATH, m_times=m_times, delta=0.0,
                                           mean=pv, noise_std=1.0, dt=1.0 / AF)
        else:
            process_type = getattr(mf.pe.ProcessType, cfg['process'])
            returns = mf.pe.generate_paths(process_type=process_type, phi=np.array([pv]),
                                           ar_params=[pv], x0=np.array([0.0]), n_path=N_PATH,
                                           m_times=m_times, delta=cfg['delta'], mean=0.0,
                                           noise_std=1.0, dt=1.0 / AF)
        if os.path.exists(_part_file(parts_path, fig_name, i)):
            print(f"{fig_name} part {i} exists, generation consumed for rng order only", flush=True)
        else:
            _compute_part(fig_name, i, pv, returns, parts_path)
        del returns
        gc.collect()


def _compute_part(fig_name: str, k: int, pv: float, returns: np.ndarray, parts_path: str) -> None:
    """monte carlo and analytic values for the seven spans of one configuration"""
    cfg = FIGS[fig_name]
    out = dict(mc={}, mc_std={}, sr={}, sr_std={}, srn={}, srn_std={}, an={}, tur_an={}, sr_an={}, srn_an={})
    for key, tf_span in SPANS.items():
        t0 = time.time()
        pnl_paths, weights, vols = compute_tf_strat_pnl(returns=returns, long_span=tf_span,
                                                        vol_span=VOL_SPAN, vol_target=VOL_TARGET,
                                                        short_span=None, annualization_factor=AF)
        total_pnl, pnl_an, vol_an, sharpe = compute_path_stats(pnl_paths=pnl_paths, annualization_factor=AF)
        vol_turnover_an = AF * np.nanmean(vols[1:, :] * np.abs(weights[1:, :] - weights[:-1, :]), axis=0)
        out['mc'][key] = np.nanmean(pnl_an)
        out['mc_std'][key] = 1.96 * np.nanstd(pnl_an) / np.sqrt(N_PATH)
        out['sr'][key] = np.nanmean(sharpe)
        out['sr_std'][key] = 1.96 * np.nanstd(sharpe) / np.sqrt(N_PATH)
        sharpe_net = (pnl_an - NET_COST * vol_turnover_an) / vol_an
        out['srn'][key] = np.nanmean(sharpe_net)
        out['srn_std'][key] = 1.96 * np.nanstd(sharpe_net) / np.sqrt(N_PATH)
        if cfg['process'] is None:
            out['an'][key] = expected_pnl_white_noise(mean=pv, long_span=tf_span, short_span=None,
                                                      vol_target=VOL_TARGET, annualization_factor=AF)
            out['sr_an'][key] = sharpe_white_noise(long_span=tf_span, short_span=None,
                                                   sr_underlying=pv, af=AF)
            process_type = mf.pe.ProcessType.WHITE_NOISE
        elif cfg['process'] == 'AR_P':
            out['an'][key] = expected_pnl_ar1(phi=pv, long_span=tf_span, short_span=None, mean=0.0,
                                              vol_target=VOL_TARGET, annualization_factor=AF)
            out['sr_an'][key] = sharpe_ar1(phi=pv, long_span=tf_span, short_span=None,
                                           sr_underlying=0.0, af=AF)
            process_type = mf.pe.ProcessType.AR_P
        else:
            out['an'][key] = expected_pnl_arfima(delta=cfg['delta'], phi=pv, long_span=tf_span,
                                                 short_span=None, mean=0.0, vol_target=VOL_TARGET,
                                                 annualization_factor=AF)
            out['sr_an'][key] = sharpe_arfima(d=cfg['delta'], phi=pv, long_span=tf_span,
                                              short_span=None, sr_underlying=0.0, af=AF)
            process_type = mf.pe.ProcessType.ARFIMA
        out['tur_an'][key] = expected_turnover(long_span=tf_span, short_span=None,
                                               annualization_factor=AF, vol_target=VOL_TARGET)
        var_code = mf.analytic_var_code(process_type=process_type, process_variable=pv,
                                        delta=cfg['delta'],
                                        mean=pv if cfg['process'] is None else 0.0,
                                        long_span=tf_span, short_span=None, annualization_factor=AF)
        out['srn_an'][key] = out['sr_an'][key] - NET_COST * out['tur_an'][key] / (VOL_TARGET * np.sqrt(var_code))
        del pnl_paths, weights, vols, total_pnl, pnl_an, vol_an, sharpe, sharpe_net, vol_turnover_an
        gc.collect()
        print(f"{fig_name} k={k} span {key}: {time.time() - t0:.0f}s", flush=True)
    with open(_part_file(parts_path, fig_name, k), 'wb') as f:
        pickle.dump(out, f)
    print(f"{fig_name} part {k} saved", flush=True)


def _frames_for(fig_name: str, parts_path: str) -> Dict[str, pd.DataFrame]:
    cfg = FIGS[fig_name]
    parts = []
    for k in range(len(cfg['variables'])):
        with open(_part_file(parts_path, fig_name, k), 'rb') as f:
            parts.append(pickle.load(f))
    out = {}
    for field in ['mc', 'mc_std', 'sr', 'sr_std', 'srn', 'srn_std', 'an', 'sr_an', 'srn_an']:
        cols = {}
        for k, part in enumerate(parts):
            tag = 'Analytic' if field.endswith('_an') or field == 'an' else 'MC'
            cols[f"{tag}, {cfg['label']}={cfg['variables'][k]:0.2f}"] = \
                pd.Series(part[field]).reindex(list(SPANS.keys()))
        out[field] = pd.DataFrame.from_dict(cols, orient='columns')
    return out


def _style_axes(axs: List[plt.Axes]) -> None:
    """print-legibility pass: titles 21pt darkblue, ticks 17pt, labels 18pt, legend 15pt"""
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


def plot_paper_figure(fig_name: str, parts_path: str) -> plt.Figure:
    """three-panel exhibit: expected annual return, gross sharpe, net sharpe at NET_COST"""
    cfg = FIGS[fig_name]
    f = _frames_for(fig_name, parts_path)
    with sns.axes_style('darkgrid'):
        kwargs = dict(ncols=2, legend_loc='upper center',
                      capsize=12, exact_colors=cfg['colors'], colors=cfg['colors'], fontsize=17,
                      framealpha=0.9, size=8, marker='_', exact_marker='o')
        fig, axs = plt.subplots(1, 3, figsize=(18, 5.5), tight_layout=True)
        qis.plot_errorbar(df=f['mc'], y_std_errors=f['mc_std'], exact=f['an'],
                          title="(A) Expected annual return of TF system", var_format='{:.1%}',
                          xlabel='Signal span', ax=axs[0], **kwargs)
        qis.plot_errorbar(df=f['sr'], y_std_errors=f['sr_std'], exact=f['sr_an'],
                          title="(B) Sharpe ratio of TF system", var_format='{:.2f}',
                          xlabel='Signal span', ax=axs[1], **kwargs)
        qis.plot_errorbar(df=f['srn'], y_std_errors=f['srn_std'], exact=f['srn_an'],
                          title="(C) Net Sharpe ratio",  # the cost level is stated in the caption
                          var_format='{:.2f}', xlabel='Signal span', ax=axs[2], **kwargs)
        axs[2].axhline(0.0, color='black', lw=1.2, ls='--', alpha=0.6)
        _style_axes(axs)
    return fig


class LocalTests(Enum):
    COMPUTE_WHITE_NOISE = 1
    COMPUTE_AR = 2
    COMPUTE_ARFIMA = 3   # slowest generation, ~15 minutes
    PLOT = 4             # renders all three figures from the parts


def run_local_test(local_test: LocalTests, parts_path: str = 'papers/tf_systems/replication/results') -> None:
    local_path = qis.local_path.get_output_path()
    if local_test == LocalTests.COMPUTE_WHITE_NOISE:
        compute_parts('expected_return_white_noise', parts_path=parts_path)
    elif local_test == LocalTests.COMPUTE_AR:
        compute_parts('expected_return_ar', parts_path=parts_path)
    elif local_test == LocalTests.COMPUTE_ARFIMA:
        compute_parts('expected_return_arfima1', parts_path=parts_path)
    elif local_test == LocalTests.PLOT:
        for fig_name in FIGS.keys():
            fig = plot_paper_figure(fig_name, parts_path=parts_path)
            qis.save_fig(fig, file_name=fig_name, local_path=local_path)
            plt.close(fig)
            print(f"{fig_name}: saved to {local_path}")


if __name__ == '__main__':
    run_local_test(LocalTests.PLOT)
