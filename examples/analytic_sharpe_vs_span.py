"""
closed-form gross and net Sharpe ratios of the European TF system as functions
of the filter span, for the AR-1 and ARFIMA processes of the paper

reproduces the qualitative content of the process figures analytically: the
white-noise drift channel grows with the span, the AR-1 autocorrelation
channel decays with the span, and the ARFIMA ong memory creates an interior
cost-optimal span

runs without any data
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
# packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from enum import Enum
# trendfollowing
from trendfollowing.analytics.autocorrelation import population_acf
from trendfollowing.analytics.sharpe import compute_annualised_sharpe, compute_daily_moments
from trendfollowing.analytics.expected_return import expected_turnover

AF = 260.0  # annualization factor, the weekday count
VOL_TARGET = 0.15  # annualized volatility target
COST = 0.0020  # cost per unit of volatility-normalized turnover, 20bp
SPANS = [5, 10, 21, 42, 63, 125, 250, 520]


def compute_net_sharpe_by_span(phi: float = 0.0,
                               d: float = 0.0,
                               cost: float = COST,  # per unit of vol-normalized turnover
                               spans: list = SPANS,
                               ) -> pd.DataFrame:
    """gross and net Sharpe ratios of the single-filter system across spans"""
    rho = population_acf(n_lags=2000, phi=phi, d=d)
    out = {}
    for span in spans:
        gross = compute_annualised_sharpe(rho=rho, long_span=span, short_span=None, sr_underlying=0.0, af=AF)
        _, var = compute_daily_moments(rho=rho, long_span=span, short_span=None, mean=0.0, variance=1.0)
        turnover = expected_turnover(long_span=span, short_span=None, annualization_factor=AF, vol_target=VOL_TARGET)
        net = gross - cost * turnover / (VOL_TARGET * np.sqrt(var))
        out[span] = dict(gross=gross, net=net)
    return pd.DataFrame.from_dict(out, orient='index')


class LocalTests(Enum):
    AR1_KNIFE_EDGE = 1
    ARFIMA_INTERIOR_OPTIMUM = 2


def run_local_test(local_test: LocalTests) -> None:
    if local_test == LocalTests.AR1_KNIFE_EDGE:
        # the AR-1 gross Sharpe and the cost drag both decay with 1/sqrt(span),
        # so the sign of the net Sharpe ratio is span-invariant at leading order
        fig, ax = plt.subplots(1, 1, figsize=(9, 5), tight_layout=True)
        for phi in [0.05, -0.05]:
            table = compute_net_sharpe_by_span(phi=phi)
            table.columns = [f"{c}, phi={phi:+0.2f}" for c in table.columns]
            table.plot(ax=ax, marker='o')
        ax.axhline(0.0, color='black', lw=0.5)
        ax.set_xscale('log'), ax.set_xlabel('signal span, days'), ax.set_ylabel('annualized Sharpe ratio')
        ax.set_title('AR-1: the cost decides the sign of the short-memory alpha at every span')
        fig.savefig('example_ar1_knife_edge.png', dpi=150)
        print(compute_net_sharpe_by_span(phi=0.05).round(3))

    elif local_test == LocalTests.ARFIMA_INTERIOR_OPTIMUM:
        # long memory with d=0.02 creates a hump-shaped net Sharpe ratio with an
        # interior optimum at the one-to-three-month spans, as in the paper
        fig, ax = plt.subplots(1, 1, figsize=(9, 5), tight_layout=True)
        for phi in [0.05, 0.0, -0.05]:
            table = compute_net_sharpe_by_span(phi=phi, d=0.02)
            ax.plot(table.index, table['net'], marker='o', label=f"net, phi={phi:+0.2f}, d=0.02")
        ax.axhline(0.0, color='black', lw=0.5)
        ax.set_xscale('log'), ax.set_xlabel('signal span, days'), ax.set_ylabel('annualized net Sharpe ratio')
        ax.legend(), ax.set_title('ARFIMA: three cost-adjusted span-selection regimes in one figure')
        fig.savefig('example_arfima_interior_optimum.png', dpi=150)
        print(compute_net_sharpe_by_span(phi=0.0, d=0.02).round(3))


if __name__ == '__main__':
    run_local_test(local_test=LocalTests.ARFIMA_INTERIOR_OPTIMUM)
