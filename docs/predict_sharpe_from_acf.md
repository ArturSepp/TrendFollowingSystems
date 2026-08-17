# Predict Sharpe from autocorrelation and drift

Use this workflow to explain a realized European trend-following Sharpe ratio with sample
autocorrelation and drift measured over the same history. It is an in-sample descriptive
attribution. Turning it into a point-in-time forecast requires a separate estimation protocol
that never uses observations beyond the decision date.

## What is being compared

The authoritative root example loads four histories with
`trendfollowing.universe.load_data`, estimates sample moments, passes them to
`tf.compute_annualised_sharpe`, and compares the result with a zero-cost reference run from
`trendfollowing.systems.european.run_european_tf_system`. It evaluates realized strategy returns
with `tf.compute_realized_sharpe`.

Both columns use the complete retained history after warmup:

- **Predicted** is the closed-form population Sharpe evaluated at a sample ACF and sample drift.
- **Realized** is the arithmetic simple-excess-return Sharpe of the reference system's gross
  strategy returns over that same history.

“Predicted” therefore means model-implied from in-sample inputs. It is not an out-of-sample
prediction, a confidence bound, or a trading recommendation.

## Volatility normalization and lag construction

For each instrument, the example performs these operations in order:

1. Remove missing price observations and calculate arithmetic `price.pct_change()` returns.
2. Apply `qis.compute_ewm` to squared returns with a 33-observation span and take the square root.
3. Divide each return by `vol.shift(1)`, then discard the first 250 retained observations and
   remaining missing values. The shift prevents the current squared return from scaling itself.
4. Fix lag zero at one and use pandas lag-wise sample correlations for lags 1 through 779.
5. Calculate drift as `sqrt(260) * z.mean() / z.std()`. Pandas uses sample standard deviation
   here, so the denominator has one degree-of-freedom correction.

The normalized return `z` is dimensionless and its volatility estimate is per daily observation,
not annualized. `AF = 260` performs annualisation only when drift and Sharpe are calculated.
The ACF array has 780 entries: lag zero plus 779 positive lags. At lag `m`, only overlapping
pairs remain, so estimation precision declines with the lag.

