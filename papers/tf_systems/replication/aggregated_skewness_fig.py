"""
figure: skewness of aggregated european tf returns, three panels
panel (A): closed-form skew(T) under white noise across spans with monte carlo markers,
where the mc estimator normalises the third central moment by the known variance T^{3/2}
panel (B): mc-only skewness for the three processes of section 6 (white noise, ar-1 with
phi=0.05, arfima with d=0.02) at the span of 100 days, with the standardised sample
skewness, which is accurate at 100,000 paths at all horizons shown
panel (C): empirical skewness of the gross single-filter european system at the span of
100 days on the 84 futures contracts: cross-sectional median and interquartile range of
the standardised sample skewness of overlapping T-day sums (requires the packaged data)
"""
# packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from enum import Enum
from typing import Tuple
from scipy.signal import fftconvolve
# qis / project
import qis as qis
from trendfollowing.universe import load_data
from trendfollowing.analytics.filters import span_to_nu
from trendfollowing.analytics.autocorrelation import ma_weights
from trendfollowing.analytics.skewness import skewness_white_noise, skewness_peak_horizon

SPANS = [5.0, 20.0, 63.0, 250.0]
COLORS = ['#4C72B0', '#DD8452', '#55A868', '#C44E52']
SEED = 8


def mc_skewness(span: float,
                horizons: np.ndarray,
                n_paths: int = 400_000,
                seed: int = SEED
                ) -> Tuple[np.ndarray, np.ndarray]:
    """monte carlo skewness and its standard error at the given horizons, one panel per span
    the estimator is the mean over paths of (F - Fbar)^3 / T^{3/2} with the known variance T,
    so its standard error is std((F - Fbar)^3) / (sqrt(n) T^{3/2})"""
    rng = np.random.RandomState(seed)
    nu = span_to_nu(span=span)
    sd_ew = np.sqrt((1.0 - nu) / (1.0 + nu))
    ew = np.zeros(n_paths)
    for _ in range(int(8 * span)):  # stationary warmup
        ew = nu * ew + (1.0 - nu) * rng.randn(n_paths)
    t_max = int(horizons.max())
    cum = np.zeros(n_paths)
    out = np.full(len(horizons), np.nan)
    se = np.full(len(horizons), np.nan)
    targets = {int(t): i for i, t in enumerate(horizons)}
    for t in range(1, t_max + 1):
        z = rng.randn(n_paths)
        cum += (ew / sd_ew) * z
        ew = nu * ew + (1.0 - nu) * z
        if t in targets:
            cubed = (cum - cum.mean()) ** 3 / t ** 1.5  # true Var[F_T] = T
            out[targets[t]] = cubed.mean()
            se[targets[t]] = cubed.std() / np.sqrt(n_paths)
    return out, se


