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

The package supports Python 3.10 and newer and depends on `qis` for portfolio analytics and
reporting. Continue with the {doc}`maintained example workflows <workflows>` for span selection,
ACF prediction, and the packaged-universe backtest.

The two numbers are the closed-form Sharpe ratio of the
[closed-form Sharpe ratio chapter](sharpe_ratio_closed_form.md), evaluated under the AR(1) and
ARFIMA processes of [Sharpe ratios under white noise, AR(1) and ARFIMA](sharpe_under_processes.md);
[Notation and conventions](notation_and_conventions.md) defines the 260-day annualisation and the
Sharpe convention they use.
