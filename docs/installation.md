---
myst:
  html_meta:
    description: >-
      Install trendfollowing from PyPI: supported Python versions, runtime dependencies including
      qis, the packaged futures dataset, the documentation extra, a development checkout with the
      test and lint groups, and a one-line check of the installation.
---

# Installation

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Install [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems) from PyPI.
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

The package installs with one command, includes the 84-contract futures dataset of the paper, and
needs no network access, data licence or credentials after installation. The analytical layer and
the Monte Carlo verification need no data at all.

## Install from PyPI

```console
python -m pip install trendfollowing
```

The distribution and import names are both `trendfollowing`. Supported Python versions are 3.10
and newer; continuous integration runs Linux on Python 3.10 to 3.14 and Windows and macOS on 3.12.

| Dependency | Minimum version | Used for |
|---|---|---|
| numpy | 2.0 | arrays and closed forms |
| pandas | 2.2.0 | time series and the dataset |
| scipy | 1.11 | special functions, filters and the test statistics |
| numba | 0.59 | compiled path simulation and system state machines |
| matplotlib | 3.8 | figures of the examples and the replication |
| statsmodels | 0.14.2 | statistical utilities |
| [qis](https://github.com/ArturSepp/QuantInvestStrats) | 5.0.9 | EWMA recursions, returns, portfolio analytics and reporting |

`trendfollowing` delegates performance statistics, factsheets and plotting to qis and does not
reimplement them; cite [qis](https://github.com/ArturSepp/QuantInvestStrats/blob/main/CITATION.cff)
as well when a result uses its analytics.

## Check the installation

```console
python -c "import trendfollowing as tf; print(tf.__version__, tf.sharpe_ar1(phi=0.05, long_span=63))"
```

The command prints the installed version and the closed-form Sharpe ratio of a 63-day filter on
an AR(1) with $\phi=0.05$, approximately 0.200195. The [quickstart](quickstart.md) runs the same
calculation with explicit conventions.

## The packaged dataset

The wheel installs the futures dataset under `trendfollowing/resources/futures`: daily prices and
USD returns of 84 contracts from July 1959 to July 2026, the 60/40 and SG Trend benchmarks, the
volume-based cost schedule and the instrument metadata. Load it with
`trendfollowing.universe.load_data()`; set the environment variable `TF_RESOURCE_PATH` to a folder
with the same `tf_system_data_*.csv` files to use another panel. The
[universe chapter](futures_universe_and_costs.md) documents the files.

## Documentation toolchain

The `docs` extra installs Sphinx, Furo, MyST and the sitemap extension used to build this site:

```console
python -m pip install "trendfollowing[docs]"
```

## Development checkout

The root examples, the tests and the paper replication live in the source repository and are not
installed with the wheel:

```console
git clone https://github.com/ArturSepp/TrendFollowingSystems.git
cd TrendFollowingSystems
uv sync --locked --group test --group lint
uv run --no-sync pytest
```

The repository's [AGENTS.md](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/AGENTS.md)
and [CONTRIBUTING.md](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CONTRIBUTING.md)
state the build, lint and documentation commands and the constraints on numerical changes. The
package is licensed under GPL-3.0-or-later, unlike most of the stack, which is MIT; review the
copyleft obligations before distributing an extension.

## See also

- [Quickstart](quickstart.md)
- [Example workflows](workflows.md)
- [Notation and conventions](notation_and_conventions.md)
- [API reference](api.md)