def mc_skewness_processes(process: str,
                          span: float,
                          horizons: np.ndarray,
                          n_paths: int = 100_000,
                          seed: int = SEED
                          ) -> Tuple[np.ndarray, np.ndarray]:
    """mc skewness of the aggregated return for the section-6 processes, standardised
    sample skewness with its standard error, one panel per process"""
    if process not in ('wn', 'ar1', 'arfima'):
        raise ValueError(f"process must be wn, ar1, or arfima, got {process!r}")
    rng = np.random.RandomState(seed)
    nu = span_to_nu(span=span)
    sd_ew = np.sqrt((1.0 - nu) / (1.0 + nu))
    warm = int(8 * span)
    steps = warm + int(horizons.max())
    if process == 'wn':
        z = rng.randn(n_paths, steps)
    elif process == 'ar1':
        phi = 0.05
        eps = rng.randn(n_paths, steps)
        z = np.empty((n_paths, steps))
        z[:, 0] = eps[:, 0] / np.sqrt(1.0 - phi * phi)
        for t in range(1, steps):
            z[:, t] = phi * z[:, t - 1] + eps[:, t]
    else:  # arfima with d=0.02, phi=0, aggregated per memory-bounded block
        psi = ma_weights(phi=0.0, d=0.02, n_lags=400)
        block_size = 25_000
        snapshots = {int(t): [] for t in horizons}
        for _ in range(n_paths // block_size):
            eps = rng.randn(block_size, steps + 400)
            z_block = fftconvolve(eps, psi[None, :], mode='full', axes=1)[:, 400:400 + steps]
            del eps
            z_block /= z_block.std()
            for k, f_vals in _aggregate_block(z_block=z_block, nu=nu, sd_ew=sd_ew,
                                              warm=warm, targets=set(snapshots)).items():
                snapshots[k].append(f_vals)
            del z_block
        out = np.full(len(horizons), np.nan)
        se = np.full(len(horizons), np.nan)
        for i, t in enumerate(horizons):
            f_all = np.concatenate(snapshots[int(t)])
            centered = f_all - f_all.mean()
            cubed = centered ** 3 / centered.std() ** 3
            out[i] = cubed.mean()
            se[i] = cubed.std() / np.sqrt(len(f_all))
        return out, se
    ew = np.zeros(n_paths)
    cum = np.zeros(n_paths)
    out = np.full(len(horizons), np.nan)
    se = np.full(len(horizons), np.nan)
    targets = {int(t): i for i, t in enumerate(horizons)}
    for t in range(steps):
        if t >= warm:
            cum += (ew / sd_ew) * z[:, t]
            k = t - warm + 1
            if k in targets:
                centered = cum - cum.mean()
                sd = centered.std()
                cubed = centered ** 3 / sd ** 3
                out[targets[k]] = cubed.mean()
                se[targets[k]] = cubed.std() / np.sqrt(n_paths)
        ew = nu * ew + (1.0 - nu) * z[:, t]
    return out, se


def _aggregate_block(z_block: np.ndarray,
                     nu: float,
                     sd_ew: float,
                     warm: int,
                     targets: set
                     ) -> dict:
    """run the signal recursion on one block and snapshot the aggregated return at the targets"""
    n, steps = z_block.shape
    ew = np.zeros(n)
    cum = np.zeros(n)
    out = {}
    for t in range(steps):
        if t >= warm:
            cum += (ew / sd_ew) * z_block[:, t]
            k = t - warm + 1
            if k in targets:
                out[k] = cum.copy()
        ew = nu * ew + (1.0 - nu) * z_block[:, t]
    return out


VOL_SPAN = 33      # days, z convention of the empirical sections
Z_WARMUP = 250     # days, z convention of the empirical sections
MIN_OBS_MULT = 6   # at least six non-overlapping lengths of history per horizon


def empirical_skew_panel(span: float,
                         horizons: np.ndarray
                         ) -> pd.DataFrame:
    """cross-sectional panel of empirical skewness by horizon for the 84 contracts
    gross single-filter european system in the scale-free form f_t = signal_{t-1} * z_t,
    standardised sample skewness of overlapping T-day sums"""
    prices = load_data()[0]
    rows = {}
    for ticker in prices.columns:
        returns = qis.to_returns(prices=prices[ticker].dropna(), is_log_returns=False)  # arithmetic daily returns
        vol = np.sqrt(qis.compute_ewm(data=np.square(returns), span=VOL_SPAN))
        z = (returns / vol.shift(1)).iloc[Z_WARMUP:].dropna()
        signal = qis.compute_ewm(data=z, span=span)
        f = (signal.shift(1) * z).iloc[int(3 * span):].dropna()
        out = np.full(len(horizons), np.nan)
        for i, t in enumerate(horizons):
            if len(f) >= MIN_OBS_MULT * int(t):
                agg = f.rolling(int(t)).sum().dropna()
                centered = agg - agg.mean()
                out[i] = float((centered ** 3).mean() / centered.std() ** 3)
        rows[ticker] = out
    return pd.DataFrame(rows, index=horizons).T


class LocalTests(Enum):
    PAPER_FIGURE = 1


def run_local_test(local_test: LocalTests) -> None:
    if local_test == LocalTests.PAPER_FIGURE:
        fig, axs = plt.subplots(1, 3, figsize=(18.5, 4.6), tight_layout=True)
        horizons_grid = np.unique(np.round(np.logspace(0.0, np.log10(1500), 200)).astype(int))
        for span, color in zip(SPANS, COLORS):
            axs[0].plot(horizons_grid, skewness_white_noise(horizon=horizons_grid, span=span),
                        color=color, lw=1.8, label=f"span = {span:0.0f}")
            mc_horizons = np.unique(np.round(np.logspace(np.log10(2), np.log10(1500), 9)).astype(int))
            mc, se = mc_skewness(span=span, horizons=mc_horizons)
            axs[0].errorbar(mc_horizons, mc, yerr=1.96 * se, fmt='o', color=color,
                            ms=5, mfc='white', mew=1.4, elinewidth=1.2, capsize=2.5)
            t_star = skewness_peak_horizon(span=span)
            axs[0].axvline(t_star, color=color, lw=0.7, ls=':', alpha=0.6)
            axs[0].plot([span], skewness_white_noise(horizon=np.array([span]), span=span),
                        '*', color=color, ms=13, zorder=5)
        axs[0].set_xscale('log')
        axs[0].set_xlabel('aggregation horizon $T$, days')
        axs[0].set_ylabel('skewness of the $T$-period return')
        axs[0].set_title('(A) Closed form (lines) and MC (markers), white noise')
        axs[0].legend(frameon=False, loc='upper right')
        axs[0].axhline(0.0, color='black', lw=0.6)

        mc_horizons_b = np.unique(np.round(np.logspace(np.log10(2), np.log10(1500), 9)).astype(int))
        span_b = 100.0
        processes = [('white noise', 'wn', 'o', '#4C72B0', 0.92),
                     ('AR-1 $\\phi=0.05$', 'ar1', 's', '#DD8452', 1.0),
                     ('ARFIMA $d=0.02$', 'arfima', '^', '#55A868', 1.08)]
        axs[1].plot(horizons_grid, skewness_white_noise(horizon=horizons_grid, span=span_b),
                    color='black', lw=1.6, label='white noise, closed form', zorder=1)
        for label, process, marker, color, x_offset in processes:
            mc, se = mc_skewness_processes(process=process, span=span_b, horizons=mc_horizons_b)
            axs[1].errorbar(mc_horizons_b * x_offset, mc, yerr=1.96 * se, fmt=marker, color=color,
                            ms=5, mfc='white', mew=1.4, elinewidth=1.2, capsize=2.5, label=label)
        axs[1].set_xscale('log')
        axs[1].set_xlabel('aggregation horizon $T$, days')
        axs[1].set_ylabel('skewness of the $T$-period return')
        axs[1].set_title(f'(B) MC across processes, span = {span_b:0.0f}')
        axs[1].legend(frameon=False, loc='upper right')

        panel = empirical_skew_panel(span=span_b, horizons=mc_horizons_b)
        axs[2].fill_between(mc_horizons_b, panel.quantile(0.25, axis=0), panel.quantile(0.75, axis=0),
                            color='#4C72B0', alpha=0.20, label='interquartile range, 84 contracts')
        axs[2].plot(mc_horizons_b, panel.median(axis=0), 'o-', color='#4C72B0', lw=1.8, ms=5,
                    label='median across contracts')
        axs[2].plot(horizons_grid, skewness_white_noise(horizon=horizons_grid, span=span_b),
                    ls='--', color='black', lw=1.6, label='white noise, closed form')
        axs[2].set_title(f'(C) Empirical, 84 futures contracts, span = {span_b:0.0f}')
        axs[2].legend(frameon=False, loc='upper right')

        for ax in axs[1:]:
            ax.set_xscale('log')
            ax.set_xlabel('aggregation horizon $T$, days')
        for ax in axs:
            ax.axhline(0.0, color='black', lw=0.6)
            ax.set_ylim(-0.15, 2.9)
            ax.grid(True, which='major', alpha=0.35, lw=0.6)
        import os
        path = os.environ.get('TF_FIGURE_PATH', './')
        fig.savefig(f"{path}aggregated_skewness.PNG", dpi=300)
        print(f"saved to {path}aggregated_skewness.PNG")


if __name__ == '__main__':
    run_local_test(local_test=LocalTests.PAPER_FIGURE)
