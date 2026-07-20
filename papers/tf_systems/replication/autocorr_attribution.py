"""
attribution of european tf sharpe ratios to empirical autocorrelation and drift (paper exhibit m8)
per instrument: estimate the sample acf and drift of volatility-normalised returns, feed them into
the analytical sharpe formula, and compare with the realised sharpe of the gross european tf backtest
panels: (a) evolution of ewm lag-1 autocorrelation across instruments,
        (b) predicted vs realised sharpe scatter across instruments and spans,
        (c) cross-sectional medians by span: predicted (autocorrelation-only), predicted (total), realised
"""
# packages
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from enum import Enum
from typing import List, Optional, Tuple
# qis
import qis as qis
# project
from trendfollowing.universe import load_data
from trendfollowing.systems.backtest_utils import compute_vol_norm_returns
from trendfollowing.systems.european import compute_tf_strat_pnl
from trendfollowing.analytics.sharpe import compute_annualised_sharpe, compute_realized_sharpe
from trendfollowing.analytics.filters import span_to_nu

SPANS: List[int] = [5, 10, 21, 42, 63, 125, 250, 520]  # ewma filter spans in days
VOL_SPAN: int = 33  # ewma span of the volatility estimator, as in the paper backtests
AF: float = 260.0  # annualisation factor, as in the paper
N_LAGS: int = 780  # acf truncation at three years of daily lags
WARMUP: int = 250  # days skipped at the start of each instrument sample, as in the backtests
MIN_OBS: int = 1560  # minimum sample length after warmup, six years of daily data
EWM_AC_SPAN: int = 2600  # ten-year ewm span for the lag-1 autocorrelation evolution panel


def compute_sample_acf(z: np.ndarray,
                       n_lags: int = N_LAGS
                       ) -> np.ndarray:
    """
    biased sample acf rho(m) = gamma(m) / gamma(0) for m = 0..n_lags
    gamma(m) = (1/T) sum_{t=m+1..T} (z_t - zbar) (z_{t-m} - zbar), the psd-guaranteeing estimator

    computed locally rather than via a qis helper so the normalisation matches the rho(m)
    convention of the paper Sharpe formula (Corollary col:sr) exactly: divisor T for every lag,
    single demeaning, no small-sample or windowing correction
    """
    if z.ndim != 1:
        raise ValueError(f"z must be one-dimensional, got ndim={z.ndim!r}")
    n_obs = len(z)
    if n_obs <= n_lags:
        raise ValueError(f"sample length {n_obs!r} must exceed n_lags={n_lags!r}")
    x = z - np.mean(z)
    gamma = np.empty(n_lags + 1)
    for m in range(n_lags + 1):
        gamma[m] = np.dot(x[m:], x[:n_obs - m]) / n_obs
    return gamma / gamma[0]


