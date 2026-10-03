---
myst:
  html_meta:
    description: >-
      The futures universe packaged with trendfollowing: 84 liquid contracts in seven asset
      classes from July 1959 to July 2026, the continuous-series and USD conventions, the 60/40
      and SG Trend benchmarks, the volume-based cost schedule by asset class and period, and the
      load_data interface with its resource override.
---

# The futures universe and cost schedule

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Implemented in [trendfollowing](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

The empirical evidence of the handbook comes from one dataset, installed with the package: daily
prices of 84 liquid futures contracts across equity, bond, short-rate, currency and commodity
markets from July 1959 to July 2026, two benchmarks, a volume-based transaction-cost schedule and
instrument metadata. This chapter documents what the dataset contains, the conventions under which
its series were built, the cost model the backtests apply, and the interface that loads it.

## Overview

The dataset supports three uses: the paper's empirical exhibits, the maintained examples, and
user research that needs a realistic multi-asset futures panel without a data licence or network
access. It is immutable: published backtests and the tests of the package depend on its bytes, and
`TF_RESOURCE_PATH` substitutes another folder rather than editing it. The chapter covers:

1. the universe and its asset classes;
2. continuous series, excess returns and USD conversion;
3. the benchmarks;
4. the cost schedule and its conversion to costs per unit of volatility;
5. the loading interface.

## Inputs, notation, and assumptions

| Convention | This article |
|---|---|
| Return basis | Daily prices of continuous futures whose relative returns are USD excess returns of the held contract |
| Normalisation | Not applicable; the systems normalise downstream |
| Signal filter | Not applicable |
| Moment basis | Not applicable: data and cost inputs |
| Annualisation | Not applicable; costs are per trade, one way |
| Timing | Daily closes on a business-day index; ragged instrument starts, common end on 10 July 2026 |
| Costs | One-way volume cost per unit of notional turnover, by asset class and period |
| trendfollowing default | `load_data(time_period=None, tickers=None)` returns prices, costs, benchmarks, metadata and the group order |

| Symbol or input | Meaning | Units and convention |
|---|---|---|
| $k_{i,t}$ | Volume cost of instrument $i$ on day $t$ | Decimal per unit of notional turnover |
| `group_data` | Asset class of each instrument | One of the seven classes |
| `names` | Short instrument name | Text |

## Methodology

### The universe

| Asset class | Contracts | Earliest contract |
|---|---:|---|
| Equities | 21 | January 1962 |
| Bonds | 16 | January 1962 |
| STIR | 4 | June 1989 |
| FX | 10 | September 1971 |
| Energy | 7 | July 1986 |
| Metals | 6 | January 1975 |
| Agriculture | 20 | July 1959 |
| Total | 84 | July 1959 |

The table is Table 7.1 of Sepp and Lucic (2026). STIR stands for short-term interest rates. The
panel has 17,487 business days from 2 July 1959 to 10 July 2026; each contract enters when its
history starts, and every contract is observed on the last day.

### Continuous series, excess returns and currency

Futures expire, so a continuous series stitches the front and second contracts at roll dates
before first notice. The stitching adjusts the price level at each roll, so the **relative returns
of the continuous series carry no roll-related jumps and equal the excess returns of the held
contract** (Carver, 2023). Futures returns are excess returns because margins are small and funding
is embedded in the futures price. Returns of non-USD contracts are converted to USD by scaling the
local return with the exchange-rate ratio, $r_t=(s_t^{\ast}/s_{t-1}^{\ast}-1)(x_t/x_{t-1})$ (Sepp and
Lucic, 2026, Section 2). Price levels of a continuous series are an accounting device: compare
their returns, not their levels, across contracts.

### Benchmarks

- **60/40 Equity/Bond**: a portfolio of 60% S&P 500 futures (`ES1 Index`) and 40% 10-year US
  Treasury futures (`TY1 Comdty`), rebalanced quarterly with `qis.backtest_model_portfolio`. The
  paper uses its quarterly returns to define bear, normal and bull regimes at the one-sigma 16% and
  84% quantiles.
- **SG Trend**: the SG Trend Index (Bloomberg `NEIXCTAT Index`), which tracks the ten largest
  trend-following CTAs, from 31 December 1999. It reports funded programmes including interest
  income, while the packaged contracts and the 60/40 benchmark are excess returns; comparisons
  therefore modestly favour the index.

### The cost schedule

**Definition (volume costs; Hurst, Ooi and Pedersen, 2017, Exhibit B1).** The one-way cost of
instrument $i$ on day $t$ is a function of its asset class and the period:

| Asset class | Until Dec 1992 | Jan 1993 to Dec 2002 | From Jan 2003 |
|---|---:|---:|---:|
| Equities | 34bp | 11bp | 6bp |
| Bonds | 6bp | 2bp | 1bp |
| STIR | 6bp | 2bp | 1bp |
| FX | 18bp | 6bp | 3bp |
| Energy, Metals, Agriculture | 58bp | 19bp | 10bp |

The table is Table 7.2 of Sepp and Lucic (2026). The costs cover rebalancing and rolling, and are
representative of a medium-to-slow trend-following system; they exclude market impact. A backtest
charges $k_{i,t}\lvert w_{i,t}-w_{i,t-1}\rvert$. Dividing by the annualised volatility of the contract
gives the cost per unit of volatility-normalised turnover of the
[turnover chapter](turnover_and_net_sharpe.md): from 2003, 6bp on an equity future with 16%
volatility is 37.5bp, and 10bp on a commodity with 25% volatility is 40bp, the range in which the
short-memory break-even costs lie.

> **Insight.** Costs fell by an order of magnitude between the 1980s and the 2000s. A backtest
> that applies today's costs to the 1970s overstates early net performance, and one that applies
> a single historical average understates recent net performance.

## Worked example

The block loads the packaged dataset, checks the universe against Table 7.1, rebuilds the cost
panel from the schedule and the 60/40 benchmark from its definition, and restricts a load to a
period and two tickers.

```python
import warnings

import numpy as np
import pandas as pd
import qis
from trendfollowing.local_path import get_universe_data_path
from trendfollowing.universe import COST_STRUCTURE, get_costs, load_data

with warnings.catch_warnings():  # the CSV reader infers the date format
    warnings.simplefilter('ignore', UserWarning)
    prices, volume_costs, benchmark_prices, descriptive_df, group_order = load_data()

# the panel and the seven asset classes of Table 7.1
assert prices.shape == (17487, 84) and volume_costs.shape == prices.shape
assert prices.index[0] == pd.Timestamp('1959-07-02') and prices.index[-1] == pd.Timestamp('2026-07-10')
assert (prices.apply(lambda s: s.last_valid_index()) == prices.index[-1]).all()
assert group_order == ['Equities', 'Bonds', 'STIR', 'FX', 'Energy', 'Metals', 'Agriculture']
counts = descriptive_df['group_data'].value_counts()
assert counts.to_dict() == {'Equities': 21, 'Agriculture': 20, 'Bonds': 16, 'FX': 10, 'Energy': 7,
                            'Metals': 6, 'STIR': 4}
earliest = prices.apply(lambda s: s.first_valid_index()).groupby(descriptive_df['group_data']).min()
assert earliest.dt.strftime('%Y-%m').to_dict() == {
    'Agriculture': '1959-07', 'Bonds': '1962-01', 'Energy': '1986-07', 'Equities': '1962-01',
    'FX': '1971-09', 'Metals': '1975-01', 'STIR': '1989-06'}

# the cost panel is the schedule mapped by asset class and period
rebuilt = get_costs(prices=prices, group_data=descriptive_df['group_data'])
np.testing.assert_array_equal(rebuilt.to_numpy(), volume_costs.to_numpy())
assert len(COST_STRUCTURE) == 3
for date, equity, bond, commodity in (('1985-06-28', 0.0034, 0.0006, 0.0058),
                                      ('1997-06-30', 0.0011, 0.0002, 0.0019),
                                      ('2015-06-30', 0.0006, 0.0001, 0.0010)):
    row = volume_costs.loc[date]
    np.testing.assert_allclose([row['ES1 Index'], row['TY1 Comdty'], row['CL1 Comdty']],
                               [equity, bond, commodity])

# the 60/40 benchmark is a quarterly rebalanced qis portfolio of ES1 and TY1
sixty_forty = qis.backtest_model_portfolio(prices=prices[['ES1 Index', 'TY1 Comdty']],
                                           weights=np.array([0.6, 0.4]),
                                           rebalancing_freq='QE').get_portfolio_nav()
packaged = benchmark_prices['60/40 Equity/Bond'].dropna()
joined = pd.concat([sixty_forty, packaged], axis=1).dropna()
np.testing.assert_allclose(joined.iloc[:, 0] / joined.iloc[0, 0], joined.iloc[:, 1] / joined.iloc[0, 1],
                           rtol=1e-12)
assert benchmark_prices['SG Trend'].first_valid_index() == pd.Timestamp('1999-12-31')

# a restricted load: one decade, two contracts
with warnings.catch_warnings():
    warnings.simplefilter('ignore', UserWarning)
    subset = load_data(time_period=qis.TimePeriod('2000-01-01', '2010-12-31'),
                       tickers=['ES1 Index', 'TY1 Comdty'])
assert subset[0].shape == (2870, 2) and subset[3].shape == (2, 2)
assert get_universe_data_path().rstrip('\\/').endswith('futures')
```

## Implementation in trendfollowing

| Quantity | Formula | trendfollowing entry point |
|---|---|---|
| Load the dataset | prices, volume costs, benchmarks, metadata, group order | `trendfollowing.universe.load_data(time_period=None, tickers=None)` |
| Cost schedule | three periods by seven asset classes | `trendfollowing.universe.COST_STRUCTURE` |
| Cost panel | the schedule mapped onto a price panel | `trendfollowing.universe.get_costs(prices, group_data)` |
| Data folder | installed resources or `TF_RESOURCE_PATH` | `trendfollowing.local_path.get_universe_data_path()` |
| Regenerate the dataset | Bloomberg and a private data layer; maintainers only | `trendfollowing.universe.generate_data()` |

The data layer lives in
[universe.py](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/src/trendfollowing/universe.py)
and the files in
[resources/futures](https://github.com/ArturSepp/TrendFollowingSystems/tree/main/src/trendfollowing/resources/futures):
`tf_system_data_prices.csv`, `_usd_returns.csv`, `_volume_costs.csv`, `_benchmark_prices.csv`,
`_descriptive_df.csv`, and the OHLC files of `ES1`, `GC1` and `TY1`. CSV loading goes through
`qis.load_df_dict_from_csv`.
API reference: {py:func}`trendfollowing.universe.load_data`,
{py:func}`trendfollowing.universe.get_costs` and
{py:func}`trendfollowing.local_path.get_universe_data_path`.

Contract details:

- `load_data` returns the tuple `(prices, volume_costs, benchmark_prices, descriptive_df,
  group_order)`. `time_period` restricts the three time series; `tickers` restricts the prices,
  the costs and the metadata, not the benchmarks.
- `TF_RESOURCE_PATH` is read when `load_data` is called, so changing it needs no new process. The
  folder must contain the same `tf_system_data_*.csv` files.
- `get_costs` assigns each period up to and including its end date and then starts the next
  period on that same date, so a period's last day takes the following period's rate: 31 December
  1992 carries the 1993–2002 costs.
- `generate_data` requires `TF_RESOURCE_PATH`, Bloomberg access and a private package; it is not
  part of the public workflow.

> **Pitfall.** Writing new or modified files into the installed `resources/futures` folder breaks
> the reproducibility of every published backtest and of the package tests. Point
> `TF_RESOURCE_PATH` to a separate folder instead.

## Interpretation and limitations

- The universe is screened for liquidity and history, which tilts it towards heavily traded
  markets; contracts that died or were delisted are not in it.
- The early decades contain fewer contracts, mostly agriculture, so a full-history portfolio
  changes composition over time.
- The cost model is proportional and ignores market impact, roll timing and slippage beyond the
  schedule; it is representative of medium-to-slow systems, not of fast or large programmes.
- A fixed end date does not freeze the vendor history from which the files were built; the
  packaged bytes, not a re-download, define the published results.

## See also

- [The European system](european_system.md)
- [Turnover, trading costs and the net Sharpe ratio](turnover_and_net_sharpe.md)
- [The futures evidence of Sepp and Lucic (2026)](case_study_futures_evidence.md)
- [Compare and backtest the three systems](system_comparison_and_backtest.md)
- [Bibliography](bibliography.md)

## References

1. Sepp, A., and Lucic, V. (2026). The Science and Practice of Trend-Following Systems. Working paper. [arXiv:2607.19497](https://arxiv.org/abs/2607.19497); [SSRN 3167787](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787). Section 7 and Tables 7.1 and 7.2 describe the universe and the costs.
2. Hurst, B., Ooi, Y. H., and Pedersen, L. H. (2017). A Century of Evidence on Trend-Following Investing. *The Journal of Portfolio Management*, 44(1), 15–29. [DOI: 10.3905/jpm.2017.44.1.015](https://doi.org/10.3905/jpm.2017.44.1.015). The volume-based cost schedule of Exhibit B1.
3. Carver, R. (2023). *Advanced Futures Trading Strategies*. Harriman House. Continuous futures series and roll adjustment.
4. Sepp, A., and Lucic, V. trendfollowing: Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python. [Software citation metadata](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).
5. Sepp, A. qis: Performance analytics, portfolio backtesting, risk analysis, and factsheet reporting in Python. [Software citation metadata](https://github.com/ArturSepp/QuantInvestStrats/blob/main/CITATION.cff).
