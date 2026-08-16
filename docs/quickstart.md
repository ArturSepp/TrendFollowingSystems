# Quickstart

Install the released package from PyPI:

```console
pip install trendfollowing
```

Then evaluate the closed-form annualized Sharpe ratio of the European system under an
AR(1) return process:

```python
import trendfollowing as tf

sharpe = tf.sharpe_ar1(phi=0.05, long_span=21)
print(sharpe)
```

The package supports Python 3.10 and newer and depends on `qis` for portfolio analytics
and reporting. Continue with the
[repository README](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/README.md)
for the generic autocorrelation formula and the packaged-universe backtest, or choose a
maintained {doc}`workflow <workflows>`.