Volatility smoothing belongs to [`qis`](https://quantinveststrats.readthedocs.io/). This package
uses that implementation rather than defining a second EWM convention.

## Sample inputs and conventions

| Input | Example value | Meaning |
|---|---:|---|
| `long_span` | 63 | single EWMA signal span in retained daily observations |
| `short_span` | `None` | no short filter leg |
| volatility span | 33 | EWM span used to standardize underlying returns |
| warmup | 250 | initial retained observations excluded from the comparison |
| ACF truncation | 779 positive lags | about three trading years at `AF = 260` |
| `sr_underlying` | sample Sharpe of `z` | drift channel in the analytical result |
| costs | `0.0` | the realized comparison is gross of transaction costs |
| realized variance | `ddof=1` | sample-variance convention used by the root example |

`tf.compute_annualised_sharpe` combines autocorrelation and drift. Set `sr_underlying=0.0` in a
separate calculation to isolate the autocorrelation channel; the root example reports only the
combined result. Its Sharpe convention is
`sqrt(AF) * mean(simple excess return) / std(simple excess return)`. There is no implicit cash-rate
subtraction or geometric-return conversion.

The prediction path constructs `z` from arithmetic price changes. The reference system runner
uses its documented log-return signal path internally, then the example converts its compounded
NAV back to simple strategy returns for realized Sharpe. Signal and weight caps retain their
runner defaults. These implementation boundaries, finite samples, stochastic volatility, and
non-Gaussian returns are reasons not to expect the two columns to be identical.

## Run the authoritative example

From a repository checkout with the core package installed:

```console
python examples/predict_sharpe_from_acf.py
```

[`examples/predict_sharpe_from_acf.py`](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/examples/predict_sharpe_from_acf.py)
uses only futures data bundled in the wheel, requires no network, writes no files, and takes about
19 seconds on the reference Python 3.12 environment. Its fixed rounded output is:

| Instrument | Predicted | Realized |
|---|---:|---:|
| ES1 Index | 0.227 | 0.206 |
| TY1 Comdty | 0.942 | 0.649 |
| GC1 Comdty | 0.283 | 0.234 |
| C 1 Comdty | 0.625 | 0.620 |

Read proximity as an in-sample attribution check: the sample autocorrelation and drift contain
information consistent with the realized gross strategy return. Read a gap as model residual,
not as a trade. The four rows are not independent validation samples because the model and
comparison use each row's same history.

## Point-in-time use

A point-in-time research design must define an expanding or rolling estimation window. At every
decision date `t`:

1. construct volatility-normalized returns using only information available through `t`;
2. estimate drift and every ACF lag only from that window;
3. freeze the resulting parameters and signal at `t`; and
4. apply the decided weight over the next return interval, then advance the window.

The `vol.shift(1)` operation is necessary but not sufficient: it makes local volatility scaling
causal, while the root example's full-sample ACF and drift remain in-sample. A backtest that
reuses those full-sample estimates at earlier dates has look-ahead bias.

## Data coverage

The bundled dataset is daily and has ragged instrument starts. For the four fixed histories in
the current artifact, the example retains:

| Instrument | First price | Last price | Price observations | Post-warmup `z` observations |
|---|---|---|---:|---:|
| ES1 Index | 1962-01-02 | 2026-07-10 | 16,834 | 16,584 |
| TY1 Comdty | 1962-01-05 | 2026-07-10 | 16,831 | 16,581 |
| GC1 Comdty | 1975-01-06 | 2026-07-10 | 13,440 | 13,190 |
| C 1 Comdty | 1959-07-03 | 2026-07-10 | 17,486 | 17,236 |

The selected bundled series have no internal missing price rows between their first and last
valid observations. Other instruments or user-supplied data need not share that property.

## Missing observations

The example handles every ticker separately: it drops missing prices before calculating returns,
so it neither forces a common panel start nor fills a missing price. If a user-supplied series has
an internal gap, the returns on either side become adjacent retained observations. A lag then
means retained observations, not necessarily consecutive exchange days. Audit the calendar,
duplicates, stale marks, contract-roll treatment, and gap policy before interpreting the ACF.

The sample must also be materially longer than the warmup and maximum lag. A high-lag correlation
can be computed from fewer pairs but can be too noisy to support a stable attribution.

## The paper comparison

The published attribution is a replication result tied to the committed paper data, formulas,
and conventions; it is not a promise of future performance. The full replication module
`papers/tf_systems/replication/autocorr_attribution.py` uses a biased, positive-semidefinite sample
ACF with one demeaning and divisor `T`, applies `ddof=0` to reproduce the committed exhibits, and
reports autocorrelation-only, total, and realized tables across instruments and spans.

Those choices intentionally differ from the smaller root example's lag-wise pandas correlation
and `ddof=1`. Keep each workflow internally consistent rather than mixing one ACF estimator with
the other workflow's checked values. Use the {doc}`paper and replication map <paper>` to reproduce
the published exhibit.

## Estimation risk

- Sample drift is noisy and enters the closed form nonlinearly; a small mean change can materially
  move the predicted Sharpe.
- Long-lag ACF estimates use fewer pairs and invite multiple-testing and truncation sensitivity.
- Volatility regimes, structural breaks, heavy tails, and signal or weight caps violate or extend
  the stationary Gaussian closed-form assumptions.
- Choosing the instrument, span, lag count, or sample start after seeing the same realized Sharpe
  creates selection bias.
- Similar predicted and realized values in-sample do not supply uncertainty intervals or evidence
  of persistence.

This guide does not define a production forecast, optimize an estimation window, change the
paper's values, or duplicate `qis` backtesting and volatility documentation. Continue with the
{doc}`closed-form analytics guide <closed_form_analytics>` for model assumptions and the
{doc}`example workflows <workflows>` for execution boundaries.
