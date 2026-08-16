# Example workflows

The public examples remain at the repository root so a new reader can find and run them
without learning the package internals first.

## Compare Sharpe across filter spans

[`examples/analytic_sharpe_vs_span.py`](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/examples/analytic_sharpe_vs_span.py)
compares the analytical Sharpe ratio across spans and process assumptions.

## Predict Sharpe from an autocorrelation function

[`examples/predict_sharpe_from_acf.py`](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/examples/predict_sharpe_from_acf.py)
shows how an estimated autocorrelation function enters the generic closed-form calculation.

## Backtest the European system

[`examples/backtest_european_system.py`](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/examples/backtest_european_system.py)
runs the paper's European reference system using the futures data bundled with the package.

Run an example from the repository root after a development install:

```console
pip install -e ".[dev]"
python examples/analytic_sharpe_vs_span.py
```

Examples may write ignored `example_*.png` figures to the working directory. For the full
research workflow and its data boundary, use the {doc}`paper and replication map <paper>`.
