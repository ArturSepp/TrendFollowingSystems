# AGENTS.md

Guidance for AI coding agents working in the **TrendFollowingSystems** repository.

## Project overview

`trendfollowing` implements closed-form analytics for trend-following systems —
expected return, Sharpe ratio, skewness, and turnover under white noise, AR(1), and
ARFIMA processes — together with three complete system implementations (European,
American, and time-series momentum), Monte Carlo verification, and backtests on an
84-contract futures dataset spanning 1959-2026.

It is the replication package for *The Science and Practice of Trend-Following Systems*
(Sepp and Lucic, 2026). Distribution and import name `trendfollowing`. Licensed
**GPL-3.0** (`LICENSE`) — unlike most of the stack, which is MIT. Depends on `qis` for
analytics and reporting.

## Ecosystem position

This package is one of eight open-source Python libraries maintained at
[github.com/ArturSepp](https://github.com/ArturSepp). Before implementing anything
non-trivial, check whether it already exists in one of these:

| Package | Repository | Purpose |
|---|---|---|
| `qis` | QuantInvestStrats | Performance analytics, factsheets, visualisation |
| `optimalportfolios` | OptimalPortfolios | Portfolio construction and backtesting |
| `factorlasso` | factorlasso | Sparse factor models and factor covariance estimation |
| `bbg-fetch` | BloombergFetch | Bloomberg data fetching |
| `trendfollowing` | TrendFollowingSystems | Trend-following systems: closed-form theory and replication |
| `goal-based-allocation` | GoalBasedAllocation | Dynamic MV allocation under regime-switching jump-diffusions |
| `stochvolmodels` | StochVolModels | Stochastic volatility pricing analytics |
| `vanilla-option-pricers` | VanillaOptionPricers | Vanilla option pricers and implied volatility fitters |

Actual package dependencies within the stack: `optimalportfolios` depends on `qis`
and `factorlasso`; `trendfollowing` depends on `qis`; `stochvolmodels` has an
optional `research` extra that pulls in `qis`. The others are independent.

Do not vendor or copy code between these packages. If functionality belongs in a
sibling package, say so rather than reimplementing it here.

## Repository layout

```
trendfollowing/
  analytics/   closed-form formulas for system moments
  processes/   price process models (white noise, AR(1), ARFIMA)
  systems/     European, American and TSMOM system implementations
  analysis/    analysis helpers
  resources/   packaged data
  backtests.py, universe.py
papers/        replication code for the paper (importable: papers.*)
tests/         7 test modules (top-level, test_*.py)
examples/      runnable examples
```

## Commands

```bash
pip install -e ".[dev]"
pytest tests/ -q                 # as CI runs it
pytest tests/test_sharpe.py -v   # one module
ruff check trendfollowing/       # lint
```

`[tool.pytest.ini_options] pythonpath = ["."]` puts the repository root on `sys.path`
so tests can import the `papers.*` replication modules under a bare `pytest`
invocation. Supported Python is >= 3.10; CI runs 3.10 - 3.12 plus a separate
verification job.

## Conventions

- Test files are named `test_*.py` and live in the top-level `tests/` directory. This is a
  deliberate deviation from the in-package `<subpackage>/tests/` layout the rest of the
  stack uses: this is a replication package, and a reviewer who downloads it should find
  the tests without first learning the package structure. Do not "fix" it to match a
  sibling.
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
- Do not modify the packaged futures dataset in `trendfollowing/resources/` or the
  universe definitions: published backtests depend on them.
- Do not reimplement performance statistics or plotting — use `qis`.
- Do not commit backtest output, figures, or log files (`sg.log` in the repository root
  is an accident, not a pattern to follow).

<!-- ===== SHARED AGENT CORE (consumer variant) — begin =====
     Generated from SHARED_AGENT_CORE.md in the maintainer's project knowledge. Do not hand-edit
     between these markers — propose the change to the maintainer instead. Variants: builder
     (qis) / consumer / standalone. Last synced 2026-08-08, agent core v1.2. -->

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
resample, unsmooth, covariance, correlation, regime, factsheet, tracking error, risk
contribution.

- **The hard stop:** a `for` loop over dates accumulating a position, a weight or a P&L is
  `qis.backtest_model_portfolio`. The hand-rolled version gets drift adjustment wrong — `qis`
  holds *units* between rebalancings, not weights.
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

## Roadmap execution

Feature roadmaps live at the repository root as `ROADMAP_<feature>.md`. An execution request
names the file and the stage. A stage is complete when its stated verification command passes;
its out-of-scope list is binding.

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

Then: commit, tag `v<version>`, build and publish to PyPI, and cut a GitHub Release
with the same tag. Do not bump versions as part of an unrelated change, and do not
publish without the maintainer explicitly asking for a release.
