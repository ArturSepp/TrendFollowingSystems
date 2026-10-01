"""The analytic expected return of the ARFIMA process figure against its frozen Monte Carlo."""

import pickle

import pytest

from papers.tf_systems.replication import mc_net_sharpe_paper_figs as process
from papers.tf_systems.replication import paths
from trendfollowing.analytics.expected_return import expected_pnl_arfima

FIG_NAME = "expected_return_arfima1"


@pytest.mark.parametrize("k", range(3))
def test_arfima_expected_return_within_frozen_mc_interval(k):
    """With the 2000-lag ACF of Section 5.1 the analytic value is inside the 95% MC interval."""
    cfg = process.FIGS[FIG_NAME]
    # trusted frozen input, see data/reference/README.md; test_resources checks its hash
    with open(process._part_file(str(paths.REFERENCE_DIR), FIG_NAME, k), "rb") as f:
        part = pickle.load(f)
    phi = cfg["variables"][k]
    for key, span in process.SPANS.items():
        analytic = expected_pnl_arfima(delta=cfg["delta"], phi=phi, long_span=span,
                                       short_span=None, mean=0.0, vol_target=process.VOL_TARGET,
                                       annualization_factor=process.AF)
        assert abs(analytic - part["mc"][key]) <= part["mc_std"][key], (phi, key)
