---
myst:
  html_meta:
    description: >-
      The research paper behind trendfollowing, The Science and Practice of Trend-Following
      Systems by Sepp and Lucic, with the handbook chapter that develops each section, the map
      from manuscript exhibits to their generators, the frozen reference inputs and the
      verification scripts.
---

# Paper and replication

*Author: [Artur Sepp](https://github.com/ArturSepp) / First recorded: [2026-08-16](https://github.com/ArturSepp/TrendFollowingSystems/commit/1bceb64e2e10fa0014d10f4fbb69c84ece61f667)*

The package accompanies Artur Sepp and Vladimir Lucic's *The Science and Practice of
Trend-Following Systems*, of which [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems)
is the replication package.
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

- [Read the paper on SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787), or on
  [arXiv](https://arxiv.org/abs/2607.19497).
- [Open the replication guide](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/papers/tf_systems/README.md).
- [Browse the replication modules](https://github.com/ArturSepp/TrendFollowingSystems/tree/main/papers/tf_systems/replication).
- [Cite the software and paper](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

The wheel contains the immutable futures inputs used by the public examples. Frozen paper caches remain in the source checkout under
`papers/tf_systems/replication/data/reference/`; new caches and generated outputs
go to the external runtime. Neither is installed as package resources. See the replication guide before regenerating exhibits.

For a shorter route into the implementation, begin with the maintained
{doc}`example workflows <workflows>`.

## The paper in the handbook

The paper classifies trend-following systems into European, American and time-series-momentum
designs and develops the analytical theory of the European system: an exact sample-path identity
for the P&L, closed-form gross and leading-order net Sharpe ratios under a stationary
autocorrelation function, a Poisson-kernel spectral reading of the alpha, cost asymptotics, and the
closed-form skewness of aggregated returns. Each section is developed in a handbook chapter:

| Paper section | Handbook chapter |
|---|---|
| 2.1 EWMA filter | [EWMA filters and variance-preserving signals](ewma_filters.md) |
| 2.2 Volatility estimation | [Volatility normalisation and position sizing](volatility_normalisation.md) |
| 3, 4 and Appendix A: the three systems | [European](european_system.md), [American](american_system.md) and [TSMOM](tsmom_system.md) systems |
| 4.2–4.5 Cumulative and expected return | [The P&L decomposition](pnl_decomposition.md) |
| 4.4 Turnover; Appendix C | [Turnover, trading costs and the net Sharpe ratio](turnover_and_net_sharpe.md) |
| 5 Sharpe ratio | [The closed-form Sharpe ratio](sharpe_ratio_closed_form.md) |
| 6 Specific processes and verification | [Return-generating processes](return_processes.md), [Sharpe ratios under named processes](sharpe_under_processes.md) |
| 7.1–7.3 Implementation and attribution | [The futures evidence](case_study_futures_evidence.md), [the futures universe](futures_universe_and_costs.md), [realised Sharpe ratios](sharpe_inference.md) |
| 7.4 and Appendix D: skewness | [Skewness of aggregated returns](aggregated_skewness.md) |

## Exhibits and their generators

One entry point reproduces every figure, driven by the `PaperFigure` enum:

```console
python -m papers.tf_systems.replication.reproduce_all_figures
```

| Manuscript exhibit | Figure file | Generator in `papers/tf_systems/replication/` |
|---|---|---|
| Figure 2.1, filter impulse responses | `signal_weight` | `filter_figs.py` |
| Figure 4.1, the system on S&P 500 futures | `ES1_short_signals` | `illustrate_systems.py` |
| Figures 6.1–6.3, process figures | `expected_return_white_noise`, `_ar`, `_arfima1` | `mc_net_sharpe_paper_figs.py`, from frozen caches |
| Table 6.1, Student-t verification | `sharpe_verification_t6` | `mc_sharpe.py`, `t6_assemble.py`, from generated parts |
| Tables 7.1 and 7.2, universe and costs | `universe_table`, `cost_assumptions` | stages of `reproduce_all_figures.py` |
| Figure 7.1, grid backtests | `european_grid`, `american_grid_spans`, `tsmom_grid` | `backtest_figs.py` |
| Figure 7.2, SG Trend comparison | `tf_sg_backtest_paper` | `backtest_figs.py` |
| Figures 7.3 and 7.4, attribution | `tf_prediction_scatter`, `tf_prediction_medians` | `cross_system_attribution_figs.py`, from the frozen grid cache |
| Figure 7.5, aggregated skewness | `aggregated_skewness` | `aggregated_skewness_fig.py` |

Render the exhibits available from the frozen caches without recomputation, and run the
Ledoit–Wolf comparison with the SG Trend Index:

```console
python -m papers.tf_systems.replication.cached_figures
python -m papers.tf_systems.replication.sg_sharpe_test
```

The handbook displays the twelve approved manuscript figures from `papers/tf_systems/paper/figures/`.
New output, caches and LaTeX builds go to external folders, never into the checkout; the frozen
reference inputs carry SHA-256 hashes and are not regenerated to agree with new code.

## Verification of manuscript claims

Standalone scripts in `papers/tf_systems/replication/` check the analytical claims of the paper:

- `verify_cumreturn_boundary.py`: the boundary term of the sample-path identity to machine
  precision, and its order $N/T$.
- `verify_asymptotics.py`: the AR(1) break-even cost and the ARFIMA large-cost asymptotics.
- `verify_garch_and_truncation.py`: the GARCH(1,1) normalisation pipeline and the ARFIMA
  truncation bound.
- `verify_ls_normalization.py`: the unit variance of the long-short filter and the turnover closed
  form against Monte Carlo.
- `verify_arfima_variance_scale.py`: the ARFIMA variance scale of the drift normalisation, also run
  as a separate CI job.

The handbook's worked examples repeat several of these checks in a few lines each and run in the
package test suite.

## Citation

```bibtex
@article{SeppLucic2026trendfollowing,
  author        = {Sepp, Artur and Lucic, Vladimir},
  title         = {The Science and Practice of Trend-Following Systems},
  year          = {2026},
  eprint        = {2607.19497},
  archivePrefix = {arXiv},
  primaryClass  = {q-fin.ST},
  note          = {SSRN: \url{https://ssrn.com/abstract=3167787}},
  doi           = {10.2139/ssrn.3167787}
}
```

Cite the software version a replication ran as well; the
[README](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/README.md#citation) gives the
`@software` entry.
