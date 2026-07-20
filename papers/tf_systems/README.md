# The Science and Practice of Trend-Following Systems

Replication folder for Sepp & Lucic, *The Science and Practice of
Trend-Following Systems*. The compiled manuscript is
[`paper/TrendFollowing_PaperA_SIFIN_v1.pdf`](paper/TrendFollowing_PaperA_SIFIN_v1.pdf)
(47 pages). The analytics are implemented in the `trendfollowing` package at
the repository root; this folder holds the manuscript source and the code that
regenerates every figure and table.

## The paper in one paragraph

We classify trend-following systems into European, American, and Time Series
Momentum designs and develop the analytical theory around the European system.
The central results are an exact sample-path identity decomposing the
cumulative P&L into a realized-autocorrelation channel and a squared-drift
channel, closed-form gross and leading-order net Sharpe ratios under a generic
stationary autocorrelation function within the linear-process class (the
excess kurtosis of the innovations enters through a single loading), a
Poisson-kernel spectral reading of the alpha, and cost asymptotics: a nearly
span-invariant AR-1 break-even cost of 37bp to 41bp at phi = 0.05 against
realistic costs of 40bp to 60bp, and an interior cost-optimal span under
ARFIMA long memory. On 84 liquid futures contracts, the sample autocorrelation
function and drift reproduce the realized Sharpe ratios of the European system
with a pooled correlation of 0.99 and a slope of 0.96, of the TSMOM system
with 0.89 and 0.73, and of the American system with 0.92 and 0.61 at the spans
above one month. At matched parameters, all three systems are statistically
indistinguishable from the SG Trend Index by the Ledoit-Wolf test (Sharpe
ratios of 0.47, 0.50, and 0.55 against 0.47, net of costs and 2/20 fees).

## Layout

```
tf_systems/
├── Makefile
├── paper/                       LaTeX source and the compiled manuscript
│   ├── TrendFollowing_PaperA_SIFIN_v1.tex  .pdf
│   └── figures/                 the eleven manuscript figures (committed; regenerable)
├── replication/
│   ├── *.py                     exhibit generators and verification scripts (maps below)
│   ├── data/                    empty by design: the paper runs from the common dataset in
│   │                            trendfollowing/resources/ (see data/README.md)
│   └── results/                 committed Monte Carlo caches (process-figure parts, grid cache)
└── private/                     untracked local notes and reviews (never published)
```

## LaTeX class file

Read and download the paper on SSRN:
[ssrn.com/abstract=3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787).
The LaTeX source, figures, and compiled PDF here are the replication copy.

