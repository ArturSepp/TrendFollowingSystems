# Changelog

All notable changes to trendfollowing are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.4] - 2026-07-28

**Portfolio-level volatility targeting in the European system produced undefined
leverage on days of non-positive portfolio variance, and this release is the first
to carry the fix.** `np.reciprocal(..., where=portfolio_var > 0.0)` was called
without `out=`, so the cells the mask skips were left holding whatever the freshly
allocated buffer contained rather than zero. `run_european_tf_system` with
`portfolio_covar_span` set could therefore apply arbitrary leverage on those days,
and the value was not reproducible between runs. The fix (`4b6e39a`, 2026-07-22)
allocates a zero array and passes it as `out=`, so a non-positive-variance day
gets zero leverage. Any European-system result produced with `portfolio_covar_span`
set on a version at or below 1.0.3 should be regenerated.

`trendfollowing/systems/american.py` and `trendfollowing/systems/tsmom.py` still
call `np.reciprocal` the same way. Those two lines are unchanged in this release
and are the open item behind it.

1.0.3 was published without a changelog entry; it was a version bump in
`pyproject.toml` and nothing else (`ff28a8a`).

### Added

- `tests/test_version_metadata.py`: `pyproject.toml`, `CITATION.cff` and the
  `@software` BibTeX entry in `README.md` must carry the same version, and
  `date-released` must be an ISO date. The three had drifted — see below.
- A version-carrying `@software` BibTeX entry in `README.md`. The README cited the
  paper and nothing else, so a replication had no way to record which version of
  the code it ran; for a replication package that is the citation that matters.

### Fixed

- `CITATION.cff` said 1.0.0 against a published 1.0.3, so anyone citing the package
  from that file named a release three patches behind the code that produced the
  paper's tables. It now says 1.0.4 with a current `date-released`, and the new test
  fails if it drifts again.

### Changed

- `numpy` floor raised to `>=2.0`, matching the rest of the stack. No resolution
  changes: `qis` already requires it, so every install has resolved numpy 2.x
  regardless of what this file declared.
- ruff no longer selects `I`. Import order here groups the scientific stack before
  the project packages, which isort's ordering contradicts; the rule was selected in
  this repository and in no other of the stack.
- `AGENTS.md` records the top-level `tests/` layout as a deliberate
  replication-package deviation rather than a drift from the in-package convention
  the siblings use.

### Removed

- `.coverage` and `example_ar1_knife_edge.png` are no longer tracked. Both are
  generated: the PNG is written into the working directory by
  `examples/analytic_sharpe_vs_span.py`, and nothing in the README or the papers
  tree references it. `.gitignore` now covers `.coverage*` and `example_*.png`.

## [1.0.2] - 2026-07-22

### Added

- `trendfollowing.local_path` and `trendfollowing/settings.yaml`: qis-style path
  resolution for all resource and output folders. Relative settings entries
  resolve against the repository root, and the environment overrides
  `TF_RESOURCE_PATH`, `TF_PAPERS_PATH` and `TF_OUTPUT_PATH` take precedence, so
  a source checkout runs with no configuration and a pip install points the
  settings at local data.
- `RESOURCE_RELOCATION_ROADMAP.md` mapping the old data locations to the new
  `resources/` layout.

### Changed

- Static resources moved out of the package to the repository root: futures
  prices and costs under `resources/futures/` (the minimal dataset for running
  the package), paper replication caches under `resources/papers/<paper>/`
  (not shipped with pip). The wheel ships code plus `settings.yaml` only, and
  `[tool.setuptools.package-data]` no longer packages CSV files.
- qis dependency raised to `qis >= 5.0.9`. Regime-conditional figures run
  through the native `qis.plot_regime_data` with
  `PerfParams(sharpe_convention=SharpeConvention.ARITHMETIC)`, the exactly
  additive decomposition that `trendfollowing.conventions` fixes, and the
  replication figures use the qis plot interfaces throughout
  (`plot_time_series` with regime shadows, `plot_bars`, `plot_scatter`,
  `plot_line`, `plot_stack`).

### Fixed

- A figure-output path in the replication tree pointed to a shadow folder
  instead of the folder the paper source includes, so regenerated figures did
  not reach the compiled manuscript.
- `PerfParams.copy()` in qis dropped `sharpe_convention` and silently reverted
  regime decompositions to the per-annum convention. Fixed upstream in
  qis 5.0.9, which this release requires.

## [1.0.1] - 2026-07-21

### Added
- `trendfollowing.conventions` — the single source for the return conventions
  both papers fix. Exports `AF_DAILY = 260` (the papers' trading-day
  annualisation, passed explicitly in place of the 252 that `qis` infers from
  the calendar density of the futures panel), `PPY_QUARTERLY = 4`,
  `PPY_MONTHLY = 12` and `compute_daily_annualised_vol`. Sharpe ratios are
  arithmetic throughout — `sqrt(a) * mean / std` of periodic simple excess
  returns — because the JOIM paper's regime decomposition (Proposition 1) is
  exact only under arithmetic means, and the SIFIN paper's analytic Sharpe
  ratios use the same convention. All four symbols are re-exported from the
  package top level.

### Changed
- Replication scripts (`aggregated_skewness_fig.py`, `sg_sharpe_test.py`,
  `verify_skewness_directions.py`) take their annualisation and Sharpe
  convention from `trendfollowing.conventions` instead of restating it locally.
- Daily futures data are stored as prices built from log returns; returns are
  extracted with `qis.to_returns` with the `is_log_returns` flag stated at the
  call, and periodic returns for regime sampling are arithmetic simple returns
  at calendar anchors.

### Fixed
- Typos in the SIFIN paper source.

### Removed
- A stray `sg.log` and a generated `.thm` file tracked in the repository.

## [1.0.0] - 2026-07-20

Initial public release: the replication package for *The Science and Practice
of Trend-Following Systems*.

### Added
- `trendfollowing` package (`backtests`, `universe`, `systems.tsmom`) and the
  `papers/tf_systems` replication tree with paper source and figures.
- CI workflow running the test suite, with the repository root on `sys.path` so
  tests can import the `papers.*` modules.
- Contribution guidelines, an issue template, and `AGENTS.md`.
- README with PyPI badges, paper figures, an ecosystem overview, and a pointer
  to the SSRN working paper.

### Fixed
- Canonical GPL-3.0 licence text, so GitHub detects the licence.
- README math rendering.

---

The documentation and infrastructure entries above landed after 1.0.0 was
published to PyPI and are not separately versioned; they ship in 1.0.1.
