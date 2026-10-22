# Contributing to TrendFollowingSystems

*Author: [Artur Sepp](https://github.com/ArturSepp) / First recorded: [2026-08-22](https://github.com/ArturSepp/TrendFollowingSystems/commit/f484c4924276814fe4219574976fca8c0a9e6299)*

Source: [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

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

## Starter tasks

These are bounded proposals, not assigned issues or confirmed defects. Recheck source and open
work before agreeing one task. Use the existing [feature form](https://github.com/ArturSepp/TrendFollowingSystems/issues/new?template=feature_request.yml),
Area **Documentation or deterministic example**. Include the task ID, owner, exact paths, reproduction, acceptance and focused
check under Proposed behavior; retain required boundary checkboxes. Use the bug form only for
observed incorrect behaviour. Keep numerical code, public signatures, dependencies, fixtures and
canonical examples unchanged for these documentation tasks.

### TF-1: clarify closed-form output

Owner: TrendFollowingSystems. Edit only `docs/quickstart.md` to resolve one observed output-reading ambiguity. Acceptance: identify both model Sharpe numbers and the 260-day/zero-drift convention without calling them realised investment results.

```console
python examples/quickstart.py
python -m pytest tests/test_examples.py -k quickstart -q
```

### TF-2: explain the offline data boundary

Owner: TrendFollowingSystems. Edit only `docs/workflows.md` to clarify which workflow uses generated inputs and which uses bundled futures resources. Acceptance: a reader can choose a data-free task without changing resource paths or frozen data.

```console
python -m pytest tests/test_packaged_resources.py -q
```

### TF-3: check release navigation

Owner: TrendFollowingSystems. Edit only `docs/quickstart.md` to clarify one released-versus-main boundary. Acceptance: keep the pinned canonical script and distinguish stable/main without changing paper values or packaging.

```console
python -m pytest tests/test_docs_foundation.py -q
```

Run the package's existing strict HTML command after a documentation edit and inspect the
changed passage. On the maintainer's OneDrive checkout, dot-source the shared
`Enter-AgentRepo.ps1` first and use `C:\Python\TrendFollowingSystems312\Scripts\python.exe`.
Keep exports, caches, builds and run output on C. The `uv` setup below is for ordinary contributor
checkouts outside OneDrive; never create `.venv` in the synchronized checkout.

Follow the [shared review guidance](https://github.com/ArturSepp/ArturSepp/blob/main/docs/contributing_to_stack.md#review-attribution-and-automation-assisted-changes).
Record the revision, actual versions, exact checks and skips, rendered review and material
automation assistance. Preserve MIT licensing and retained third-party attribution. Automated checks do not
establish independent reader success. Review time and acceptance are not promised.

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
under this project's MIT licence, preserving applicable third-party notices.
