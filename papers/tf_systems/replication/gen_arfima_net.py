import sys, time; # run from the repository root with the package installed
import numpy as np
import matplotlib; matplotlib.use('Agg')
import qis
from papers.tf_systems.replication import mc_expected_return_figs as mf

t0 = time.time()
mf.pe.set_seed(8)
spans = {'1w': 5, '2w': 10, '1m': 21, '3m': 63, '6m': 125, '1y': 250, '2y': 500}
fig = mf.plot_article_mc_figure(process_type=mf.pe.ProcessType.ARFIMA, phis=[0.05, 0.0, -0.05], delta=0.02, mean=0.0,
                                long_spans=spans, short_span=None, n_path=1000, n_years=50, tr_costs=0.0,
                                net_cost=0.0020, figure_type=mf.FigureType.AX3_NET_SHARPE)
qis.save_fig(fig, file_name='expected_return_arfima1', local_path='./figs/')
print(f"figure saved in {time.time()-t0:.0f}s", flush=True)
ax_net = fig.axes[2]
for line in ax_net.get_lines():
    y = line.get_ydata()
    if len(y) == len(spans) and np.all(np.isfinite(y)):
        print('  panel C series: ' + '  '.join(f"{v:6.3f}" for v in y), flush=True)
print("DONE", flush=True)
