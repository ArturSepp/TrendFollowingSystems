"""
white-noise net-sharpe figure in resumable parts: identical functions, identical rng order, lower peak memory
usage: python wn_orchestrate.py 0|1|2 to compute one drift variable, python wn_orchestrate.py plot to assemble
"""
# packages
import gc
import sys
import time
import pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
# project
# run from the repository root with the package installed
import qis as qis
from qis.plots.utils import get_n_colors
from papers.tf_systems.replication import mc_expected_return_figs as mf
from trendfollowing.systems.european import compute_tf_strat_pnl
from trendfollowing.systems.backtest_utils import compute_path_stats
from trendfollowing.analytics.expected_return import expected_pnl_white_noise, expected_turnover
from trendfollowing.analytics.sharpe import sharpe_white_noise

MEANS = [-0.5, 0.0, 0.5]
SPANS = {'1w': 5, '2w': 10, '1m': 21, '3m': 63, '6m': 125, '1y': 250, '2y': 500}
N_PATH, N_YEARS, AF, VOL_TARGET, VOL_SPAN, NET_COST = 1000, 50, 260, 0.15, 33, 0.0020
PART = './results/wn_part_{k}.pkl'


def compute_variable(k: int) -> None:
    """generate paths for all means in rng order, compute the seven spans for mean index k only"""
    m_times = N_YEARS * AF
    mf.pe.set_seed(8)
    returns = None
    for i, mean_value in enumerate(MEANS):
        r = mf.pe.generate_paths(process_type=mf.pe.ProcessType.WHITE_NOISE,
                                 phi=np.array([0.0]), ar_params=[0.0], x0=np.array([0.0]),
                                 n_path=N_PATH, m_times=m_times, delta=0.0,
                                 mean=mean_value, noise_std=1.0, dt=1.0 / AF)
        if i == k:
            returns = r
        del r
        gc.collect()
    process_variable = MEANS[k]
    out = dict(mc={}, mc_std={}, tur={}, tur_std={}, sr={}, sr_std={}, srn={}, srn_std={},
               an={}, tur_an={}, sr_an={}, srn_an={})
    for key, tf_span in SPANS.items():
        t0 = time.time()
        pnl_paths, weights, vols = compute_tf_strat_pnl(returns=returns, long_span=tf_span, vol_span=VOL_SPAN,
                                                        vol_target=VOL_TARGET, short_span=None,
                                                        annualization_factor=AF)
        total_pnl, pnl_an, vol_an, sharpe = compute_path_stats(pnl_paths=pnl_paths, annualization_factor=AF)
        vol_turnover_an = AF * np.nanmean(vols[1:, :] * np.abs(weights[1:, :] - weights[:-1, :]), axis=0)
        out['mc'][key] = np.nanmean(pnl_an)
        out['mc_std'][key] = 1.96 * np.nanstd(pnl_an) / np.sqrt(N_PATH)
        out['tur'][key] = np.nanmean(vol_turnover_an)
        out['tur_std'][key] = 10.0 * 1.96 * np.nanstd(vol_turnover_an) / np.sqrt(N_PATH)
        out['sr'][key] = np.nanmean(sharpe)
        out['sr_std'][key] = 1.96 * np.nanstd(sharpe) / np.sqrt(N_PATH)
        sharpe_net = (pnl_an - NET_COST * vol_turnover_an) / vol_an
        out['srn'][key] = np.nanmean(sharpe_net)
        out['srn_std'][key] = 1.96 * np.nanstd(sharpe_net) / np.sqrt(N_PATH)
        out['an'][key] = expected_pnl_white_noise(mean=process_variable, long_span=tf_span, short_span=None,
                                                  vol_target=VOL_TARGET, annualization_factor=AF)
        out['sr_an'][key] = sharpe_white_noise(long_span=tf_span, short_span=None,
                                               sr_underlying=process_variable, af=AF)
        out['tur_an'][key] = expected_turnover(long_span=tf_span, short_span=None,
                                               annualization_factor=AF, vol_target=VOL_TARGET)
        var_code = mf.analytic_var_code(process_type=mf.pe.ProcessType.WHITE_NOISE,
                                        process_variable=process_variable, delta=0.0, mean=0.0,
                                        long_span=tf_span, short_span=None, annualization_factor=AF)
        out['srn_an'][key] = out['sr_an'][key] - NET_COST * out['tur_an'][key] / (VOL_TARGET * np.sqrt(var_code))
        del pnl_paths, weights, vols, total_pnl, pnl_an, vol_an, sharpe, sharpe_net, vol_turnover_an
        gc.collect()
        print(f"k={k} span {key}: done in {time.time() - t0:.0f}s", flush=True)
    with open(PART.format(k=k), 'wb') as f:
        pickle.dump(out, f)
    print(f"part {k} saved", flush=True)


def plot_assembled() -> None:
    parts = []
    for k in range(3):
        with open(PART.format(k=k), 'rb') as f:
            parts.append(pickle.load(f))
    frames = {}
    for field in ['mc', 'mc_std', 'tur', 'tur_std', 'sr', 'sr_std', 'srn', 'srn_std', 'an', 'tur_an', 'sr_an', 'srn_an']:
        cols = {}
        for k, part in enumerate(parts):
            tag = 'Analytic' if field.endswith('_an') or field == 'an' else 'Monte-Carlo'
            cols[f"{tag}, drift={MEANS[k]:0.2f}"] = pd.Series(part[field], name='MC')
        frames[field] = pd.DataFrame.from_dict(cols, orient='columns')
    colors = get_n_colors(n=3)
    with sns.axes_style('darkgrid'):
        kwargs = dict(ncols=2, legend_loc='upper center', capsize=10, exact_colors=colors, colors=colors,
                      fontsize=12, framealpha=0.9, size=5, marker='_', exact_marker='o')
        fig, axs = plt.subplots(1, 3, figsize=(18, 6), tight_layout=True)
        qis.plot_errorbar(df=frames['mc'], y_std_errors=frames['mc_std'], exact=frames['an'],
                          title="(A) Expected annual return of TF system", var_format='{:.1%}',
                          xlabel='Signal span', ax=axs[0], **kwargs)
        qis.plot_errorbar(df=frames['sr'], y_std_errors=frames['sr_std'], exact=frames['sr_an'],
                          title="(B) Sharpe ratio of TF system", var_format='{:.2f}',
                          xlabel='Signal span', ax=axs[1], **kwargs)
        qis.plot_errorbar(df=frames['srn'], y_std_errors=frames['srn_std'], exact=frames['srn_an'],
                          title=f"(C) Net Sharpe ratio at cost of {1e4 * NET_COST:0.0f}bp per unit turnover",
                          var_format='{:.2f}', xlabel='Signal span', ax=axs[2], **kwargs)
        axs[2].axhline(0.0, color='black', lw=1.0, ls='--', alpha=0.6)
    qis.save_fig(fig, file_name='expected_return_white_noise', local_path='./figs/')
    print("figure saved")
    for field in ['srn', 'srn_an']:
        print(field, '\n', frames[field].round(3).T.to_string())


if __name__ == '__main__':
    arg = sys.argv[1]
    if arg == 'plot':
        plot_assembled()
    else:
        compute_variable(int(arg))
