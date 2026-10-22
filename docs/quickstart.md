---
myst:
  html_meta:
    description: >-
      Install trendfollowing 1.4.0 on Python 3.11 and compute two closed-form Sharpe ratios offline,
      AR(1) and ARFIMA, with the 260-day, zero-drift, single-filter conventions stated.
---

# Quickstart

*Author: [Artur Sepp](https://github.com/ArturSepp) / First recorded: [2026-08-16](https://github.com/ArturSepp/TrendFollowingSystems/commit/1bceb64e2e10fa0014d10f4fbb69c84ece61f667)*

The first calculation with [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

## Reproducible released workflow

The verified released setup for this first-use workflow is **trendfollowing 1.4.0** on
**Python 3.11**. A clean PyPI installation on Windows with Python 3.11.16 installed patched
Pillow 13.0.0 and passed the quickstart on 2026-10-22. Select a Python 3.11 interpreter as
`python`, install core without extras, and save and run the package-owned script in a working
directory outside synchronized folders:

```powershell
python --version
python -m pip install "trendfollowing==1.4.0"
python -c "from importlib.metadata import version; import trendfollowing as p; print(version('trendfollowing')); print('Pillow', version('Pillow')); print(p.__file__)"
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/ArturSepp/TrendFollowingSystems/2248d9bf866c3b2067c2e4ad1ef9cf7121d80fc5/examples/quickstart.py' -OutFile quickstart.py
python quickstart.py
```

Installation and saving the script need internet access; the calculation below runs offline.
Measure installation separately from execution, and allow any first Numba compilation to finish.
No universal time-to-first-result is promised.

The checks should report Python 3.11, trendfollowing 1.4.0 and Pillow 13.0.0 or newer. The import
path should point to the installed package in the selected environment's `site-packages`.

This CPU calculation returns two deterministic closed-form Sharpe ratios, not an empirical backtest or investment forecast. It needs no data, credentials or optional extras and writes no files. `qis` is a core dependency for analytics/reporting; the packaged futures resources are not part of this first-use path. The fixed convention is 260 trading days per year, zero underlying drift and a 63-day EWMA filter.

[Stable documentation](https://trendfollowingsystems.readthedocs.io/en/stable/) follows the
maintained `stable` branch: TFS 1.4.0 with documentation corrections. The
[latest channel](https://trendfollowingsystems.readthedocs.io/en/latest/) follows `main` and may
include unreleased changes. Check the build's source version and the installed package version.
Existing figures, results and conventions below remain the canonical example's contract.

Install the released package from PyPI:

```console
python -m pip install "trendfollowing==1.4.0"
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

Version 1.4.0 requires Python 3.11 or newer and patched Pillow 13.0.0 or newer.
The package depends on `qis` for portfolio analytics and reporting. Continue with the
{doc}`maintained example workflows <workflows>` for
span selection, ACF prediction, and the packaged-universe backtest.

The two numbers are the closed-form Sharpe ratio of the
[closed-form Sharpe ratio chapter](sharpe_ratio_closed_form.md), evaluated under the AR(1) and
ARFIMA processes of [Sharpe ratios under white noise, AR(1) and ARFIMA](sharpe_under_processes.md);
[Notation and conventions](notation_and_conventions.md) defines the 260-day annualisation and the
Sharpe convention they use.