SIFIN is one of SIAM's online-only journals, so the manuscript uses
`siamonline250211.cls` from SIAM's
[LaTeX2e Multimedia Macros](https://epubs.siam.org/journal-authors). The class
file is committed in `paper/`, so the folder is self-contained:
`make paper` runs three `pdflatex` passes with no BibTeX (the bibliography is
inline).
The committed PDF is the production build: 47 pages, zero warnings, zero
overfull boxes. The 3.05pt overfull `\vbox` per running-head page in the log
is inherent to the class and invisible in the PDF, as documented in the
preamble.

## Reproducing the exhibits

Exhibit generators run from the repository root (they import
`papers.tf_systems.replication.*` and `trendfollowing`):

```bash
python -m papers.tf_systems.replication.reproduce_all_figures
```

The `PaperFigure` enum maps the manuscript exhibits to the generators:

| Manuscript exhibit | figure file(s) | generator |
|---|---|---|
| Figure 2.1 filter impulse responses | `signal_weight` | `filter_figs.py` |
| Figure 4.1 system illustration on ES1 | `ES1_short_signals` | `illustrate_systems.py` |
| Figures 6.1-6.3 process figures | `expected_return_{white_noise, ar, arfima1}` | `mc_net_sharpe_paper_figs.py` (from `results/` caches) |
| Table 6.1 Student-t verification | `sharpe_verification_t6` | `mc_sharpe.py`, `t6_assemble.py` (from `results/` caches) |
| Table 7.1 universe, Table 7.2 costs | `universe_table`, `cost_assumptions` | `reproduce_all_figures.py` stages |
| Figure 7.1 grid backtests | `european_grid`, `american_grid_spans`, `tsmom_grid` | `backtest_figs.py` |
| Figure 7.2 SG Trend comparison | `tf_sg_backtest_paper` | `backtest_figs.py` |
| Figures 7.3-7.4 attribution | `tf_prediction_scatter`, `tf_prediction_medians` | `cross_system_attribution_figs.py` (grid cache in `results/`) |
| Figure 7.4 aggregated skewness | `aggregated_skewness` | `aggregated_skewness_fig.py` (closed form + MC + empirical panel, requires the packaged data) |

Simulation figures are seed-exact (seed 8) and need no data. The Monte Carlo
aggregates behind the process figures and the verification table are cached in
`replication/results/`, so those figures re-render in seconds without
re-simulation: re-rendering from the committed caches reproduces the committed
PNGs pixel for pixel. Empirical figures run from the packaged dataset.
Figures are written to `TF_FIGURE_PATH` if set, and to the `qis` output path
otherwise.

The statistical comparison against the SG Trend Index (Ledoit-Wolf test on
monthly net-of-fee returns) reruns with:

```bash
cd replication && PYTHONPATH=../../.. python sg_sharpe_test.py
```

## Verification of manuscript claims
- `verify_cumreturn_boundary.py` — machine-precision check of the boundary term R_T in the
  sample-path identity (Proposition on the cumulative return) and its O(span/T) scaling.
- `verify_asymptotics.py` — Propositions C.2 and C.3: AR-1 break-even closed form and the ARFIMA
  large-cost asymptotics (optimal span ~ c^(1/2d), net-to-gross limit 4d/(1+2d)).
- `verify_garch_and_truncation.py` — GARCH(1,1) pipeline check (volatility normalization recovers
  the iid innovations) and the ARFIMA ACF truncation bound (<1e-4 relative at the longest span).
- `ewma_variance_check.py` — variance-preserving filter normalizations.
- `net_sharpe_span.py`, `optimal_span.py` — net-Sharpe span profiles and cost-optimal span numerics.

## Cross-system attribution development
- `grid_search_systems.py` — parameter search over American (span, short) and TSMOM (L, M)
  specifications; identifies (short=2) and (L=1, M=span) as the closest discretized counterparts
  of the European filter. Results cached in `grid_cache.pkl`.
- `cross_system_attribution.py`, `cross_system_attribution_best.py`, `cross_system_panel_c.py` —
  exploratory versions of the cross-system exhibits. The paper figures are produced by
  `paper_code/tf_systems/cross_system_attribution_figs.py`.

## Process-figure machinery (superseded by the package module)
- `figpass_orchestrate.py`, `figpass_plot.py` — resumable per-configuration Monte Carlo parts and
  the restyled plotting pass. The maintained version is
  `paper_code/tf_systems/mc_net_sharpe_paper_figs.py`.
- `wn_orchestrate.py`, `gen_wn_net.py`, `gen_arfima_net.py` — earlier white-noise and ARFIMA
  generators, kept for reference (old figure style).

## Table 6.1 machinery
- `t6_ls_parts.py`, `t6_assemble.py`, `t6_kappa_column.py` — resumable Monte Carlo parts and
  assembly for the verification table with Gaussian and Student-t innovations.

## Caches
- `grid_cache.pkl` — predicted/realized Sharpe tables for all systems and the grid-search results.
- `expected_return_*_part_*.pkl` — per-configuration Monte Carlo aggregates (seed 8) behind the
  three process figures; `mc_net_sharpe_paper_figs.LocalTests.PLOT` renders from these directly.
- `verify_ls_normalization.py` — unit test of the long-short normalization (unit signal variance)
- `verify_skewness_directions.py` — MC direction checks behind the skewness subsection:
  positive autocorrelation and long memory raise the aggregated profile, mean reversion
  lowers it, the hump is preserved (about five minutes)
  and the corrected turnover closed form against direct Monte Carlo; would have caught both the
  q-exponent inversion and the zeta formula error found in the July 2026 mathematical audits.
