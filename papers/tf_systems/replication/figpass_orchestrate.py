"""ar and arfima net-sharpe figure data in resumable parts, identical rng order to the originals
usage: python figpass_orchestrate.py ar 0|1 ; python figpass_orchestrate.py arfima 0|1|2"""
# packages
import gc, sys, time, pickle
import numpy as np
import matplotlib
matplotlib.use('Agg')
# project
# run from the repository root with the package installed
from papers.tf_systems.replication import mc_expected_return_figs as mf
from trendfollowing.systems.european import compute_tf_strat_pnl
from trendfollowing.systems.backtest_utils import compute_path_stats
from trendfollowing.analytics.expected_return import expected_pnl_ar1, expected_pnl_arfima, expected_turnover
from trendfollowing.analytics.sharpe import sharpe_ar1, sharpe_arfima

SPANS = {'1w': 5, '2w': 10, '1m': 21, '3m': 63, '6m': 125, '1y': 250, '2y': 500}
N_PATH, N_YEARS, AF, VOL_TARGET, VOL_SPAN, NET_COST = 1000, 50, 260, 0.15, 33, 0.0020
FIGS = {'ar': dict(process=mf.pe.ProcessType.AR_P, variables=[0.05, -0.05], delta=0.0),
        'arfima': dict(process=mf.pe.ProcessType.ARFIMA, variables=[0.05, 0.0, -0.05], delta=0.02)}
PART = './results/{fig}_part_{k}.pkl'

def compute_all(fig_key: str) -> None:
    """one generation pass, identical rng stream, compute each part as its paths arrive"""
    cfg = FIGS[fig_key]
    m_times = N_YEARS * AF
    mf.pe.set_seed(8)
    import os
    for i, pv in enumerate(cfg['variables']):
        returns = mf.pe.generate_paths(process_type=cfg['process'], phi=np.array([pv]), ar_params=[pv],
                                       x0=np.array([0.0]), n_path=N_PATH, m_times=m_times, delta=cfg['delta'],
                                       mean=0.0, noise_std=1.0, dt=1.0 / AF)
        if os.path.exists(PART.format(fig=fig_key, k=i)):
            print(f"{fig_key} part {i} exists, generation consumed for rng order only", flush=True)
        else:
            compute_part(fig_key, i, pv, returns)
        del returns
        gc.collect()


def compute_part(fig_key: str, k: int, pv: float, returns) -> None:
    cfg = FIGS[fig_key]
    out = dict(mc={}, mc_std={}, sr={}, sr_std={}, srn={}, srn_std={}, an={}, tur_an={}, sr_an={}, srn_an={})
    for key, tf_span in SPANS.items():
        t0 = time.time()
        pnl_paths, weights, vols = compute_tf_strat_pnl(returns=returns, long_span=tf_span, vol_span=VOL_SPAN,
                                                        vol_target=VOL_TARGET, short_span=None, annualization_factor=AF)
        total_pnl, pnl_an, vol_an, sharpe = compute_path_stats(pnl_paths=pnl_paths, annualization_factor=AF)
        vol_turnover_an = AF * np.nanmean(vols[1:, :] * np.abs(weights[1:, :] - weights[:-1, :]), axis=0)
        out['mc'][key] = np.nanmean(pnl_an)
        out['mc_std'][key] = 1.96 * np.nanstd(pnl_an) / np.sqrt(N_PATH)
        out['sr'][key] = np.nanmean(sharpe)
        out['sr_std'][key] = 1.96 * np.nanstd(sharpe) / np.sqrt(N_PATH)
        sharpe_net = (pnl_an - NET_COST * vol_turnover_an) / vol_an
        out['srn'][key] = np.nanmean(sharpe_net)
        out['srn_std'][key] = 1.96 * np.nanstd(sharpe_net) / np.sqrt(N_PATH)
        if fig_key == 'ar':
            out['an'][key] = expected_pnl_ar1(phi=pv, long_span=tf_span, short_span=None, mean=0.0,
                                              vol_target=VOL_TARGET, annualization_factor=AF)
            out['sr_an'][key] = sharpe_ar1(phi=pv, long_span=tf_span, short_span=None, sr_underlying=0.0, af=AF)
        else:
            out['an'][key] = expected_pnl_arfima(delta=cfg['delta'], phi=pv, long_span=tf_span, short_span=None,
                                                 mean=0.0, vol_target=VOL_TARGET, annualization_factor=AF)
            out['sr_an'][key] = sharpe_arfima(d=cfg['delta'], phi=pv, long_span=tf_span, short_span=None,
                                              sr_underlying=0.0, af=AF)
        out['tur_an'][key] = expected_turnover(long_span=tf_span, short_span=None,
                                               annualization_factor=AF, vol_target=VOL_TARGET)
        var_code = mf.analytic_var_code(process_type=cfg['process'], process_variable=pv, delta=cfg['delta'],
                                        mean=0.0, long_span=tf_span, short_span=None, annualization_factor=AF)
        out['srn_an'][key] = out['sr_an'][key] - NET_COST * out['tur_an'][key] / (VOL_TARGET * np.sqrt(var_code))
        del pnl_paths, weights, vols, total_pnl, pnl_an, vol_an, sharpe, sharpe_net, vol_turnover_an
        gc.collect()
        print(f"{fig_key} k={k} span {key}: {time.time()-t0:.0f}s", flush=True)
    with open(PART.format(fig=fig_key, k=k), 'wb') as f:
        pickle.dump(out, f)
    print(f"{fig_key} part {k} saved", flush=True)

if __name__ == '__main__':
    compute_all(sys.argv[1])
