# The Science and Practice of Trend-Following Systems

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Project: [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

Companion workspace for Sepp and Lucic, *The Science and Practice of
Trend-Following Systems*. The existing SIFIN LaTeX source, SIAM class and twelve
figure files are tracked. No compiled PDF is tracked or supplied by this layout
migration. Read the paper on [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787).
The SSRN-format source remains local. See the [paper contract](../AGENTS.md).

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

## Layout and builds

```text
tf_systems/
  paper/                    approved SIFIN source, class and twelve figures
  drafts/                   previous versions and their figures; ignored
  presentations/            local by default; no current public exceptions
  private/                  correspondence and reviews; ignored
  agents/                   working records; ignored
  replication/
    data/
      reference/            nine frozen caches, provenance and SHA-256 hashes
      local/                restricted inputs, if needed; ignored
    tests/                  offline input and output-routing checks
    *.py                    existing research and verification entry points
```

Local sections may be absent in a fresh clone. Common futures inputs remain in
`src/trendfollowing/resources/futures/`; they are not duplicated here. The nine
existing caches were moved without changing bytes from the former repository
`resources/papers/tf_systems/results/` directory. Legacy local caches in
`resources/` are retained but ignored. New runs use external runtime directories.

On the maintainer's Windows host, configure `Enter-AgentRepo.ps1` as directed by
root `AGENTS.md` and use `C:\Python\TrendFollowingSystems312\Scripts\python.exe`.
Never create an environment under OneDrive. `TF_PAPER_OUTPUT_PATH` selects an
absolute run directory outside the checkout and OneDrive; its default is the
configured `AGENT_LOCAL_ROOT/outputs/tf_systems` runtime. `TF_FIGURE_PATH` may
select a separate external figure directory.

To build the approved current manuscript from the repository root:

```console
python -m papers.tf_systems.replication.build_paper
```

This copies approved assets to external `latex-build/` and invokes three
pdflatex passes. The existing SIAM class remains tracked; the bibliography is
inline. The helper does not replace the source or publish a PDF. A successful
layout migration is not a claim that the manuscript compiled in this environment.

## Render the available frozen exhibits

```console
python -m papers.tf_systems.replication.cached_figures
python -m pytest papers/tf_systems/replication/tests -q
```

The first command reads only `replication/data/reference/` and renders the three
process figures and two cross-system attribution figures into external
`figures/`. It does not run the full Monte Carlo experiment or overwrite the
approved PNGs. Rendering can vary with dependency versions; pixel equality is
not assumed. The other manuscript exhibits require their own computation.

`mc_net_sharpe_paper_figs.run_local(COMPUTE_...)` writes new parts to external
`results/`. `PLOT` reads frozen references by default; pass an explicit external
`parts_path` to plot a newly generated run. Missing run parts raise an error
instead of falling back to historical caches.

## Full exhibit generation

The full generator includes expensive simulations and data-dependent stages.
Run it from the repository root in the configured environment (it imports
`papers.tf_systems.replication.*` and `trendfollowing`):

```bash
python -m papers.tf_systems.replication.reproduce_all_figures
```

The `PaperFigure` enum maps the manuscript exhibits to the generators:

| Manuscript exhibit | figure file(s) | generator |
|---|---|---|
| Figure 2.1 filter impulse responses | `signal_weight` | `filter_figs.py` |
| Figure 4.1 system illustration on ES1 | `ES1_short_signals` | `illustrate_systems.py` |
| Figures 6.1-6.3 process figures | `expected_return_{white_noise, ar, arfima1}` | `mc_net_sharpe_paper_figs.py` (from frozen reference caches) |
| Table 6.1 Student-t verification | `sharpe_verification_t6` | `mc_sharpe.py`, `t6_assemble.py` (requires separate generated `t6_part_*` caches) |
| Table 7.1 universe, Table 7.2 costs | `universe_table`, `cost_assumptions` | `reproduce_all_figures.py` stages |
| Figure 7.1 grid backtests | `european_grid`, `american_grid_spans`, `tsmom_grid` | `backtest_figs.py` |
| Figure 7.2 SG Trend comparison | `tf_sg_backtest_paper` | `backtest_figs.py` |
| Figures 7.3-7.4 attribution | `tf_prediction_scatter`, `tf_prediction_medians` | `cross_system_attribution_figs.py` (frozen grid cache in `data/reference/`) |
| Figure 7.4 aggregated skewness | `aggregated_skewness` | `aggregated_skewness_fig.py` (closed form + MC + empirical panel, requires the packaged data) |

The existing simulation designs and seeds are unchanged. Frozen reference
inputs cover the process figures and cross-system attribution, not every table.
Table 6.1 requires separately generated Monte Carlo parts. Empirical stages use
the packaged dataset; the ATR comparison may require terminal access.
New results and figure candidates remain external. See the
[cache provenance](replication/data/reference/README.md) for preservation scope.

The statistical comparison against the SG Trend Index (Ledoit-Wolf test on
monthly net-of-fee returns) reruns with:

```bash
python -m papers.tf_systems.replication.sg_sharpe_test
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
  of the European filter. New results cached in external `results/grid_cache.pkl`.
- `cross_system_attribution.py`, `cross_system_attribution_best.py`, `cross_system_panel_c.py` —
  exploratory versions of the cross-system exhibits. The paper figures are produced by
  `papers/tf_systems/replication/cross_system_attribution_figs.py`.

## Process-figure machinery (superseded by the package module)
- `figpass_orchestrate.py`, `figpass_plot.py` — resumable per-configuration Monte Carlo parts and
  the restyled plotting pass. The maintained version is
  `papers/tf_systems/replication/mc_net_sharpe_paper_figs.py`.
- `wn_orchestrate.py`, `gen_wn_net.py`, `gen_arfima_net.py` — earlier white-noise and ARFIMA
  generators, kept for reference (old figure style).

## Table 6.1 machinery
- `t6_ls_parts.py`, `t6_assemble.py`, `t6_kappa_column.py` — resumable Monte Carlo parts and
  assembly for the verification table with Gaussian and Student-t innovations.

## Caches
- `grid_cache.pkl` — predicted/realized Sharpe tables for all systems and the grid-search results.
- `expected_return_*_part_*.pkl` — per-configuration Monte Carlo aggregates (seed 8) behind the
  three process figures; `mc_net_sharpe_paper_figs.Locals.PLOT` renders from these directly.
- `verify_ls_normalization.py` — unit test of the long-short normalization (unit signal variance)
- `verify_skewness_directions.py` — MC direction checks behind the skewness subsection:
  positive autocorrelation and long memory raise the aggregated profile, mean reversion
  lowers it, the hump is preserved (about five minutes)
  and the corrected turnover closed form against direct Monte Carlo; would have caught both the
  q-exponent inversion and the zeta formula error found in the July 2026 mathematical audits.
