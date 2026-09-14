## Python environment (mandatory)

- Never create, use, or install packages into a Python virtual environment anywhere under `C:\Users\artur\OneDrive`.
- Keep this repository's environment outside OneDrive at `C:\Python\TrendFollowingSystems312`.
- Use `C:\Python\TrendFollowingSystems312\Scripts\python.exe` for Python, tests, linters, and package installation.
- If it is missing, create it with `py -3.12 -m venv C:\Python\TrendFollowingSystems312`.
- Never run plain `uv sync` or plain `uv run` from this checkout: uv otherwise creates `<repo>\.venv` even when uv was launched through a Python executable under `C:\Python`.
- If a uv project operation is required, first set `UV_PROJECT_ENVIRONMENT=C:\Python\TrendFollowingSystems312`; for pip-style operations prefer `uv pip ... --python C:\Python\TrendFollowingSystems312\Scripts\python.exe`.
- If any OneDrive-local environment already exists, do not use it; report it for removal.
- Run standard portfolio tasks through
  `& "$env:USERPROFILE\OneDrive\analytics\my_github\ArturSepp\scripts\repo_governance\Invoke-Repo.ps1" -Task verify`.
  Use `-Task check` or `-Task test` for a narrower run. The launcher selects this repository's
  external interpreter and routes generated state to C:.

# AGENTS.md

Guidance for AI coding agents working in the **TrendFollowingSystems** repository.

## Project overview

`trendfollowing` provides closed-form trend-following analytics, reference system
implementations, and reproducible futures evidence in Python for quantitative researchers
and practitioners. It is a research and replication library, not a broker integration or
general-purpose execution engine; portfolio analytics and reporting are delegated to `qis`.

It is the replication package for *The Science and Practice of Trend-Following Systems*
(Sepp and Lucic, 2026). Distribution and import name `trendfollowing`. Licensed
**GPL-3.0** (`LICENSE`) — unlike most of the stack, which is MIT. Depends on `qis` for
analytics and reporting.

## Ecosystem position

