---
myst:
  html_meta:
    description: >-
      Documentation for trendfollowing: the trendfollowing handbook of closed-form
      trend-following analytics (filters, normalisation, processes, the P&L identity, the
      closed-form Sharpe ratio, costs and skewness), the European, American and TSMOM reference
      systems, the futures evidence, guides, runnable examples and API reference.
---

# trendfollowing documentation

*Author: [Artur Sepp](https://github.com/ArturSepp) / First recorded: [2026-08-16](https://github.com/ArturSepp/TrendFollowingSystems/commit/1bceb64e2e10fa0014d10f4fbb69c84ece61f667)*

<a id="trendfollowing"></a>

[trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems) is a Python library of
closed-form trend-following analytics, reference system implementations and reproducible futures
evidence for quantitative researchers and practitioners. It computes the expected return, the gross
and net Sharpe ratio, the turnover and the skewness of trend-following systems from the
autocorrelation and drift of the returns they trade, and runs the European, American and
time-series-momentum systems on a packaged panel of 84 futures. It is the replication package of
*The Science and Practice of Trend-Following Systems* (Sepp and Lucic, 2026). It is a research and
replication library, not a broker integration or general-purpose execution engine; portfolio
analytics and reporting are delegated to [qis](https://github.com/ArturSepp/QuantInvestStrats).

Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

## Start here

1. [Install trendfollowing](installation.md). The core installation command is
   `python -m pip install trendfollowing`.
2. Run the offline [quickstart](quickstart.md): two closed-form Sharpe ratios in a few lines, with
   their conventions stated.
3. Keep [Notation and conventions](notation_and_conventions.md) at hand: the reserved symbols,
   the 260-day annualisation, the arithmetic Sharpe convention, timing and the two cost units are
   defined there once for every chapter.
4. Run the [example workflows](workflows.md): span selection, Sharpe prediction from an
   autocorrelation function, and a backtest of the European system on the packaged futures.

<a id="choose-your-task"></a>

## The system in one picture

The European system holds, in each contract, the variance-preserving EWMA signal of
volatility-normalised returns $z_t=r_t/\sigma_{t-1}$, scaled to a volatility target. Its daily
return and its expected annual return are

$$
f_t=\frac{\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}}S_{t-1}z_t,
\qquad
\bar F_{1y}=h_{1y}\sum_{m=1}^{\infty}\nu^m\rho(m)+\frac{l\sigma_{\mathrm{target}}}{\sqrt{\mathrm{af}}}\mu_{\mathrm{an}}^2 ,
$$

an autocorrelation channel and a squared-drift channel, and its Sharpe ratio is a closed-form
function of the autocorrelation function $\rho$, the drift $\mu_{\mathrm{an}}$, the excess kurtosis
of the innovations and the span alone. The handbook builds these results step by step and connects
them to the code and the data:

| Question | Chapters |
|---|---|
| How is the signal built and scaled? | [EWMA filters](ewma_filters.md), [volatility normalisation](volatility_normalisation.md) |
| Which return processes are analysed? | [Return-generating processes](return_processes.md) |
| Where does the P&L come from? | [The P&L decomposition](pnl_decomposition.md) |
| What is the Sharpe ratio, and how does the span change it? | [The closed-form Sharpe ratio](sharpe_ratio_closed_form.md), [Sharpe ratios under named processes](sharpe_under_processes.md) |
| What do costs do, and which span is cost optimal? | [Turnover, costs and the net Sharpe ratio](turnover_and_net_sharpe.md) |
| Why are trend-following returns positively skewed? | [Skewness of aggregated returns](aggregated_skewness.md) |
| How do the three system designs work in code? | [European](european_system.md), [American](american_system.md), [TSMOM](tsmom_system.md) |
| What data and costs do the backtests use? | [The futures universe and cost schedule](futures_universe_and_costs.md) |
| What does the futures evidence show, and how are Sharpe ratios compared? | [The futures evidence](case_study_futures_evidence.md), [realised Sharpe ratios](sharpe_inference.md) |

## The trendfollowing handbook

The methodology chapters form one book. Each chapter defines its method with formulas and concise
proofs, states its conventions in an eight-row convention card, works an example whose numbers the
test suite checks, and links to the functions that implement it. Symbols keep one meaning
throughout; see [Notation and conventions](notation_and_conventions.md) and the
[bibliography](bibliography.md).

### Part I: Foundations

- [Notation and conventions](notation_and_conventions.md): reserved symbols, returns of continuous
  futures, volatility-normalised returns, spans, annualisation, the Sharpe convention, timing and
  costs.
- [EWMA filters and variance-preserving signals](ewma_filters.md): span and smoothing parameter,
  the single and long-short filters with unit variance, impulse responses, mean gains and
  initialisation.
- [Volatility normalisation and position sizing](volatility_normalisation.md): the lagged EWMA
  volatility, the volatility-target weight, the system-return identity, heavy tails, dampened
  autocorrelation and the Kelly reading.
- [Return-generating processes](return_processes.md): white noise, AR(1), MA(1) and ARFIMA, their
  autocorrelation functions and moving-average weights, the hypergeometric generating function and
  the Monte Carlo engine.

### Part II: The European system in closed form

- [The P&L decomposition: autocorrelation and drift channels](pnl_decomposition.md): the exact
  sample-path identity, the expected return under any stationary autocorrelation function, and its
  Poisson-kernel spectral reading.
- [The closed-form Sharpe ratio](sharpe_ratio_closed_form.md): the variance of a product with
  excess kurtosis, the loadings $A_\nu$, $B_\nu$ and $K_\nu$, and the long-short extension.
- [Sharpe ratios under white noise, AR(1) and ARFIMA](sharpe_under_processes.md): exact and
  leading-order rules, the span trade-off and the paper's verification table.
- [Turnover, trading costs and the net Sharpe ratio](turnover_and_net_sharpe.md): the
  signal-turnover proxy, the net Sharpe ratio, the AR(1) break-even cost and cost-optimal spans.
- [Skewness of aggregated returns](aggregated_skewness.md): the closed-form skewness under white
  noise, its master curve and peak near half the span, and its empirical profile.

### Part III: Reference systems

- [The European system](european_system.md): continuous weights, caps, portfolio volatility
  targeting, warmup and the P&L, turnover and cost accounting of `BacktestOutputs`.
- [The American system](american_system.md): price crossovers with a range buffer, sizing at
  inception and trailing stops.
- [Time-series momentum](tsmom_system.md): normalised sums of signs over $M$ periods of $L$ days,
  and the sign-filter discount.
- [The futures universe and cost schedule](futures_universe_and_costs.md): 84 contracts from 1959
  to 2026, benchmarks and volume costs.

### Part IV: Evidence and inference

- [Realised Sharpe ratios and their comparison](sharpe_inference.md): the realised estimator, its
  sampling error, the Ledoit–Wolf test and regime-conditional Sharpe ratios.
- [The futures evidence of Sepp and Lucic (2026)](case_study_futures_evidence.md): grid
  backtests, the SG Trend comparison, the attribution of realised Sharpe ratios and the skewness
  of the cross-section.

## Guides

Task-oriented pages that run the methods end to end:

- [Closed-form analytics and span selection](closed_form_analytics.md): process inputs, units,
  outputs and the span-selection example.
- [Predict Sharpe from autocorrelation and drift](predict_sharpe_from_acf.md): the in-sample
  attribution workflow on packaged futures and its point-in-time boundary.
- [Compare and backtest the three systems](system_comparison_and_backtest.md): choosing a design,
  the common contract, costs, warmups, timing and the paper's backtests.
- [Choosing a trend-following or backtesting tool](choosing_a_backtesting_tool.md): a dated,
  source-backed comparison with pysystemtrade, vectorbt and Backtesting.py.

## Reference

- [API reference](api.md): every public object, grouped by the chapter that explains it.
- [Bibliography](bibliography.md): every work cited by the handbook, in one style.
- [Paper and replication](paper.md): the paper, its exhibits and the generators that reproduce them.
- [Documentation standard](documentation_standard.md): page forms, convention card, notation,
  executed examples and figure provenance.

## Research paper

Sepp, A., and Lucic, V. (2026). *The Science and Practice of Trend-Following Systems*. Working
paper. [arXiv:2607.19497](https://arxiv.org/abs/2607.19497);
[SSRN 3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787). Cite the paper for
its methods and the [software record](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff)
for the version a replication used, together with
[qis](https://github.com/ArturSepp/QuantInvestStrats/blob/main/CITATION.cff) where its analytics
are used.

<a id="project-links"></a>

## Project resources

- [PyPI package](https://pypi.org/project/trendfollowing/) and
  [source repository](https://github.com/ArturSepp/TrendFollowingSystems).
- [Issue tracker](https://github.com/ArturSepp/TrendFollowingSystems/issues) and
  [contributor guide](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CONTRIBUTING.md).
- [Changelog](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CHANGELOG.md).
- Analytics and reporting dependency: [qis](https://github.com/ArturSepp/QuantInvestStrats).

<!-- The sidebar mirrors the groups above. Keep each document in exactly one tree. -->

```{toctree}
:hidden:
:maxdepth: 1
:caption: Start here

installation
quickstart
workflows
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Part I - Foundations

notation_and_conventions
ewma_filters
volatility_normalisation
return_processes
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Part II - The European system in closed form

pnl_decomposition
sharpe_ratio_closed_form
sharpe_under_processes
turnover_and_net_sharpe
aggregated_skewness
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Part III - Reference systems

european_system
american_system
tsmom_system
futures_universe_and_costs
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Part IV - Evidence and inference

sharpe_inference
case_study_futures_evidence
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Guides

closed_form_analytics
predict_sharpe_from_acf
system_comparison_and_backtest
choosing_a_backtesting_tool
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Reference

api
bibliography
paper
documentation_standard
```
