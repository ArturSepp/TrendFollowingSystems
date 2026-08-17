# Choosing a trend-following or backtesting tool

**Version snapshot: 2026-08-17.** This guide compares workflows and public capabilities, not
popularity. **No universal winner** exists: the appropriate tool depends on whether the job is
analytical trend-following research, a production futures stack, broad parameter exploration, or
a compact single-asset strategy test.

The comparison covers the open-source or community offering named in each project's official
sources. It does not benchmark speed or returns, install the alternatives, assess paid editions,
or provide legal advice.

## Overlap and different design goals

All four projects can participate in strategy research, but they start from different questions:

- `trendfollowing` asks how return predictability, drift, a trend filter, and costs determine
  closed-form moments, then connects those results to three maintained reference systems and a
  scientific replication workflow. See the {doc}`closed-form guide <closed_form_analytics>`,
  {doc}`three-system guide <system_comparison_and_backtest>`, and
  {doc}`paper map <paper>`.
- [pysystemtrade][pst-repo] is a broader systematic-futures backtesting and production stack built
  around Rob Carver's framework. Its official sources document both a backtesting environment and
  automated Interactive Brokers futures trading.
- [vectorbt][vbt-repo] is a matrix-oriented research engine for multi-asset analysis and large
  parameter sweeps, with portfolio backtesting, data access, robustness tooling, and interactive
  analysis.
- [Backtesting.py][bt-repo] is a compact bar-by-bar strategy framework. Its
  [official quickstart][bt-quickstart] describes user-supplied OHLC data and focuses on entry/exit
  rules for one tradeable asset at a time.

These are design differences, not quality rankings. A specialized analytical package can answer
a question that a general engine leaves to the user; a broader engine can support operational or
strategy types that `trendfollowing` intentionally does not implement.

## Capability matrix

“Not identified” means that the capability was not found in the official sources audited for this
page. It is not proof that no extension, user code, branch, or paid product can provide it.

| Capability | `trendfollowing` 1.0.5 | pysystemtrade 1.8.2 | vectorbt 1.1.0 | Backtesting.py 0.6.6 |
|---|---|---|---|---|
| Primary design and audience | Research and replication library for closed-form trend-following analysis and maintained futures reference systems; not a broker or general execution engine. | Systematic-futures backtesting plus a production system for technically experienced users; the [repository][pst-repo] documents its scope and support expectations. | Matrix-oriented general strategy research for multi-asset and large parameter sweeps; see the [official feature list][vbt-repo]. | Compact, bar-by-bar entry/exit strategy testing and optimization for an individual tradeable asset; see the [official quickstart][bt-quickstart]. |
| Closed-form trend-following moments | Expected return, volatility, Sharpe ratio, skewness, and turnover are package workflows; see {doc}`closed-form analytics <closed_form_analytics>`. | **Not identified** as a documented project capability in the [repository][pst-repo] or [backtesting guide][pst-backtesting]. | **Not identified** in the audited [community feature set][vbt-repo]. | **Not identified** in the audited [API][bt-api] and [quickstart][bt-quickstart]. |
| Process models and analytical span/cost study | White noise, AR(1), ARFIMA, and empirical ACF inputs, including span and trading-cost interpretation. | **Not identified** as the same closed-form process/span workflow in the audited [backtesting guide][pst-backtesting]. | **Not identified** as the same closed-form process/span workflow in the audited [official repository][vbt-repo]. | **Not identified** as the same closed-form process/span workflow in the audited [official documentation][bt-api]. |
| European, American, and TSMOM references | Maintains all three with explicit units, costs, warmups, and timing; see the {doc}`system comparison <system_comparison_and_backtest>`. | The [repository][pst-repo] documents systems from Rob Carver's framework; exact equivalence to this package's named trio was **not identified**. | General signal and portfolio construction are documented, but exact implementations of this named trio were **not identified** in the [community sources][vbt-repo]. | User-defined `Strategy` rules are documented, but exact implementations of this named trio were **not identified** in the [official examples][bt-quickstart]. |
| Futures or other market data | Bundles an immutable 84-contract futures panel for replication and accepts `TF_RESOURCE_PATH` for an external panel; see {doc}`data boundaries <system_comparison_and_backtest>`. | The official [data guide][pst-data] covers supplied backtest data and configurable CSV, Parquet, MongoDB, and Interactive Brokers flows; it also warns that the shipped multiple/adjusted CSVs have not been updated since March 2024. | The [official feature list][vbt-repo] documents built-in data access, preprocessing, synthetic data generation, and multi-asset inputs. | Users bring OHLC data in a pandas `DataFrame`; small example data are demonstrated in the [quickstart][bt-quickstart]. |
| Monte Carlo and scientific replication | Paper modules cover Monte Carlo and empirical replication, with a map from claims to code and data in {doc}`paper and replication <paper>`. | Book-framework backtesting is documented, but a domain-specific Monte Carlo replication contract equivalent to this project's was **not identified** in the audited [official sources][pst-repo]. | General random-strategy and robustness workflows are documented; a domain-specific replication contract equivalent to this project's was **not identified** in the [community feature set][vbt-repo]. | Parameter optimization is documented in the [quickstart][bt-quickstart], but a domain-specific Monte Carlo replication contract equivalent to this project's was **not identified**. |
| General strategy-engine scope | Deliberately narrow: three reference systems and analytical research workflows, with analytics/reporting delegated to `qis`. | Broader systematic-futures research and production lifecycle, documented in the [backtesting][pst-backtesting] and [production][pst-production] guides. | Broad signal, portfolio, multi-asset, indicator, optimization, and interactive-analysis scope in the [official repository][vbt-repo]. | General user-defined bar-by-bar rules for one asset; the [quickstart][bt-quickstart] explicitly says multi-asset portfolio rebalancing is not its focus. |
| Execution or broker integration | None; this boundary is intentional. | Automated futures trading through Interactive Brokers is documented in the [repository][pst-repo], [IB guide][pst-ib], and [production guide][pst-production]. | Broker execution was **not identified** in the audited open-source [repository][vbt-repo]; documented scheduling and notifications are not treated here as broker connectivity. | Broker execution was **not identified** in the audited [website/API][bt-api] or [repository][bt-repo]. |
| License and extension implications | [GPL-3.0-or-later][tf-license]. Review copyleft obligations before distributing an extension. | [GPL-3.0][pst-license]. Review copyleft obligations before distributing an extension. | [Apache 2.0 with Commons Clause][vbt-license], described upstream as fair-code; the official terms restrict selling products or services primarily comprising the software and warn that optional dependencies may differ. | [AGPL-3.0][bt-license]. Review its strong-copyleft terms before distributing a modification or providing a modified network service. |

