# Closed-form analytics and span selection

Use the closed forms to compare European-system filter spans under an explicit return process
before running an empirical backtest. They describe population moments under stated assumptions;
they do not estimate future performance or choose a production portfolio.

## Choose the return-process input

The common input is an autocorrelation array `rho` whose first element is lag zero. Build a
population input with `tf.population_acf`, or supply an empirical ACF with the same layout.

| Input | Construction | Interpretation |
|---|---|---|
| white noise | `tf.population_acf(n_lags=2000)` | zero serial correlation; any expected return comes from drift |
| AR(1) | `tf.population_acf(n_lags=2000, phi=0.05)` | lag `m` correlation is `phi**m`, with `abs(phi) < 1` |
| ARFIMA | `tf.population_acf(n_lags=2000, phi=0.0, d=0.02)` | persistent fractional process, with `abs(d) < 0.5` |
| empirical ACF | a one-dimensional array `[1.0, rho_1, rho_2, ...]` | sample estimates at the same observation frequency used by `af` |

Lag zero must equal one. More lags reduce truncation error for persistent inputs but do not cure
estimation error. An empirical ACF calculated over the full history is descriptive and must not
be treated as point-in-time evidence inside a backtest; the dedicated empirical workflow is
covered in the next guide.

## Controls and units

| Argument | Unit and meaning |
|---|---|
| `long_span` | EWMA span in observations; with daily inputs, a value of `63` means 63 trading days |
| `short_span` | optional second EWMA span in the same units; `None` selects one filter, while a distinct shorter span creates the normalized long-short filter |
| `af` | observations per year used for annualisation; `tf.AF_DAILY` is exactly `260` |
| `sr_underlying` | annualized drift of the standardized underlying, expressed as arithmetic simple-excess-return Sharpe |
| `vol_target` | annualized strategy-volatility target as a decimal, such as `0.15` for 15% |
| cost | decimal return per unit of volatility-normalized turnover; the root example uses `0.002`, or 20 bp |

Set `sr_underlying=0.0` to isolate the autocorrelation channel. A nonzero value adds the drift
channel. The Sharpe convention is
`sqrt(af) * mean(simple excess return) / standard deviation(simple excess return)`: input returns
are already excess returns, and neither a cash rate nor compounding is applied implicitly.

## Outputs

The public top-level API exposes four distinct quantities:

- `tf.expected_annual_return` returns the population arithmetic annual return at `vol_target`.
- `tf.compute_annualised_sharpe` returns the annualized population Sharpe for any supplied ACF.
- `tf.expected_turnover` returns annualized volatility-normalized turnover under serial
  independence. It is a turnover approximation when applied beside a correlated process.
- `tf.skewness_white_noise` returns the exact standardized third moment of aggregated
  single-filter returns for a white-noise underlying and a horizon measured in observations.

Sharpe is independent of the volatility target because the strategy loading cancels. Expected
return and monetary cost do depend on the target. The analytical API does not silently subtract
costs: a net result requires an explicit cost convention, as shown by the root example.

```python
import trendfollowing as tf

rho = tf.population_acf(n_lags=2000, phi=0.05)
gross_sharpe = tf.compute_annualised_sharpe(
    rho=rho, long_span=63, short_span=None, sr_underlying=0.0, af=tf.AF_DAILY
)
annual_return = tf.expected_annual_return(
    rho=rho, long_span=63, sr_underlying=0.0, vol_target=0.15, af=tf.AF_DAILY
)
turnover = tf.expected_turnover(
    long_span=63, short_span=None, annualization_factor=tf.AF_DAILY, vol_target=0.15
)
skewness = tf.skewness_white_noise(horizon=260, span=63)
```

For these fixed inputs, the values are approximately `0.200195`, `0.031523`, `7.779374`, and
`1.362449`, respectively. They are model outputs, not forecasts.

## Exact and leading-order results

“Exact” means exact under the function's process, Gaussian, filter, and finite-input assumptions;
it does not mean free of model or sampling error.

| Process | Exact interface | Leading-order interface |
|---|---|---|
| white noise with drift | `tf.sharpe_white_noise` | `tf.sharpe_white_noise_approx` |
| zero-drift AR(1) | `tf.sharpe_ar1` | `tf.sharpe_ar1_approx` |
| ARFIMA(1,d,0) | `tf.sharpe_arfima` | none |
| arbitrary finite ACF | `tf.compute_annualised_sharpe` | none |

The `_approx` functions expose long-span, weak-effect leading terms and are useful for intuition,
not as interchangeable aliases. `tf.sharpe_arfima` and the generic finite-ACF calculation are
also subject to the requested lag truncation. Independent tests compare exact and approximate
Sharpe results, generic and process-specific expected returns, and exact white-noise skewness
against brute-force Gaussian moment enumeration.

## Run the span-selection example

From a repository checkout with the core package installed, run:

```console
python examples/analytic_sharpe_vs_span.py
```

[`examples/analytic_sharpe_vs_span.py`](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/examples/analytic_sharpe_vs_span.py)
uses no dataset or network. It prints gross and cost-adjusted Sharpe across eight spans and writes
`example_arfima_interior_optimum.png` to the current directory. With its fixed
`phi=0.0`, `d=0.02`, `vol_target=0.15`, and 20 bp cost convention, net Sharpe rises from `0.071`
at 5 days to its `0.197` maximum at 42 days, then declines to `0.126` at 520 days.

Interpret the maximum as a conditional model trade-off: longer spans retain more long-memory
signal and reduce turnover, but eventually dilute the gross signal. It is not a universal span
recommendation. Change one process or cost assumption at a time and compare the entire curve,
not only its maximum.

## Failure modes

- An ACF with `rho[0] != 1`, inconsistent lag spacing, or too few lags invalidates the input
  contract or creates material truncation error.
- Mixing calendar-day spans with daily trading observations, or changing `af` without changing
  the input frequency, produces wrong annualized values.
- A span must be positive; the generic ACF calculation also requires an EWMA decay strictly
  between zero and one. Long and short spans must be distinct.
- Treating `expected_turnover` as an exact correlated-process turnover or treating the example's
  scalar cost as a market-impact model overstates what was calculated.
- Selecting the best span on a full-sample empirical ACF and reporting it as out-of-sample is
  look-ahead bias.

## Non-goals

This page does not estimate an ACF, promise future Sharpe, model execution or market impact,
run a backtest, or reproduce `qis` portfolio analytics. Continue with the {doc}`example workflows
<workflows>` for execution details, the {doc}`API map <api>` for module ownership, and the
[`qis` documentation](https://quantinveststrats.readthedocs.io/) for delegated portfolio
reporting.
