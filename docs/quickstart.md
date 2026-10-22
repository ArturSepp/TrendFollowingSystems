---
myst:
  html_meta:
    description: >-
      Install trendfollowing and compute two deterministic closed-form Sharpe ratios offline,
      AR(1) and ARFIMA, with the 260-day, zero-drift, single-filter conventions stated.
---

# Quickstart

*Author: [Artur Sepp](https://github.com/ArturSepp) / First recorded: [2026-08-16](https://github.com/ArturSepp/TrendFollowingSystems/commit/1bceb64e2e10fa0014d10f4fbb69c84ece61f667)*

The first calculation with [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

## Reproducible released workflow

The tested support floor for this first-use workflow is **trendfollowing 1.3.1** on
Python 3.12. This is a verified floor, not the historical introduction version. Install core
without extras; save and run the existing package-owned script in a working directory outside
synchronized folders:

```powershell
python -m pip install "trendfollowing==1.3.1"
python -c "from importlib.metadata import version; import trendfollowing as p; print(version('trendfollowing')); print(p.__file__)"
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/ArturSepp/TrendFollowingSystems/b1d75d974dc1f08c63fd9763f84147779090e3bc/examples/quickstart.py' -OutFile quickstart.py
python quickstart.py
```

Installation and saving the script need internet access; the calculation below runs offline.
Measure installation separately from execution, and allow any first Numba compilation to finish.
No universal time-to-first-result is promised.

This CPU calculation returns two deterministic closed-form Sharpe ratios, not an empirical backtest or investment forecast. It needs no data, credentials or optional extras and writes no files. `qis` is a core dependency for analytics/reporting; the packaged futures resources are not part of this first-use path. The fixed convention is 260 trading days per year, zero underlying drift and a 63-day EWMA filter.

[Stable documentation](https://trendfollowingsystems.readthedocs.io/en/stable/) is the release channel;
[latest](https://trendfollowingsystems.readthedocs.io/en/latest/) follows main and may include unreleased changes. Check the build's
source version; a stable alias is not proof of the latest PyPI upload. Existing figures,
results and conventions below remain the canonical example's contract.

Install the released package from PyPI:

```console
pip install trendfollowing
```

Then run the authoritative offline example from a checkout or downloaded source tree:

```console
python examples/quickstart.py
```

The documentation includes that root script directly, so the runnable source and this page
cannot silently drift:

```{literalinclude} ../examples/quickstart.py
:language: python
:caption: examples/quickstart.py
```

The first line reports the installed package version. With the script's fixed parameters, the
AR(1) annualized Sharpe is `0.200195` and the ARFIMA(0,d,0) annualized Sharpe is `0.288820`.
Both are deterministic closed forms: they require no network or dataset, write no files, and
open no GUI. The stated convention is 260 trading days per year, zero underlying drift, and a
single 63-day EWMA filter. Change `PHI`, `D`, or `LONG_SPAN` first when exploring assumptions.

Version 1.4.0 requires Python 3.11 or newer and patched Pillow 13.0.0 or newer; the pinned
1.3.1 example above retains its original requirements. The package depends on `qis` for portfolio
analytics and reporting. Continue with the {doc}`maintained example workflows <workflows>` for
span selection, ACF prediction, and the packaged-universe backtest.

The two numbers are the closed-form Sharpe ratio of the
[closed-form Sharpe ratio chapter](sharpe_ratio_closed_form.md), evaluated under the AR(1) and
ARFIMA processes of [Sharpe ratios under white noise, AR(1) and ARFIMA](sharpe_under_processes.md);
[Notation and conventions](notation_and_conventions.md) defines the 260-day annualisation and the
Sharpe convention they use.