This package is one of ten public Python libraries maintained at
[github.com/ArturSepp](https://github.com/ArturSepp). Check the owning package before
adding a capability or copying code between repositories.

| Package | Repository | Purpose |
|---|---|---|
| `qis` | QuantInvestStrats | performance analytics, backtesting, and factsheet reporting |
| `optimalportfolios` | OptimalPortfolios | portfolio construction and rolling backtesting |
| `factorlasso` | FactorLasso | sparse factor-model estimation |
| `bbg-fetch` | BloombergFetch | Bloomberg data in pandas DataFrames |
| `stochvolmodels` | StochVolModels | stochastic-volatility pricing and calibration |
| `trendfollowing` | TrendFollowingSystems | closed-form trend-following analytics |
| `privateassets` | PrivateAssets | multi-factor PME for private assets |
| `goal-based-allocation` | GoalBasedAllocation | goal-based allocation under regime-switching jump-diffusions |
| `vanilla-option-pricers` | VanillaOptionPricers | Numba-vectorised BSM and Bachelier pricing |
| `option-chain-analytics` | OptionChainAnalytics | point-in-time option-chain data and queries |

Core dependency edges: `optimalportfolios` consumes `qis` and `factorlasso`;
`trendfollowing` and `privateassets` consume `qis`; `stochvolmodels` consumes
`vanilla-option-pricers`; `option-chain-analytics` consumes `qis` and
`vanilla-option-pricers`. The remaining packages have no core stack dependencies.

Optional edges: PrivateAssets' `factors` extra adds `factorlasso`; StochVolModels'
`research` extra adds `qis` and `option-chain-analytics`; OCA's `bloomberg` and `all`
extras add `bbg-fetch`. Core imports must work without optional dependencies.
OCA never imports StochVolModels or the private SigmaStrats consumer. Exact
maintainer-tool exceptions are recorded in `.github/stack-policy.json`; they do
not authorise adding those dependencies to core or importing them at package root.

## Repository layout

```
src/trendfollowing/
  analytics/   closed-form formulas for system moments
  processes/   price process models (white noise, AR(1), ARFIMA); local runners beside owners
  systems/     European, American and TSMOM system implementations
  run_local/   source-adjacent development runners; excluded from distributions
  resources/   immutable futures data installed with the package
  backtests.py, universe.py
resources/     writable paper replication caches; not installed
papers/        replication code for the paper (importable: papers.*)
tests/         top-level test modules (test_*.py)
examples/      runnable examples; kept at repository root
docs/          Sphinx/MyST documentation source; generated output stays untracked
```

## Commands

```bash
uv sync --locked --group test
uv run --no-sync pytest                                  # as CI runs it
uv run --no-sync pytest tests/test_sharpe.py -v          # one module
uv run --locked --only-group lint ruff check src/trendfollowing/
uv sync --locked --extra docs                            # documentation toolchain
uv run --no-sync python -m sphinx -E -W --keep-going -b html docs docs/_build/html
uv run --no-sync python -m sphinx -E -W -b linkcheck docs docs/_build/linkcheck
```

`[tool.pytest.ini_options] pythonpath = ["."]` puts the repository root on `sys.path`
only so tests can import the non-installed `papers.*` replication modules under a bare
`pytest` invocation. `tests/test_src_layout.py` prevents that exception from masking a
legacy root `trendfollowing/` package. Supported Python is >= 3.10; CI runs Linux 3.10–3.14
plus Windows and macOS 3.12, separate verification, and built-artifact jobs.

## Conventions

- Test files are named `test_*.py` and live in the top-level `tests/` directory. This is a
  deliberate deviation from the in-package `<subpackage>/tests/` layout the rest of the
  stack uses: this is a replication package, and a reviewer who downloads it should find
  the tests without first learning the package structure. Do not "fix" it to match a
  sibling.
- Development runners live in the nearest `run_local/<subject>_run.py` directory, define
  `Locals` and `run_local(local=...)`, and have no `__init__.py`. Never import `run_local`
  from production code or a public `__init__.py`; setuptools and `MANIFEST.in` exclude the
  runners from built distributions. Root `examples/` and development entry points under
  `papers/tf_systems/replication/` use the same dispatcher names; `reproduce_all_figures.py`
  orchestrates the paper cases through `run_local(local=...)`.
- Line length 100 (`ruff`, rules `E`, `F`, `W`). `I` is not selected anywhere in this
  stack: the import convention groups the scientific stack before the project packages,
  which isort reorders.
- Hot numerical paths are `numba`-compiled; keep them array-based and avoid Python-level
  loops or pandas operations inside compiled functions.
- Closed-form analytics and Monte Carlo estimates are cross-checked against each other:
  a new analytical result should come with the Monte Carlo test that verifies it.
- Enums carry system and process type selection.
- Reporting and plotting go through `qis`, which is a declared dependency.

## Constraints — do not do these

- Do not change analytical formulas without the corresponding Monte Carlo verification
  passing. The tests exist precisely to catch algebra errors.
- Do not modify the futures dataset in `src/trendfollowing/resources/futures/` or the
  universe definitions: published backtests depend on them.
- Do not reimplement performance statistics or plotting — use `qis`.
- Do not commit backtest output, figures, or log files (`sg.log` in the repository root
  is an accident, not a pattern to follow).

<!-- ===== SHARED AGENT CORE (consumer variant) — begin =====
     Generated from SHARED_AGENT_CORE.md in the maintainer's project knowledge. Do not hand-edit
     between these markers — propose the change to the maintainer instead. Variants: builder
     (qis) / consumer / standalone. Last synced 2026-09-13, agent core v1.6 -->

## Domain invariants

Not inferable from any single file, and the source of numerically wrong code that runs clean:

- **No look-ahead, anywhere in a backtest path.** A weight decided at *t* is applied over
  *[t, t+1]*. Estimation is point-in-time: `MeanAdjType.INSAMPLE` subtracts a full-sample mean
  and is therefore forward-looking — correct for a descriptive exhibit, wrong inside a backtest.
- **Return convention is stated, never implied** — `qis.to_returns(..., is_log_returns=...)`.
  Annualisation follows from the frequency; never silently switch convention, frequency, or
  annualisation factor.
- **Sharpe has three explicitly labelled conventions** in `qis`; excess variants need
  `PerfParams.rates_data`. State which one a number uses.
- **`qis.BootstrapType.STATIONARY` wraps circularly from qis 5.1.0.** Any result resampled under
  an earlier version does not reproduce.
- One convention per concept across the stack. If two packages disagree, that is a bug to
  report, not a difference to accommodate.

## Use the stack before you write it

This package consumes `qis` (analytics, backtesting, reporting). Reimplementing a capability it
exports is a defect, not a convenience. Triggers — stop and check the export list before
writing: backtest, rebalance, turnover, drawdown, Sharpe, volatility target, bootstrap,
resample, unsmooth, covariance, correlation, regime, factsheet, tracking error, realised
tracking error, information ratio, benchmark beta, marginal contribution, risk contribution.

- **The hard stop:** a `for` loop over dates accumulating a position, a weight or a P&L is
  `qis.backtest_model_portfolio`. The hand-rolled version gets drift adjustment wrong — `qis`
  holds *units* between rebalancings, not weights.
- **Never hand-roll `d' Σ d`, a beta ratio, or a TE decomposition.** Ex-ante tracking error,
  factor exposures, benchmark beta and marginal TE come from `qis.RiskModel` (a plain
  `{date: covar}` dict constructs a covariance-only model); realised ex-post TE is
  `qis.compute_ewma_realised_tracking_error` (EWMA series), and whole-sample TE/IR scalars are
  `qis.compute_te_ir_errors`.
- **Never invent a symbol.** If a function, class, or keyword argument is not in the export
  list, it does not exist. Check in one line —
  `python -c "import qis; print([n for n in dir(qis) if 'unsmooth' in n.lower()])"`;
  `qis.api.CORE_API` is the documented core and `help(qis.<symbol>)` gives the arguments. Say a
  symbol is missing rather than producing code that calls it.
- **If you genuinely must reimplement**, name the rejected stack symbol and why, in a comment on
  the line above the definition — that turns a silent divergence into a reviewable decision.
- Never introduce `quantstats`, `pyfolio`, `empyrical`, `ffn`, `bt`, or an ad-hoc statistics
  layer.

## Verification loop

- Plan → patch → verify. Name the verification command and its result when proposing a patch.
- A second pass is mandatory where a plausible patch can be numerically wrong and still run
  clean: estimation windows, signal construction, volatility targeting, annualisation, anything
  resampled. Verify against a reference computed a different way — here the closed-form
  analytics and the Monte Carlo tests cross-check each other — and say which.
- Prove a new test fails before trusting that it passes: reintroduce the defect, watch it fail,
  restore.

## Escalation and scope

- Stop and propose before proceeding when a change would exceed roughly five files, alter a
  public signature, or touch a numerical path.
- Never change numerical results, random seeds, or computed values unless the change is the
  request.
- A public-signature change carries a `CHANGELOG.md` entry and a version bump in the same
  change. Removing a keyword argument from a function taking `**kwargs` is a silent break — the
  caller's keyword is swallowed and nothing raises. Treat it as breaking.
- Do not refactor beyond the requested scope. Propose the wider change; do not perform it.

## Concurrent sessions

More than one agent or session may work on this checkout at the same time, so a file can change
between your read of it and your write.

- Re-read a file from disk immediately before editing it. Never write a file from an earlier
  read: a whole-file write from a stale copy silently reverts another session's work.
- Prefer minimal anchored edits over whole-file replacement. If the on-disk content is not what
  you expected, stop and reconcile your change onto the current content rather than overwrite.

## Agent-generated artifacts

All agent-generated roadmaps, execution plans, audits, reports, handoffs, and other working
outputs live under the repository-root `agents/` directory, which is local and ignored by Git.
Never create `ROADMAP_*.md`, `Claude outputs/`, `Codex outputs/`, or similar agent-output
artifacts at the repository root. Name feature roadmaps `agents/ROADMAP_<feature>.md`. An
execution request names the file and stage. A stage is complete when its stated verification
command passes; its out-of-scope list is binding.

<!-- ===== SHARED AGENT CORE — end ===== -->

## Replication contract

`papers/` reproduces the tables and figures of Sepp and Lucic (2026). CI additionally
runs `verify_arfima_variance_scale.py` as a standalone verification job. Any change to
analytics, processes, or system implementations requires re-running the replication
scripts and confirming the published values are unchanged. Report a mismatch; do not
update the paper values to match new output.

## Release checklist

A release touches three version locations. All three must agree, and
`tests/test_version_metadata.py` fails when they do not:

1. `version` in `pyproject.toml`
2. `version` and `date-released` in `CITATION.cff`
3. the `@software` BibTeX entry in `README.md`

For an authorized publication: commit, tag that exact main-reachable commit as
`v<version>`, then build, verify and publish its artifacts. Frequent PyPI updates are
supported. A GitHub Release page is optional and created only when requested; it is not
required for a local build, pip installation or routine package publication. Development
versions on main may be ahead of PyPI. Do not publish or bump a version for unrelated work.
