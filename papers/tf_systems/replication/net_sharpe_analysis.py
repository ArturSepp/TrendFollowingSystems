"""
net sharpe ratio analysis: span and cost grids, break-even costs, and optimal-span validation
reproduces the net-sharpe numbers and the ar-1 closed forms quoted in the paper
"""
# packages
import numpy as np
from enum import Enum
from typing import Optional, Tuple
# qis / project
from trendfollowing.analytics.sharpe import compute_daily_moments
from trendfollowing.analytics.filters import span_to_nu
from trendfollowing.analytics.autocorrelation import population_acf

AF = 260.0


def sr_net_analytic(rho: np.ndarray,
                    long_span: float,
                    cost: float,  # cost per unit of volatility-normalised turnover
                    sr_underlying: float = 0.0,
                    af: float = AF,
                    ) -> Tuple[float, float, float]:
    """(net sharpe, gross sharpe, cost drag) per corollary col:sr and equation eq:sr_net of the paper"""
    mean_f, var_f = compute_daily_moments(rho=rho, long_span=long_span, short_span=None,
                                          mean=sr_underlying / np.sqrt(af), variance=1.0)
    nu = span_to_nu(long_span)
    gross = float(np.sqrt(af) * mean_f / np.sqrt(var_f))
    drag = float(2.0 * af * cost / np.sqrt(np.pi) * np.sqrt(1.0 - nu) / np.sqrt(var_f))
    return gross - drag, gross, drag


def break_even_cost_ar1(phi: float, af: float = AF) -> float:
    """long-span break-even cost c*_inf = sqrt(pi/(2a)) * phi/(1-phi), equation eq:sr_net_ar1"""
    return float(np.sqrt(np.pi / (2.0 * af)) * phi / (1.0 - phi))


def optimal_span_ar1(phi: float,
                     cost: float,
                     af: float = AF,
                     ) -> float:
    """interior optimal span of the net sharpe ratio under zero-drift ar-1, equation eq:sr_net_span
    span* = (6 phi/(1-phi) + 1.5 x)/(1-x) with x = cost/c*_inf, exact in the limit x -> 1"""
    x = cost / break_even_cost_ar1(phi=phi, af=af)
    if not x < 1.0:
        raise ValueError(f"cost must be below the break-even level, got x={x!r}")
    return float((6.0 * phi / (1.0 - phi) + 1.5 * x) / (1.0 - x))


def rho_arfima0d0(d: float, n_lags: int = 400000) -> np.ndarray:
    """acf of arfima(0,d,0) by the gamma-ratio recursion rho(m) = rho(m-1)*(m-1+d)/(m-d)"""
    rho = np.ones(n_lags)
    for m in range(1, n_lags):
        rho[m] = rho[m - 1] * (m - 1.0 + d) / (m - d)
    return rho


def argmax_span(rho: np.ndarray,
                cost: float,
                span_bounds: Tuple[float, float] = (2.0, 20000.0),
                n_grid: int = 500,
                af: float = AF,
                ) -> Tuple[float, float]:
    """(optimal span, net sharpe at the optimum) by grid search on a log-spaced span grid"""
    spans = np.geomspace(span_bounds[0], span_bounds[1], n_grid)
    vals = np.array([sr_net_analytic(rho=rho, long_span=s, cost=cost, af=af)[0] for s in spans])
    i = int(np.argmax(vals))
    return float(spans[i]), float(vals[i])


class LocalTests(Enum):
    SPAN_COST_GRID = 1
    AR1_OPTIMAL_SPAN = 2
    ARFIMA_SCALING = 3


def run_local_test(local_test: LocalTests) -> None:
    if local_test == LocalTests.SPAN_COST_GRID:
        # the net sharpe grids behind the figures and the section 6 discussion
        for name, phi, d in [('AR-1 phi=0.05', 0.05, 0.0), ('ARFIMA d=0.02', 0.0, 0.02)]:
            rho = population_acf(n_lags=2000, phi=phi, d=d)
            print(f"=== {name}, c=20bp ===")
            for span in [5.0, 10.0, 21.0, 63.0, 125.0, 250.0, 500.0]:
                net, gross, drag = sr_net_analytic(rho=rho, long_span=span, cost=0.0020)
                print(f"span {span:>5.0f}: gross {gross:7.3f}, net {net:7.3f}")

    elif local_test == LocalTests.AR1_OPTIMAL_SPAN:
        # validation of equation eq:sr_net_span against the exact optimum
        phi = 0.05
        c_star = break_even_cost_ar1(phi=phi)
        rho = population_acf(n_lags=2000, phi=phi, d=0.0)
        print(f"AR-1 phi={phi}: c*_inf = {1e4 * c_star:.1f}bp")
        for x in [0.8, 0.9, 0.95, 0.98]:
            s_exact, v = argmax_span(rho=rho, cost=x * c_star)
            s_formula = optimal_span_ar1(phi=phi, cost=x * c_star)
            print(f"x={x:.2f}: exact span* {s_exact:7.1f}, formula {s_formula:7.1f}, ratio {s_exact / s_formula:.2f}")

    elif local_test == LocalTests.ARFIMA_SCALING:
        # the scaling-regime invariant of the arfima footnote: drag/gross -> (1-2d)/(1+2d) at the optimum
        d = 0.2
        rho = rho_arfima0d0(d=d, n_lags=2000000)
        print(f"ARFIMA d={d}: target drag share (1-2d)/(1+2d) = {(1 - 2 * d) / (1 + 2 * d):.3f}")
        for cbp in [50.0, 200.0, 800.0]:
            s_star, _ = argmax_span(rho=rho, cost=cbp / 1e4, span_bounds=(2.0, 100000.0), n_grid=350)
            net, gross, drag = sr_net_analytic(rho=rho, long_span=s_star, cost=cbp / 1e4)
            print(f"c={cbp:>5.0f}bp: span* {s_star:8.0f}, drag/gross {drag / gross:.3f}")


if __name__ == '__main__':
    run_local_test(local_test=LocalTests.AR1_OPTIMAL_SPAN)