License summaries are selection prompts, not legal conclusions. Read the linked license text and
obtain appropriate advice for a commercial, redistributed, or hosted product.

## Workflow-based decision guide

| If the immediate job is... | Start with... | Why this tool is favored for that job | Main boundary to check |
|---|---|---|---|
| Derive or reproduce trend-following moments from white-noise, AR(1), ARFIMA, or empirical-ACF assumptions; study span and cost analytically | `trendfollowing` | Those formulas, conventions, and scientific checks are its specialized public workflow. | It is not a general execution or broker stack. |
| Research and operate a systematic-futures portfolio, including an Interactive Brokers production path | [pysystemtrade][pst-repo] | Its official scope spans futures backtesting, data management, production processes, and IB integration. | Latest tagged release is older than the current development documentation, installation is from Git rather than PyPI, and its framework is not a drop-in equivalent of this package's research conventions. |
| Explore many signal configurations or assets through array-oriented portfolio backtests and interactive analysis | [vectorbt][vbt-repo] | Broadcasting, accelerated matrix operations, portfolio simulation, and parameter sweeps are first-class documented goals. | Validate path-dependent execution semantics and review the Commons Clause before commercial embedding or resale. |
| Prototype and optimize a clear OHLC entry/exit rule for one tradeable asset | [Backtesting.py][bt-quickstart] | Its concise `Strategy`/`Backtest` workflow, optimizer, plots, and statistics target that use case directly. | Multi-asset portfolio rebalancing is explicitly outside its main fit; review AGPL obligations. |

If a research program uses more than one tool, validate signal lag, fill timing, return convention,
volatility scaling, costs, warmup, and missing-data handling at the boundary. This page establishes
no interoperability guarantee and no equality of results across engines.

## Where `trendfollowing` is specialized

`trendfollowing` is the clearest fit when the research question itself is specific to the science
and practice implemented here:

- mapping autocorrelation and drift assumptions to closed-form trend-following moments;
- comparing white-noise, AR(1), ARFIMA, and empirical-ACF inputs under explicit annualization and
  cost conventions;
