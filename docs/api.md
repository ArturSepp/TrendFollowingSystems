# API map

The stable import name is `trendfollowing`. Common analytical functions are re-exported at
the package top level; specialized functionality is grouped into these modules:

| Module | Responsibility |
|---|---|
| `trendfollowing.analytics` | Closed-form moments, expected returns, turnover, Sharpe ratios, and autocorrelation helpers |
| `trendfollowing.processes` | White-noise, AR(1), and ARFIMA process utilities |
| `trendfollowing.systems` | European, American, and time-series-momentum reference systems |
| `trendfollowing.universe` | Load the immutable futures data bundled in the wheel |
| `trendfollowing.backtests` | Shared backtest-facing result and orchestration helpers |

The authoritative public re-export list is `src/trendfollowing/__init__.py` in the
[source repository](https://github.com/ArturSepp/TrendFollowingSystems). Use the
{doc}`quickstart <quickstart>` for a first top-level call and the {doc}`example workflows
<workflows>` for executable integrations.

Portfolio performance analytics, factsheets, and reporting belong to
[`qis`](https://github.com/ArturSepp/QuantInvestStrats), rather than a parallel API in this
package.
