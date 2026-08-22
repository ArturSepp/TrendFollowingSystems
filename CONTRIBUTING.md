# Contributing to TrendFollowingSystems

Thanks for your interest in `trendfollowing`. The package is the replication library for
*The Science and Practice of Trend-Following Systems*, so published results and the distinction
between reusable package workflows and paper replication constrain what can change.

## Scope

In scope:

- Bug fixes in closed-form analytics, process models, system implementations, or backtests
- Numerical robustness improvements with an independently computed regression test
- Compatibility work for supported Python, `numba`, and `qis` releases
- Documentation, deterministic examples, packaging, and terminal-free tests

Open an issue before writing code that changes analytical formulas, public signatures, dependency
floors, the packaged futures universe, or replication orchestration. Performance analytics and
reporting belong in `qis`; do not reimplement them here. Do not submit proprietary data, generated
figures, backtest output, or changes to published paper values.

## Reporting a bug

Use the bug-report template and include the `trendfollowing` version, Python version, operating
system, a minimal reproducer, and the full traceback or incorrect output. Prefer generated data.
If the problem concerns a paper result, name the exhibit and the replication command used.

## Development setup

```bash
git clone https://github.com/ArturSepp/TrendFollowingSystems.git
cd TrendFollowingSystems
uv sync --locked --group test
uv run --no-sync pytest
uv run --locked --only-group lint ruff check src/trendfollowing/
```

The default pytest configuration runs the top-level terminal-free suite and exposes the repository
root only for imports from the paper replication package. Development runners under `run_local/`
are excluded from distributions and must not become test modules or public imports.

Build the documentation with the same warning gates used in CI:

```bash
uv sync --locked --extra docs
uv run --no-sync python -m sphinx -E -W --keep-going -b html docs docs/_build/html
uv run --no-sync python -m sphinx -E -W -b linkcheck docs docs/_build/linkcheck
```

`--locked` intentionally fails when `pyproject.toml` and `uv.lock` disagree. Dependency groups are
contributor environments, not package extras: use `test` for pytest, `lint` for Ruff, and retain
the `docs` extra for Read the Docs.

## Pull requests

- Keep one focused topic per pull request.
- Add a regression test that fails before a behavioral fix and passes afterwards.
- Preserve look-ahead, return, annualisation, signal, and volatility-targeting conventions.
- Verify numerical changes independently; do not update expected values to fit changed output.
- Do not edit `papers/`, packaged futures resources, `TF_RESOURCE_PATH`, or universe definitions.
- Do not commit generated output, private data, local paths, or development environments.
- Run the relevant test, lint, documentation, and wheel checks before submitting.
- Do not bump package or citation versions; releases are handled separately.

## Replication

Changes to analytics, processes, or system implementations require the relevant independent
closed-form/Monte Carlo cross-check and replication verification. Report any mismatch rather than
changing the paper or its expected values.

## Conduct and licence

Be civil and assume good faith. By contributing, you agree that your contribution is licensed
under this project's GPL-3.0-or-later licence.
