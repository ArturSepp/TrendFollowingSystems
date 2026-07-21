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
tests/         8 test modules (top-level, test_*.py)
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

- Test files are named `test_*.py` and live in the top-level `tests/` directory.
- Line length 100 (`ruff`, rules `E`, `F`, `W`, `I`).
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

## Replication contract

`papers/` reproduces the tables and figures of Sepp and Lucic (2026). CI additionally
runs `verify_arfima_variance_scale.py` as a standalone verification job. Any change to
analytics, processes, or system implementations requires re-running the replication
scripts and confirming the published values are unchanged. Report a mismatch; do not
update the paper values to match new output.

## Release checklist

A release touches three version locations. All three must agree:

1. `version` in `pyproject.toml`
2. `version` and `date-released` in `CITATION.cff`
3. the software BibTeX entry in `README.md` (if it pins a version)

Then: commit, tag `v<version>`, build and publish to PyPI, and cut a GitHub Release
with the same tag. Do not bump versions as part of an unrelated change, and do not
publish without the maintainer explicitly asking for a release.
