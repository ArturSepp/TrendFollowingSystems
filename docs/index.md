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
{doc}`quickstart <quickstart>`.

### Run a reference workflow

Use the three maintained, root-level scripts described in
{doc}`example workflows <workflows>` to analyze spans, predict Sharpe from an
autocorrelation function, or backtest the European system on packaged futures data.

### Reproduce the research

Start from the {doc}`paper and replication map <paper>` for the paper, executable
replication modules, data boundaries, and citation instructions.

## Project links

| Resource | Destination |
|---|---|
| Quickstart | {doc}`Install and make the first calculation <quickstart>` |
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
workflows
api
paper
```