- studying filter span analytically rather than only evaluating a grid of realized backtests;
- comparing the maintained European, American, and TSMOM reference implementations; and
- reproducing the package's Monte Carlo and 84-contract futures evidence from a documented paper
  map.

This specialization is a deliberate boundary. It avoids presenting the package as a broker,
order-management system, or universal strategy engine, and it delegates shared portfolio
analytics and reporting to [`qis`](https://github.com/ArturSepp/QuantInvestStrats).

## Where broader tools are a better fit

- Choose [pysystemtrade][pst-repo] when the primary requirement is an end-to-end systematic-futures
  research and production architecture, especially its documented Interactive Brokers route.
- Choose [vectorbt][vbt-repo] when the central problem is broad multi-asset parameter exploration,
  reusable user-defined signals, portfolio simulation, or interactive analysis at matrix scale.
- Choose [Backtesting.py][bt-quickstart] when the desired abstraction is a small, readable,
  bar-by-bar strategy over user-supplied OHLC data with built-in optimization and visualization.

Those use cases are not shortcomings in `trendfollowing`; they are outside its documented role.
Likewise, a general engine does not automatically provide this package's closed-form results,
named reference-system conventions, or scientific replication evidence.

## Methodology, versions, sources, and limitations

The audit was performed on **2026-08-17** using only official project repositories,
documentation, release records, package-index records, and license files. Alternatives were not
installed, and no speed, return, or accuracy benchmark was run. Popularity metrics were excluded
from selection and recommendation.

| Project | Version basis used here | Activity/source interpretation |
|---|---|---|
| `trendfollowing` | [1.0.5 on PyPI][tf-pypi], released 2026-08-01 | This documentation and the repository's tagged package metadata define the compared public contract. |
| pysystemtrade | [1.8.2 tagged release][pst-release], published 2024-11-06 | 1.8.2 is the latest official tagged release found. The project is not on PyPI; current capability links use the active official `develop` repository and documentation. The [repository history note][pst-repo] records the January 2026 move to `pst-group`. |
| vectorbt | [1.1.0 on PyPI][vbt-pypi], released 2026-07-05 | The official community repository and its 1.1.0 package/release records define the compared scope; VectorBT PRO is not assessed. |
| Backtesting.py | [0.6.6 on PyPI][bt-pypi], released 2026-07-22 | PyPI is the stable-version record used because the official [GitHub releases page][bt-releases] has no latest release object; current official docs and the repository define capabilities. |

Limits of this comparison:

- “Not identified” is an audit result, not a universal negative claim.
- Feature depth, extension ecosystems, paid products, unpublished branches, and user-built adapters
  were not evaluated.
- Documentation can change after the audit date; recheck versions, licenses, and broker support
  before committing to an architecture.
- A capability name does not establish matching financial semantics. Cross-engine results require
  independent convention and timing checks.
- The page does not recommend combining packages unless the integration is separately designed and
  verified.

[tf-pypi]: https://pypi.org/project/trendfollowing/
[tf-license]: https://github.com/ArturSepp/TrendFollowingSystems/blob/main/LICENSE
[pst-repo]: https://github.com/pst-group/pysystemtrade
[pst-release]: https://github.com/pst-group/pysystemtrade/releases/tag/1.8.2
[pst-backtesting]: https://github.com/pst-group/pysystemtrade/blob/develop/docs/backtesting.md
[pst-data]: https://github.com/pst-group/pysystemtrade/blob/develop/docs/data.md
[pst-ib]: https://github.com/pst-group/pysystemtrade/blob/develop/docs/IB.md
[pst-production]: https://github.com/pst-group/pysystemtrade/blob/develop/docs/production.md
[pst-license]: https://github.com/pst-group/pysystemtrade/blob/develop/LICENSE
[vbt-repo]: https://github.com/polakowo/vectorbt
[vbt-pypi]: https://pypi.org/project/vectorbt/
[vbt-license]: https://github.com/polakowo/vectorbt/blob/master/LICENSE.md
[bt-repo]: https://github.com/kernc/backtesting.py
[bt-releases]: https://github.com/kernc/backtesting.py/releases
[bt-pypi]: https://pypi.org/project/backtesting/
[bt-api]: https://kernc.github.io/backtesting.py/doc/backtesting/
[bt-quickstart]: https://kernc.github.io/backtesting.py/doc/examples/Quick%20Start%20User%20Guide.html
[bt-license]: https://github.com/kernc/backtesting.py/blob/master/LICENSE.md
