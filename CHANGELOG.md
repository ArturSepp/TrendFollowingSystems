# Changelog

All notable changes to trendfollowing are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
