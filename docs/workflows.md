# Example workflows

The public examples remain at the repository root so a new reader can find and run them
without learning the package internals first.

## Compare Sharpe across filter spans

[`examples/analytic_sharpe_vs_span.py`](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/examples/analytic_sharpe_vs_span.py)
compares the analytical Sharpe ratio across spans and process assumptions. It uses no data or
network, takes about 3 seconds on the reference Python 3.12 environment, prints the gross/net
span table, and writes `example_arfima_interior_optimum.png` to the current directory. The fixed
case has its maximum net Sharpe of about `0.197` at the 42-day span.

## Predict Sharpe from an autocorrelation function

[`examples/predict_sharpe_from_acf.py`](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/examples/predict_sharpe_from_acf.py)
shows how an estimated autocorrelation function enters the generic closed-form calculation. It
uses the futures data installed in the wheel, requires no network, takes about 18 seconds, and
writes no files. The fixed four-contract output starts with ES1 predicted/realized Sharpe of
approximately `0.227`/`0.206`.

## Backtest the European system

[`examples/backtest_european_system.py`](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/examples/backtest_european_system.py)
runs the paper's European reference system using the futures data bundled with the package. It
requires no network, takes about 24 seconds, prints the performance summary, and writes
`example_european_backtest.png` to the current directory. The fixed LS(250,20) case reports
Sharpe `1.095`, annualized volatility `0.152`, annualized return `0.166`, and maximum drawdown
`-0.362`.

The timings are observations from the 2026-08-16 Python 3.12 verification environment, not
performance guarantees. Run an example from the repository root after a core install:

```console
pip install trendfollowing
python examples/analytic_sharpe_vs_span.py
```

CI executes all three scripts with the non-interactive `Agg` backend from a temporary current
directory. Generated `example_*.png` figures therefore remain isolated and are ignored in a
development checkout. For the full research workflow and its data boundary, use the
{doc}`paper and replication map <paper>`.
