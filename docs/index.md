# trendfollowing

`trendfollowing` provides closed-form trend-following analytics, reference system
implementations, and reproducible futures evidence in Python for quantitative researchers
and practitioners.

It is a research and replication library—not a broker integration or general-purpose
execution engine. Portfolio analytics and reporting are delegated to
[`qis`](https://github.com/ArturSepp/QuantInvestStrats).

## Choose your task

### Evaluate a trend signal analytically

Install the package and calculate a closed-form Sharpe ratio in the
{doc}`quickstart <quickstart>`, then compare process assumptions, output units, exact results,
and span costs in the {doc}`closed-form analytics guide <closed_form_analytics>`.

### Run a reference workflow

Use the three maintained, root-level scripts described in
{doc}`example workflows <workflows>` to analyze spans, predict Sharpe from an
autocorrelation function, or backtest the European system on packaged futures data.

### Explain realized Sharpe from sample moments

Use the {doc}`Sharpe prediction and attribution guide <predict_sharpe_from_acf>` to separate
point-in-time research from the in-sample replication workflow and to audit data coverage,
volatility normalization, lag construction, and estimation risk.

### Compare and backtest the reference systems

Use the {doc}`three-system comparison and backtest guide <system_comparison_and_backtest>` to
choose among European, American, and TSMOM rules and to make their inputs, exposure units, costs,
volatility targets, warmups, timing, and reusable-versus-paper workflows explicit.

### Choose the right research or backtesting tool

Use the dated, source-backed
{doc}`package choice guide <choosing_a_backtesting_tool>` to compare `trendfollowing` with
pysystemtrade, vectorbt, and Backtesting.py by workflow, analytical scope, data, production
integration, audience, and license implications.

### Reproduce the research

Start from the {doc}`paper and replication map <paper>` for the paper, executable
replication modules, data boundaries, and citation instructions.

## Project links

| Resource | Destination |
|---|---|
| Quickstart | {doc}`Install and make the first calculation <quickstart>` |
| Closed-form analytics | {doc}`Compare processes and select a filter span <closed_form_analytics>` |
| Predict Sharpe | {doc}`Attribute realized Sharpe to sample ACF and drift <predict_sharpe_from_acf>` |
| Compare systems | {doc}`Choose and backtest European, American, or TSMOM <system_comparison_and_backtest>` |
| Choose a tool | {doc}`Compare specialized research and broader backtesting workflows <choosing_a_backtesting_tool>` |
| Workflows | {doc}`Run the maintained examples <workflows>` |
| API | {doc}`Find the public modules and symbols <api>` |
| Paper and replication | {doc}`Connect the package to the research evidence <paper>` |
| Changelog | [Release history](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CHANGELOG.md) |
| Source | [GitHub repository](https://github.com/ArturSepp/TrendFollowingSystems) |
| Issues | [Issue tracker](https://github.com/ArturSepp/TrendFollowingSystems/issues) |
| Citation | [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff) |
| Package | [trendfollowing on PyPI](https://pypi.org/project/trendfollowing/) |
| Analytics dependency | [qis](https://github.com/ArturSepp/QuantInvestStrats) |

```{toctree}
:maxdepth: 2
:hidden:

quickstart
closed_form_analytics
predict_sharpe_from_acf
system_comparison_and_backtest
choosing_a_backtesting_tool
workflows
api
paper
```