def compute_attribution_tables(prices: pd.DataFrame,
                               spans: List[int] = SPANS,
                               long_short_pairs: Optional[List[Tuple[int, int]]] = ((250, 20),),
                               vol_span: int = VOL_SPAN,
                               n_lags: int = N_LAGS,
                               warmup: int = WARMUP,
                               min_obs: int = MIN_OBS,
                               af: float = AF
                               ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    per-instrument predicted and realised sharpe ratios of the single-filter european tf system
    predicted_total uses the sample acf and the sample drift of z, predicted_ac sets the drift to zero
    realised is the gross backtest sharpe on the same sample, so the tables share instruments and spans
    long_short_pairs adds the long-short filter configurations as extra columns labelled 'long/short'
    returns (predicted_total, predicted_ac, realised, instrument_stats)
    """
    returns_df = qis.to_returns(prices, is_log_returns=True, is_first_zero=False)
    returns_np = returns_df.to_numpy()
    z_np = compute_vol_norm_returns(returns=returns_np, vol_span=vol_span)

    configs = [(span, None, span) for span in spans]
    if long_short_pairs is not None:
        configs += [(long, short, f"{long}/{short}") for long, short in long_short_pairs]

    pnls = {key: compute_tf_strat_pnl(returns=returns_np,
                                      long_span=long_span,
                                      short_span=short_span,
                                      vol_span=vol_span,
                                      vol_target=0.15,
                                      annualization_factor=af)[0]
            for long_span, short_span, key in configs}

    predicted_total, predicted_ac, realised, stats = {}, {}, {}, {}
    for idx, ticker in enumerate(returns_df.columns):
        valid = np.where(np.isfinite(returns_np[:, idx]))[0]
        if len(valid) < warmup + min_obs:
            continue
        sample = valid[warmup:]
        z_i = z_np[sample, idx]
        z_i = z_i[np.isfinite(z_i)]
        rho = compute_sample_acf(z=z_i, n_lags=n_lags)
        theta = float(np.var(z_i))
        sr_z = compute_realized_sharpe(returns=z_i, af=af, ddof=0)  # ddof=0 matches the committed exhibits

        pred_total_i, pred_ac_i, realised_i = {}, {}, {}
        for long_span, short_span, key in configs:
            with np.errstate(invalid='ignore'):
                pred_total_i[key] = compute_annualised_sharpe(rho=rho, long_span=long_span, short_span=short_span,
                                                              sr_underlying=sr_z, variance=theta, af=af)
                pred_ac_i[key] = compute_annualised_sharpe(rho=rho, long_span=long_span, short_span=short_span,
                                                           sr_underlying=0.0, variance=theta, af=af)
            f_i = pnls[key][sample, idx]
            f_i = f_i[np.isfinite(f_i)]
            realised_i[key] = compute_realized_sharpe(returns=f_i, af=af, ddof=0)  # ddof=0 matches the committed exhibits
        predicted_total[ticker] = pred_total_i
        predicted_ac[ticker] = pred_ac_i
        realised[ticker] = realised_i
        x_i = z_i - np.mean(z_i)
        std_i = np.std(z_i)
        stats[ticker] = dict(n_obs=len(z_i), theta=theta, sr_z=sr_z, rho_1=rho[1],
                             skew=float(np.mean(x_i ** 3) / std_i ** 3),
                             xkurt=float(np.mean(x_i ** 4) / std_i ** 4 - 3.0))

    predicted_total = pd.DataFrame.from_dict(predicted_total, orient='index')
    predicted_ac = pd.DataFrame.from_dict(predicted_ac, orient='index')
    realised = pd.DataFrame.from_dict(realised, orient='index')
    stats = pd.DataFrame.from_dict(stats, orient='index')
    return predicted_total, predicted_ac, realised, stats


def compute_ewm_lag1_autocorr(prices: pd.DataFrame,
                              vol_span: int = VOL_SPAN,
                              ewm_span: int = EWM_AC_SPAN
                              ) -> pd.DataFrame:
    """
    ewm lag-1 autocorrelation of volatility-normalised daily returns per instrument
    """
    returns_df = qis.to_returns(prices, is_log_returns=True, is_first_zero=False)
    z_np = compute_vol_norm_returns(returns=returns_df.to_numpy(), vol_span=vol_span)
    z_df = pd.DataFrame(z_np, index=returns_df.index, columns=returns_df.columns)
    autocorr_df = qis.compute_ewm_vector_autocorr_df(data=z_df, span=ewm_span, lag=1, is_normalize=True)
    return autocorr_df


def plot_attribution_figure(predicted_total: pd.DataFrame,
                            predicted_ac: pd.DataFrame,
                            realised: pd.DataFrame,
                            autocorr_df: pd.DataFrame,
                            spans: List[int] = SPANS,
                            ac_start: str = '1971-01-01'  # display start after the ewm warmup
                            ) -> plt.Figure:
    """
    three-panel exhibit: (a) autocorrelation evolution, (b) predicted vs realised scatter, (c) medians by span
    """
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(1, 3, figsize=(18, 5.5), tight_layout=True)

        # (a) evolution of ewm lag-1 autocorrelation: cross-sectional median and interquartile band
        autocorr_df = autocorr_df.replace(0.0, np.nan)  # ewm warmup zeros are not estimates
        quantiles = pd.concat([autocorr_df.quantile(q=0.25, axis=1).rename('25% quantile'),
                               autocorr_df.median(axis=1).rename('Median'),
                               autocorr_df.quantile(q=0.75, axis=1).rename('75% quantile')], axis=1).dropna().loc[ac_start:]
        qis.plot_time_series(df=quantiles,
                             title=f"(A) EWM lag-1 autocorrelation of volatility-normalised returns",
                             x_date_freq='5YE',
                             date_format='%Y',
                             trend_line=qis.TrendLine.ZERO_SHADOWS,
                             legend_loc='upper left',
                             ax=axs[0])

        # (b) predicted vs realised sharpe across instruments and spans
        ax = axs[1]
        cmap = plt.get_cmap('viridis', len(spans))
        for i, span in enumerate(spans):
            ax.scatter(predicted_total[span], realised[span], s=14, alpha=0.65,
                       color=cmap(i), label=f"span={span}")
        joint = pd.concat([predicted_total[spans].stack().rename('pred'), realised[spans].stack().rename('real')],
                          axis=1).replace([np.inf, -np.inf], np.nan).dropna()
        slope, intercept = np.polyfit(joint['pred'], joint['real'], deg=1)
        corr = joint['pred'].corr(joint['real'])
        lims = np.array([joint.min().min(), joint.max().max()])
        ax.plot(lims, lims, color='black', linestyle='dashed', linewidth=1)
        ax.plot(lims, intercept + slope * lims, color='red', linewidth=1)
        ax.set_xlabel('Predicted Sharpe ratio from sample ACF and drift')
        ax.set_ylabel('Realised Sharpe ratio of gross European TF')
        ax.set_title(f"(B) Predicted vs realised Sharpe: corr={corr:.2f}, slope={slope:.2f}",
                     fontsize=11)
        ax.legend(loc='upper left', fontsize=7, ncol=2, title='filter span', title_fontsize=8)

        # (c) cross-sectional medians by span with realised interquartile band
        ax = axs[2]
        x = np.arange(len(spans))
        ax.plot(x, predicted_ac[spans].median(axis=0).values, marker='o', label='Predicted, autocorrelation only')
        ax.plot(x, predicted_total[spans].median(axis=0).values, marker='o', label='Predicted, autocorrelation and drift')
        ax.plot(x, realised[spans].median(axis=0).values, marker='s', color='black', label='Realised, gross')
        ax.fill_between(x, realised[spans].quantile(0.25, axis=0).values, realised[spans].quantile(0.75, axis=0).values,
                        alpha=0.2, color='black', label='Realised interquartile range')
        ax.set_xticks(x)
        ax.set_xticklabels([str(s) for s in spans])
        ax.set_xlabel('EWMA filter span in days')
        ax.set_ylabel('Annualised Sharpe ratio')
        ax.set_title("(C) Cross-sectional medians by filter span", fontsize=11)
        ax.axhline(0.0, color='grey', linewidth=0.5)
        ax.legend(loc='upper left', fontsize=8)
    return fig


class LocalTests(Enum):
    ATTRIBUTION_FIGURE = 1
    SMOKE_TEST = 2


def run_local_test(local_test: LocalTests):
    local_path = os.environ.get("TF_FIGURE_PATH", qis.local_path.get_output_path())
    if local_test == LocalTests.ATTRIBUTION_FIGURE:
        prices, _, _, descriptive_df, _ = load_data()
        predicted_total, predicted_ac, realised, stats = compute_attribution_tables(prices=prices)
        autocorr_df = compute_ewm_lag1_autocorr(prices=prices)
        fig = plot_attribution_figure(predicted_total=predicted_total, predicted_ac=predicted_ac,
                                      realised=realised, autocorr_df=autocorr_df)
        qis.save_fig(fig, file_name='autocorr_attribution', local_path=local_path)
        for name, df in dict(predicted_total=predicted_total, predicted_ac=predicted_ac,
                             realised=realised, stats=stats).items():
            df.to_csv(os.path.join(local_path, f"attribution_{name}.csv"))
        joint = pd.concat([predicted_total[SPANS].stack().rename('pred'),
                           realised[SPANS].stack().rename('real')], axis=1).dropna()
        slope, _ = np.polyfit(joint['pred'], joint['real'], deg=1)
        print(f"pooled corr = {joint['pred'].corr(joint['real']):.4f}, slope = {slope:.4f}")
        autocorr_df = autocorr_df.replace(0.0, np.nan)  # ewm warmup zeros are not estimates
        quantiles = pd.concat([autocorr_df.quantile(q=0.25, axis=1).rename('q25'),
                               autocorr_df.median(axis=1).rename('median'),
                               autocorr_df.quantile(q=0.75, axis=1).rename('q75')], axis=1).dropna()
        quantiles.to_csv(os.path.join(local_path, "attribution_ac_evolution.csv"))
        print(f"instruments included: {len(stats.index)}")
        print(f"medians by span:\npred_ac:\n{predicted_ac.median(axis=0)}\n"
              f"pred_total:\n{predicted_total.median(axis=0)}\nrealised:\n{realised.median(axis=0)}")

    elif local_test == LocalTests.SMOKE_TEST:
        prices, _, _, _, _ = load_data()
        prices = prices.iloc[:, :6]
        predicted_total, predicted_ac, realised, stats = compute_attribution_tables(
            prices=prices, spans=[21, 63, 250], n_lags=260, min_obs=1040)
        print(f"stats:\n{stats}")
        print(f"predicted_total:\n{predicted_total}")
        print(f"predicted_ac:\n{predicted_ac}")
        print(f"realised:\n{realised}")


if __name__ == '__main__':
    run_local_test(local_test=LocalTests.ATTRIBUTION_FIGURE)
