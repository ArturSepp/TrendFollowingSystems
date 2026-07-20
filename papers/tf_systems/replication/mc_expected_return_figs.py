
# packages
import gc
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import qis as qis
from qis.plots.utils import align_y_limits_axs, get_n_colors, scale_ax_bar_width
from qis.utils.df_freq import df_resample_at_int_index
from trendfollowing.analytics.sharpe import compute_daily_moments
from trendfollowing.analytics.autocorrelation import population_acf
from typing import List, Optional, Dict
from enum import Enum

# internal projects
import trendfollowing.processes.path_engine as pe
from trendfollowing.analytics.filters import compute_ewm_long_short_weights
from trendfollowing.analytics.autocorrelation import power_autocorr
from trendfollowing.analytics.sharpe import sharpe_white_noise, sharpe_ar1, sharpe_arfima
from trendfollowing.analytics.expected_return import (expected_pnl_ar1, expected_pnl_ma1,
                                                      expected_pnl_arfima, expected_turnover,
                                                      expected_pnl_white_noise)
from trendfollowing.systems.backtest_utils import compute_path_stats, compute_vol_norm_returns
from trendfollowing.systems.european import compute_tf_strat_pnl


def report_process_pnl(process_type: pe.ProcessType = pe.ProcessType.AR_P,
                       phi: float = 0.05,
                       ar_params: Optional[List] = None,
                       delta: float = 0.1,
                       vol_target: float = 0.15,
                       long_spans: List[int] = (2, 5, 10, 20, 40, 60, 90, 120, 252),
                       short_span: Optional[int] = None,
                       vol_span: int = 33,
                       annualization_factor: int = 260,
                       tr_costs: float = 0.00,
                       n_path: int = 50,
                       n_years: int = 50
                       ):
    """
    simulate process and
    compute pnl as function of tf_spans
    """
    phi = np.array([phi])  # initialise
    x0 = np.array([0.0])
    m_times = n_years*annualization_factor  # daily

    returns = pe.generate_paths(process_type=process_type,
                                phi=phi,
                                ar_params=ar_params,
                                x0=x0,
                                n_path=n_path,
                                m_times=m_times,
                                delta=delta,
                                mean=0.0,
                                noise_std=1.0,
                                dt=1.0 / annualization_factor)
    pnl_mcs = {}
    pnl_vols = {}
    stdev_mcs = {}
    sharpes = {}
    pnl_analytics = {}
    corrs = {}
    turnovers = {}
    cum_pnl_paths = {}
    cum_pnl_path1 = {}
    for tf_span in long_spans:
        pnl_paths, weights, vols = compute_tf_strat_pnl(returns=returns,
                                                           long_span=tf_span,
                                                           vol_span=vol_span,
                                                           vol_target=vol_target,
                                                           short_span=short_span,
                                                           annualization_factor=annualization_factor)
        total_pnl, pnl_an, vol_an, sharpe = compute_path_stats(pnl_paths=pnl_paths, annualization_factor=annualization_factor)
        turnover = np.nanmean(np.abs(weights[1:, :]-weights[:-1, :]), axis=0)
        key = f"{tf_span:0.0f}"
        pnl_mcs[key] = np.nanmean(pnl_an)
        stdev_mcs[key] = 3.0*1.96*np.nanstd(pnl_an) / np.sqrt(n_path)
        pnl_vols[key] = pd.Series(annualization_factor*np.nanstd(pnl_paths, axis=0))
        sharpes[key] = pd.Series(sharpe)
        turnovers[key] = pd.Series(turnover)
        cum_pnl_paths[key] = pd.Series(np.nanmean(pnl_paths, axis=1)).cumsum()
        cum_pnl_path1[key] = pd.Series(pnl_paths[:, 0]).cumsum()

        if process_type == pe.ProcessType.AR_P:
            pnl_analytics[key] = expected_pnl_ar1(phi=phi[0], long_span=tf_span, short_span=short_span, vol_target=vol_target, annualization_factor=annualization_factor)
        elif process_type == pe.ProcessType.MA_Q:
            pnl_analytics[key] = expected_pnl_ma1(phi=phi[0], long_span=tf_span, short_span=short_span, vol_target=vol_target, annualization_factor=annualization_factor)
        elif process_type == pe.ProcessType.ARFIMA:
            pnl_analytics[key] = expected_pnl_arfima(delta=delta, phi=ar_params[0], long_span=tf_span, short_span=short_span, vol_target=vol_target, annualization_factor=annualization_factor)
        else:
            raise NotImplementedError

        corr = qis.compute_path_corr(a1=pnl_paths[1:, :], a2=returns[1:, :])
        corrs[key] = corr

    corrs = pd.DataFrame.from_dict(corrs, orient='columns')
    sharpes = pd.DataFrame.from_dict(sharpes, orient='columns')
    pnl_vols = pd.DataFrame.from_dict(pnl_vols, orient='columns')
    turnovers = pd.DataFrame.from_dict(turnovers, orient='columns')
    cum_pnl_paths = pd.DataFrame.from_dict(cum_pnl_paths, orient='columns')
    cum_pnl_path1 = pd.DataFrame.from_dict(cum_pnl_path1, orient='columns')

    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(2, 2, figsize=(10, 10), tight_layout=True)
        qis.plot_histogram(df=sharpes, title='Sharpes',
                           ax=axs[0][0])
        qis.plot_histogram(df=pnl_vols, title='Vols',
                           ax=axs[1][0])
        qis.plot_histogram(df=turnovers, title='Turnovers',
                           ax=axs[0][1])
        qis.plot_histogram(df=corrs, title='Corrs',
                           ax=axs[1][1])

    pnl_mcs = pd.Series(pnl_mcs, name='MC')
    stdevs = pd.Series(stdev_mcs, name='Stdevs')
    pnl_analytics = pd.Series(pnl_analytics, name='Analytic')

    qis.plot_errorbar(df=pnl_mcs,
                      y_std_errors=stdevs,
                      exact=pnl_analytics,
                      colors=['slategrey'],
                      exact_colors='red',
                      var_format='{:.2%}',
                      legend_loc='upper center',
                      xlabel='Signal span',
                      capsize=5)

    fig1, axs1 = plt.subplots(2, 1, figsize=(10, 8), tight_layout=True)
    qis.plot_line(df=cum_pnl_path1, ax=axs1[0])
    qis.plot_line(df=cum_pnl_paths, ax=axs1[1])

    # path vol vs turnover
    path_vols = pd.Series(np.nanstd(returns, axis=0), name='vol')
    vols = vol_target / (np.sqrt(annualization_factor)*path_vols.to_numpy())
    print(f"t realisex={[x for x in turnovers.mean(axis=0)]}")
    print(f"t analytic={[expected_turnover(phi=phi[0], long_span=x, annualization_factor=annualization_factor, vol_target=vol_target) for idx, x in enumerate(long_spans)]}")

    print(f"pathvols={np.sqrt(annualization_factor)*np.nanstd(returns)}")
    print(f"mc vol = {np.sqrt(annualization_factor)*np.nanmean(path_vols)}")
    print(f"process_vol = {np.sqrt(1.0/(1.0-phi))}")

    df = pd.concat([path_vols, turnovers], axis=1)
    fig, ax = plt.subplots(1, 1, figsize=(10, 8), tight_layout=True)
    qis.plot_scatter(df=df, x='vol',
                     order=1,  # regression order
                     full_sample_order=None,  # full sample order can be different
                     fit_intercept=False,
                     ax=ax)


def plot_pnl_grid(process_type: pe.ProcessType = pe.ProcessType.AR_P,
                  phis: List[float] = [-0.1, 0.0, 0.1],
                  delta: float = 0.05,
                  vol_target: float = 0.15,
                  long_spans: List[int] = (2, 5, 10, 20, 40, 60, 90, 120, 252),
                  short_span: Optional[int] = None,
                  annualization_factor: int = 260,
                  tr_costs: float = 0.005):
    pnls = {}
    costs = {}
    for phi in phis:
        pnl_ = {}
        costs_ = {}
        for long_span in long_spans:
            key = f"{long_span:0.0f}"
            costs_[key] = expected_turnover(phi=phi, long_span=long_span, annualization_factor=annualization_factor, vol_target=vol_target)
            if process_type == pe.ProcessType.AR_P:
                pnl_[key] = expected_pnl_ar1(phi=phi, long_span=long_span, short_span=short_span, vol_target=vol_target, annualization_factor=annualization_factor)
            elif process_type == pe.ProcessType.MA_Q:
                pnl_[key] = expected_pnl_ma1(phi=phi, long_span=long_span, short_span=short_span, vol_target=vol_target, annualization_factor=annualization_factor)
            elif process_type == pe.ProcessType.ARFIMA:
                pnl_[key] = expected_pnl_arfima(phi=phi, delta=delta, long_span=long_span, short_span=short_span, vol_target=vol_target, annualization_factor=annualization_factor)
            else:
                raise NotImplementedError
        pnls[f"{phi:0.2f}"] = pd.Series(pnl_)
        costs[f"{phi:0.2f}"] = annualization_factor*tr_costs*pd.Series(costs_)

    pnls = pd.DataFrame.from_dict(pnls, orient='columns')
    costs = pd.DataFrame.from_dict(costs, orient='columns')
    net_pnl = pnls.subtract(costs)

    qis.plot_line(pnls, title='pnls')
    qis.plot_line(costs, title='costs')
    qis.plot_line(net_pnl, title='net_pnl')


def plot_pnl_grid_long_short(process_type: pe.ProcessType = pe.ProcessType.AR_P,
                             phi: float = 0.1,
                             delta: float = 0.05,
                             long_spans: List[int] = (5, 10, 20, 40, 60, 90, 120, 260),
                             short_spans: List[int] = (0, 5, 10, 20, 30, 40, 50),
                             vol_target: float = 0.15,
                             annualization_factor: int = 260,
                             tr_costs: float = 0.005):
    pnls = {}
    costs = {}
    for long_span in long_spans:
        key_i = f"{long_span:0.0f}"
        pnl_ = {}
        costs_ = {}
        for short_span in short_spans:
            if short_span < long_span:
                key_j = f"{short_span:0.0f}"
                costs_[key_j] = expected_turnover(phi=phi, long_span=long_span, annualization_factor=annualization_factor, vol_target=vol_target)
                if short_span == 0.0:
                    short_span = None
                if process_type == pe.ProcessType.AR_P:
                    pnl_[key_j] = expected_pnl_ar1(phi=phi, long_span=long_span, short_span=short_span, vol_target=vol_target, annualization_factor=annualization_factor)
                elif process_type == pe.ProcessType.MA_Q:
                    pnl_[key_j] = expected_pnl_ma1(phi=phi, long_span=long_span, short_span=short_span, vol_target=vol_target, annualization_factor=annualization_factor)
                elif process_type == pe.ProcessType.ARFIMA:
                    pnl_[key_j] = expected_pnl_arfima(phi=phi, delta=delta, long_span=long_span, short_span=short_span, vol_target=vol_target, annualization_factor=annualization_factor)
                else:
                    raise NotImplementedError
        pnls[key_i] = pd.Series(pnl_)
        costs[key_i] = annualization_factor*tr_costs*pd.Series(costs_)

    pnls = pd.DataFrame.from_dict(pnls, orient='index')
    costs = pd.DataFrame.from_dict(costs, orient='index')
    net_pnl = pnls.subtract(costs)

    qis.plot_heatmap(pnls, title='pnls')
    qis.plot_heatmap(costs, title='costs')
    qis.plot_heatmap(net_pnl, title='net_pnl')


class FigureType(Enum):
    AX2 = 1
    AX3_MC = 2
    AX3_AUTOCORR = 3
    AX3_SHARPE = 4  # three panels: (A) expected return, (B) Sharpe ratio, (C) turnover
    AX3_NET_SHARPE = 5  # three panels: (A) expected return, (B) Sharpe ratio, (C) net Sharpe ratio at cost net_cost


def analytic_var_code(process_type: pe.ProcessType,
                      process_variable: float,
                      delta: float,
                      mean: float,
                      long_span: float,
                      short_span: Optional[float],
                      annualization_factor: float,
                      ) -> float:
    """var_f of the daily strategy return in code units (l^2 D), for the net-sharpe drag normalisation"""
    if process_type == pe.ProcessType.WHITE_NOISE:
        phi, d, sr_z = 0.0, 0.0, process_variable
    elif process_type == pe.ProcessType.AR_P:
        phi, d, sr_z = process_variable, 0.0, mean
    elif process_type == pe.ProcessType.ARFIMA:
        phi, d, sr_z = process_variable, delta, mean
    else:
        raise NotImplementedError(f"net sharpe not implemented for {process_type}")
    rho = population_acf(n_lags=2000, phi=phi, d=d)
    _, var_f = compute_daily_moments(rho=rho, long_span=long_span, short_span=short_span,
                                     mean=sr_z / np.sqrt(annualization_factor), variance=1.0)
    return float(var_f)


def plot_article_mc_figure(process_type: pe.ProcessType = pe.ProcessType.AR_P,
                           phis: List[float] = (-0.05, 0.05,),
                           delta: float = 0.1,
                           mean: float = 0.0,
                           vol_target: float = 0.15,
                           long_spans: Dict[str, int] = {'1w': 5, '1m': 20},
                           short_span: Optional[int] = None,
                           vol_span: int = 33,
                           annualization_factor: int = 260,
                           means: List[float] = (-1.0, 1.0,),
                           tr_costs: float = 0.00,
                           net_cost: float = 0.0050,  # cost per unit of volatility-normalised turnover, for AX3_NET_SHARPE
                           n_path: int = 50,
                           n_years: int = 50,
                           mc_confidence: float = 1.0,
                           figure_type: FigureType = FigureType.AX3_AUTOCORR,
                           panel_label_offset: int = 0,  # shifts (A),(B) to (C),(D) for stacked rows
                           ) -> plt.Figure:
    """
    simulate process and
    compute pnl as function of tf_spans
    """
    m_times = n_years * annualization_factor  # daily

    pnl_mcs_phi = {}
    stdevs_mcs_phi = {}
    turnover_mcs_phi = {}
    stdev_turnover_mcs_phi = {}
    sharpe_mcs_phi = {}
    stdev_sharpe_mcs_phi = {}
    pnl_analytic_phi = {}
    turnover_analytic_phi = {}
    sharpe_analytic_phi = {}
    sharpe_net_mcs_phi = {}
    stdev_sharpe_net_mcs_phi = {}
    sharpe_net_analytic_phi = {}
    auto_corr_mean_phi = {}
    auto_corr_std_phi = {}

    if process_type == pe.ProcessType.WHITE_NOISE:
        process_variables = means
    else:
        process_variables = phis

    for process_variable in process_variables:
        if process_type == pe.ProcessType.WHITE_NOISE:
            returns = pe.generate_paths(process_type=process_type,
                                        phi=np.array([0.0]),
                                        ar_params=[0.0],
                                        x0=np.array([0.0]),
                                        n_path=n_path,
                                        m_times=m_times,
                                        delta=delta,
                                        mean=process_variable,
                                        noise_std=1.0,
                                        dt=1.0 / annualization_factor)
        else:
            returns = pe.generate_paths(process_type=process_type,
                                        phi=np.array([process_variable]),
                                        ar_params=[process_variable],
                                        x0=np.array([0.0]),
                                        n_path=n_path,
                                        m_times=m_times,
                                        delta=delta,
                                        mean=mean,
                                        noise_std=1.0,
                                        dt=1.0 / annualization_factor)
        # returns for autocorr
        returns_pd = pd.DataFrame(returns, index=pd.date_range("2000-01-01", periods=m_times, freq="B"))
        # vol_norm_returns = compute_vol_norm_returns(returns=returns, vol_span=vol_span)
        # print(f"std vol_norm_returns = {np.nanstd(vol_norm_returns, axis=0)}")

        an_returns_mcs = {}
        stdev_mcs = {}
        turnover_mcs = {}
        stdev_turnover_mcs = {}
        sharpe_mcs = {}
        stdev_sharpe_mcs = {}
        an_return_analytic = {}
        turnover_analytic = {}
        sharpe_analytic = {}
        sharpe_net_mcs = {}
        stdev_sharpe_net_mcs = {}
        sharpe_net_analytic = {}
        autoc_mean = {}
        autoc_std = {}
        for key, tf_span in long_spans.items():
            pnl_paths, weights, vols = compute_tf_strat_pnl(returns=returns,
                                                            long_span=tf_span,
                                                            vol_span=vol_span,
                                                            vol_target=vol_target,
                                                            short_span=short_span,
                                                            annualization_factor=annualization_factor)
            total_pnl, pnl_an, vol_an, sharpe = compute_path_stats(pnl_paths=pnl_paths, annualization_factor=annualization_factor)
            #vol_turnover_an = annualization_factor*np.nanmean(np.abs(weights[1:, :]-weights[:1, :]), axis=0)
            vol_turnover_an = annualization_factor*np.nanmean(vols[1:, :]*np.abs(weights[1:, :]-weights[:-1, :]), axis=0)
            # key = f"{tf_span:0.0f}"
            an_returns_mcs[key] = np.nanmean(pnl_an)
            stdev_mcs[key] = mc_confidence*1.96*np.nanstd(pnl_an) / np.sqrt(n_path)
            turnover_mcs[key] = np.nanmean(vol_turnover_an)
            stdev_turnover_mcs[key] = 10.0*mc_confidence*1.96*np.nanstd(vol_turnover_an) / np.sqrt(n_path)
            sharpe_mcs[key] = np.nanmean(sharpe)  # sharpe is the per-path MC sharpe from compute_path_stats
            stdev_sharpe_mcs[key] = mc_confidence*1.96*np.nanstd(sharpe) / np.sqrt(n_path)

            if process_type == pe.ProcessType.WHITE_NOISE:
                an_return_analytic[key] = expected_pnl_white_noise(mean=process_variable, long_span=tf_span, short_span=short_span, vol_target=vol_target, annualization_factor=annualization_factor)
                sharpe_analytic[key] = sharpe_white_noise(long_span=tf_span, short_span=short_span, sr_underlying=process_variable, af=annualization_factor)
            elif process_type == pe.ProcessType.AR_P:
                an_return_analytic[key] = expected_pnl_ar1(phi=process_variable, long_span=tf_span, short_span=short_span, mean=mean, vol_target=vol_target, annualization_factor=annualization_factor)
                sharpe_analytic[key] = sharpe_ar1(phi=process_variable, long_span=tf_span, short_span=short_span, sr_underlying=mean, af=annualization_factor)
            elif process_type == pe.ProcessType.MA_Q:
                an_return_analytic[key] = expected_pnl_ma1(phi=process_variable, long_span=tf_span, short_span=short_span, mean=mean, vol_target=vol_target, annualization_factor=annualization_factor)
                sharpe_analytic[key] = np.nan  # no closed-form Sharpe wired for MA-1; not used in the paper figures
            elif process_type == pe.ProcessType.ARFIMA:
                an_return_analytic[key] = expected_pnl_arfima(delta=delta, phi=process_variable, long_span=tf_span, short_span=short_span, mean=mean, vol_target=vol_target, annualization_factor=annualization_factor)
                sharpe_analytic[key] = sharpe_arfima(d=delta, phi=process_variable, long_span=tf_span, short_span=short_span, sr_underlying=mean, af=annualization_factor)
            else:
                raise NotImplementedError

            turnover_analytic[key] = expected_turnover(long_span=tf_span, short_span=short_span, annualization_factor=annualization_factor, vol_target=vol_target)

            if figure_type == FigureType.AX3_NET_SHARPE:
                # per-path net sharpe = (annual return - net_cost * annual vol-normalised turnover) / annual vol
                sharpe_net = (pnl_an - net_cost * vol_turnover_an) / vol_an
                sharpe_net_mcs[key] = np.nanmean(sharpe_net)
                stdev_sharpe_net_mcs[key] = mc_confidence * 1.96 * np.nanstd(sharpe_net) / np.sqrt(n_path)
                var_code = analytic_var_code(process_type=process_type, process_variable=process_variable,
                                             delta=delta, mean=mean, long_span=tf_span, short_span=short_span,
                                             annualization_factor=annualization_factor)
                sharpe_net_analytic[key] = sharpe_analytic[key] - net_cost * turnover_analytic[key] / (vol_target * np.sqrt(var_code))

            autocorr = qis.compute_autocorrelation_at_int_periods(data=returns_pd, span=tf_span)
            autoc_mean[key] = np.nanmean(autocorr)
            autoc_std[key] = mc_confidence * 1.96 * np.nanstd(autocorr) / np.sqrt(n_path)

            del pnl_paths, weights, vols
            gc.collect()

        if process_type == pe.ProcessType.WHITE_NOISE:
            key_mc = f"Monte-Carlo, drift={process_variable:0.2f}"
            key_an = f"Analytic, drift={process_variable:0.2f}"
            key_autocorr = f"mean={process_variable:0.2f}"
        else:
            key_an = f"Analytic, phi={process_variable:0.2f}"
            key_mc = f"Monte-Carlo, phi={process_variable:0.2f}"
            key_autocorr = f"phi={process_variable:0.2f}"

        pnl_mcs_phi[key_mc] = pd.Series(an_returns_mcs, name='MC')
        stdevs_mcs_phi[key_mc] = pd.Series(stdev_mcs, name='Stdevs')
        turnover_mcs_phi[key_mc] = pd.Series(turnover_mcs, name='MC')
        stdev_turnover_mcs_phi[key_mc] = pd.Series(stdev_turnover_mcs, name='MC')
        sharpe_mcs_phi[key_mc] = pd.Series(sharpe_mcs, name='MC')
        stdev_sharpe_mcs_phi[key_mc] = pd.Series(stdev_sharpe_mcs, name='MC')

        pnl_analytic_phi[key_an] = pd.Series(an_return_analytic, name='MC')
        turnover_analytic_phi[key_an] = pd.Series(turnover_analytic, name='MC')
        sharpe_analytic_phi[key_an] = pd.Series(sharpe_analytic, name='MC')
        sharpe_net_mcs_phi[key_mc] = pd.Series(sharpe_net_mcs, name='MC')
        stdev_sharpe_net_mcs_phi[key_mc] = pd.Series(stdev_sharpe_net_mcs, name='MC')
        sharpe_net_analytic_phi[key_an] = pd.Series(sharpe_net_analytic, name='MC')
        auto_corr_mean_phi[key_autocorr] = pd.Series(autoc_mean, name='Mean Autocorr')
        auto_corr_std_phi[key_autocorr] = pd.Series(autoc_std, name='Std Autocorr')

    pnl_mcs_phi = pd.DataFrame.from_dict(pnl_mcs_phi, orient='columns')
    stdevs_mcs_phi = pd.DataFrame.from_dict(stdevs_mcs_phi, orient='columns')
    turnover_mcs_phi = pd.DataFrame.from_dict(turnover_mcs_phi, orient='columns')
    stdev_turnover_mcs_phi = pd.DataFrame.from_dict(stdev_turnover_mcs_phi, orient='columns')
    pnl_analytic_phi = pd.DataFrame.from_dict(pnl_analytic_phi, orient='columns')
    turnover_analytic_phi = pd.DataFrame.from_dict(turnover_analytic_phi, orient='columns')
    sharpe_mcs_phi = pd.DataFrame.from_dict(sharpe_mcs_phi, orient='columns')
    stdev_sharpe_mcs_phi = pd.DataFrame.from_dict(stdev_sharpe_mcs_phi, orient='columns')
    sharpe_analytic_phi = pd.DataFrame.from_dict(sharpe_analytic_phi, orient='columns')
    sharpe_net_mcs_phi = pd.DataFrame.from_dict(sharpe_net_mcs_phi, orient='columns')
    stdev_sharpe_net_mcs_phi = pd.DataFrame.from_dict(stdev_sharpe_net_mcs_phi, orient='columns')
    sharpe_net_analytic_phi = pd.DataFrame.from_dict(sharpe_net_analytic_phi, orient='columns')
    auto_corr_mean_phi = pd.DataFrame.from_dict(auto_corr_mean_phi, orient='columns')
    auto_corr_std_phi = pd.DataFrame.from_dict(auto_corr_std_phi, orient='columns')

    colors = get_n_colors(n=len(process_variables))
    exact_colors = colors
    with sns.axes_style('darkgrid'):
        kwargs = dict(ncols=2, legend_loc='upper center', capsize=10,
                      exact_colors=exact_colors,
                      colors=exact_colors,
                      fontsize=12,
                      framealpha=0.9,
                      size=5,
                      marker='_',
                      exact_marker='o')

        if figure_type == FigureType.AX3_AUTOCORR:
            fig, axs = plt.subplots(1, 3, figsize=(18, 7), tight_layout=True)
            ax1, ax2 = axs[1], axs[2]
            next_fig_idx = 1
            acfs = {}
            lag_index = [1, 2, 3, 4] + list(long_spans.values())
            for process_variable in process_variables:
                if process_type == pe.ProcessType.WHITE_NOISE:
                    key_autocorr = f"mean={process_variable:0.2f}"
                    acf = pd.Series(0, index=list(np.arange(520)))
                else:
                    key_autocorr = f"phi={process_variable:0.2f}"
                    acf = pd.Series(power_autocorr(delta=delta, phi=process_variable, n=520)).iloc[1:]
                # reindex to long spans
                acfs[key_autocorr] = acf.reindex(index=lag_index).fillna(0.0)
            acfs = pd.DataFrame.from_dict(acfs, orient='columns')
            qis.plot_bars(df=acfs,
                          stacked=False,
                          title=f"({qis.idx_to_alphabet(1)}) Autocorrelation of lagged returns",
                          xlabel='Lag',
                          yvar_format='{:.1%}',
                          # y_limits=(-0.135, 0.135),
                          x_rotation=0,
                          ax=axs[0],
                          **qis.update_kwargs(kwargs, dict(ncols=1)))
            scale_ax_bar_width(axs[0], scale=0.35)

        elif figure_type == FigureType.AX3_MC:
            fig, axs = plt.subplots(1, 3, figsize=(16, 7), tight_layout=True)
            ax1, ax2 = axs[1], axs[2]
            next_fig_idx = 1
            qis.plot_errorbar(df=auto_corr_mean_phi,
                              y_std_errors=auto_corr_std_phi,
                              title=f"({qis.idx_to_alphabet(1)}) Lag-1 autocorrelation",
                              var_format='{:.2%}',
                              xlabel='Return sampling period',
                              add_zero_line=True,
                              ax=axs[0],
                              **qis.update_kwargs(kwargs, dict(ncols=1)))
        elif figure_type == FigureType.AX3_SHARPE:
            # three panels: (A) expected return, (B) Sharpe ratio, (C) turnover
            fig, axs = plt.subplots(1, 3, figsize=(18, 6), tight_layout=True)
            ax1, ax_sharpe, ax2 = axs[0], axs[1], axs[2]
            next_fig_idx = panel_label_offset
            qis.plot_errorbar(df=pnl_mcs_phi,
                              y_std_errors=stdevs_mcs_phi,
                              exact=pnl_analytic_phi,
                              title=f"({qis.idx_to_alphabet(next_fig_idx + 1)}) Expected annual return of TF system",
                              var_format='{:.1%}',
                              xlabel='Signal span',
                              ax=ax1,
                              **kwargs)
            qis.plot_errorbar(df=sharpe_mcs_phi,
                              y_std_errors=stdev_sharpe_mcs_phi,
                              exact=sharpe_analytic_phi,
                              title=f"({qis.idx_to_alphabet(next_fig_idx + 2)}) Sharpe ratio of TF system",
                              var_format='{:.2f}',
                              xlabel='Signal span',
                              ax=ax_sharpe,
                              **kwargs)
            qis.plot_errorbar(df=turnover_mcs_phi,
                              y_std_errors=stdev_turnover_mcs_phi,
                              exact=turnover_analytic_phi,
                              title=f"({qis.idx_to_alphabet(next_fig_idx + 3)}) Annualised volatility-adjusted turnover",
                              var_format='{:.0%}',
                              xlabel='Signal span',
                              ax=ax2,
                              **kwargs)
            return fig

        elif figure_type == FigureType.AX3_NET_SHARPE:
            # three panels: (A) expected return, (B) Sharpe ratio, (C) net Sharpe ratio at net_cost
            fig, axs = plt.subplots(1, 3, figsize=(18, 6), tight_layout=True)
            ax1, ax_sharpe, ax2 = axs[0], axs[1], axs[2]
            next_fig_idx = panel_label_offset
            qis.plot_errorbar(df=pnl_mcs_phi,
                              y_std_errors=stdevs_mcs_phi,
                              exact=pnl_analytic_phi,
                              title=f"({qis.idx_to_alphabet(next_fig_idx + 1)}) Expected annual return of TF system",
                              var_format='{:.1%}',
                              xlabel='Signal span',
                              ax=ax1,
                              **kwargs)
            qis.plot_errorbar(df=sharpe_mcs_phi,
                              y_std_errors=stdev_sharpe_mcs_phi,
                              exact=sharpe_analytic_phi,
                              title=f"({qis.idx_to_alphabet(next_fig_idx + 2)}) Sharpe ratio of TF system",
                              var_format='{:.2f}',
                              xlabel='Signal span',
                              ax=ax_sharpe,
                              **kwargs)
            qis.plot_errorbar(df=sharpe_net_mcs_phi,
                              y_std_errors=stdev_sharpe_net_mcs_phi,
                              exact=sharpe_net_analytic_phi,
                              title=f"({qis.idx_to_alphabet(next_fig_idx + 3)}) Net Sharpe ratio at cost of {1e4*net_cost:0.0f}bp per unit turnover",
                              var_format='{:.2f}',
                              xlabel='Signal span',
                              ax=ax2,
                              **kwargs)
            ax2.axhline(0.0, color='black', lw=1.0, ls='--', alpha=0.6)
            return fig

        else:
            fig, axs = plt.subplots(1, 2, figsize=(16, 6), tight_layout=True)
            ax1, ax2 = axs[0], axs[1]
            next_fig_idx = panel_label_offset

        next_fig_idx += 1
        qis.plot_errorbar(df=pnl_mcs_phi,
                          y_std_errors=stdevs_mcs_phi,
                          exact=pnl_analytic_phi,
                          title=f"({qis.idx_to_alphabet(next_fig_idx)}) Expected annual return of TF system",
                          var_format='{:.1%}',
                          xlabel='Signal span',
                          ax=ax1,
                          **kwargs)
        next_fig_idx += 1
        qis.plot_errorbar(df=turnover_mcs_phi,
                          y_std_errors=stdev_turnover_mcs_phi,
                          exact=turnover_analytic_phi,
                          title=f"({qis.idx_to_alphabet(next_fig_idx)}) Annualised volatility-adjusted turnover",
                          var_format='{:.0%}',
                          xlabel='Signal span',
                          ax=ax2,
                          **kwargs)
    return fig


def plot_autoccorrelations(n=100) -> plt.Figure:

    phi = 0.1
    params = {'AR-1': [(0.0, -phi), (0.0, phi)],
              'ARFIMA(1,d,0)': [(0.03, -phi), (0.03, phi)],
              'ARFIMA(1,-d,0)': [(-0.03, -phi), (-0.03, phi)]}
    acfs = {}
    for title, params_ in params.items():
        acfs_ = {}
        for delta, phi in params_:
            acfs_[f"d={delta:0.2f}, phi={phi:0.2f}"] = pd.Series(power_autocorr(delta=delta, phi=phi, n=n)).iloc[1:]
        acfs[title] = pd.DataFrame.from_dict(acfs_, orient='columns')

    kwargs = dict(labels_frequency=5, stacked=False, x_rotation=0, fontsize=14)
    with sns.axes_style('darkgrid'):
        fig, axs = plt.subplots(1, len(acfs.keys()), figsize=(16, 7), tight_layout=True)
        for idx, (title, df) in enumerate(acfs.items()):
            qis.plot_bars(df=df,
                          title=f"({qis.idx_to_alphabet(idx+1)}) {title}",
                          xlabel='lag',
                          y_limits=(-0.135, 0.135),
                          ax=axs[idx], **kwargs)
        align_y_limits_axs(axs)

    return fig


def plot_convexity(process_type: pe.ProcessType = pe.ProcessType.AR_P,
                   phi: float = 0.1,
                   long_span: float = 30.0,
                   short_span: Optional[int] = None,
                   annualization_factor: float = 260.0,
                   delta: float = 0.1,
                   vol_target: float = 0.15,
                   vol_span: int = 33,
                   tr_costs: float = 0.00,
                   n_path: int = 2,
                   n_years: int = 1000
                   ) -> plt.Figure:
        """
        simulate process and
        compute pnl as function of tf_spans
        """
        m_times = int(n_years * annualization_factor)  # daily
        returns = pe.generate_paths(process_type=process_type,
                                    phi=np.array([phi]),
                                    ar_params=[phi],
                                    x0=np.array([0.0]),
                                    n_path=n_path,
                                    m_times=m_times,
                                    delta=delta,
                                    mean=0.0,
                                    noise_std=1.0,
                                    dt=1.0 / annualization_factor)

        pnl_paths, weights, vols = compute_tf_strat_pnl(returns=returns,
                                                        long_span=long_span,
                                                        short_span=short_span,
                                                        vol_target=vol_target,
                                                        vol_span=vol_span,
                                                        annualization_factor=annualization_factor)

        returns = (vol_target/np.sqrt(annualization_factor))*compute_vol_norm_returns(returns=returns, vol_span=long_span)

        df = np.vstack((returns[:, 0], pnl_paths[:, 0])).T
        df = pd.DataFrame(df, columns=['instrument return', 'TF strategy return'])

        # sample_sizes = [1, 15, 30, 60, 125, 260]
        # sample_sizes = [1, 15, 30, 60, 260, 520, 3*260, 5*260]
        # sample_sizes = [1, 30, 60, 260, 5 * 260, 10 * 260]
        sample_sizes = [1, 5, 30, 60, 180, 260]
        with sns.axes_style("darkgrid"):
            fig, axs = plt.subplots(2, len(sample_sizes)//2, figsize=(14, 10), tight_layout=True)
            axs = qis.to_flat_list(axs)
            for idx, sample_size in enumerate(sample_sizes):
                s_returns = df_resample_at_int_index(df=df, sample_size=sample_size, func=np.nansum)
                qis.plot_scatter(df=s_returns,
                                 xvar_format='{:.0%}',
                                 yvar_format='{:.0%}',
                                 full_sample_label='OLS: ',
                                 fit_intercept=True,
                                 fontsize=10,
                                 order=2,
                                 ci=95,
                                 title=f"({qis.idx_to_alphabet(idx+1)}) Sample size={sample_size}",
                                 ax=axs[idx])
        qis.set_suptitle(fig, title=f"Return of trend-following strategy vs return of instrument")
        return fig


class LocalTests(Enum):
    ARTICLE_FIGURES = 1
    FIGURE_AUTOCORRELATION = 2
    FIGURE_CONVEXITY = 3
    REPORT_PNL = 4
    GRID_PNL = 5
    GRID_PNL_LONG_SHORT = 6
    WEIGHT = 7
    CHECK_AUTO_CORR = 8


def run_local_test(local_test: LocalTests):
    """Run local tests for development and debugging purposes.

    These are integration tests that download real data and generate reports.
    Use for quick verification during development.
    """

    pe.set_seed(8)

    long_spans = [5, 10, 20, 40, 60, 90, 130, 260, 520]
    long_spans = [5, 10, 20, 40, 60, 90, 130, 260, 520]
    long_spans = {'1w': 5, '2w': 10, '1m': 21, '3m': 63, '6m': 125, '1y': 250, '2y': 500}

    local_path = os.environ.get("TF_FIGURE_PATH", qis.local_path.get_output_path())  # set TF_FIGURE_PATH to the paper figures folder

    if local_test == LocalTests.ARTICLE_FIGURES:
        # phis = [0.1, 0.05, -0.05, -0.1]
        phis = [0.05, -0.05]
        arfima_phis = [0.05, 0.0, -0.05]
        figure_type = FigureType.AX3_SHARPE  # three panels: (A) return, (B) Sharpe, (C) turnover

        # each figure is re-seeded so that the full run reproduces the single-figure runs exactly
        pe.set_seed(8)
        fig = plot_article_mc_figure(process_type=pe.ProcessType.WHITE_NOISE, phis=phis, means=[-0.5, 0.0, 0.5],
                                     long_spans=long_spans, short_span=None, n_path=1000, tr_costs=0.0000,
                                     figure_type=figure_type)
        qis.save_fig(fig, file_name='expected_return_white_noise', local_path=local_path)

        pe.set_seed(8)
        fig = plot_article_mc_figure(process_type=pe.ProcessType.AR_P, phis=phis, mean=0.0, delta=0.0, long_spans=long_spans,
                                     short_span=None, n_path=1000, tr_costs=0.0000,
                                     figure_type=figure_type)
        qis.save_fig(fig, file_name='expected_return_ar', local_path=local_path)

        pe.set_seed(8)
        fig = plot_article_mc_figure(process_type=pe.ProcessType.AR_P, phis=phis, mean=0.5, delta=0.0, long_spans=long_spans,
                                     short_span=None, n_path=1000, tr_costs=0.0000,
                                     figure_type=figure_type)
        qis.save_fig(fig, file_name='expected_return_ar_mean', local_path=local_path)

        pe.set_seed(8)
        fig = plot_article_mc_figure(process_type=pe.ProcessType.ARFIMA, phis=arfima_phis, delta=0.02, long_spans=long_spans,
                                     short_span=None, n_path=1000, tr_costs=0.0*0.001,
                                     figure_type=figure_type)
        qis.save_fig(fig, file_name='expected_return_arfima1', local_path=local_path)

        pe.set_seed(8)
        fig = plot_article_mc_figure(process_type=pe.ProcessType.ARFIMA, phis=arfima_phis, delta=-0.02, long_spans=long_spans,
                                     short_span=None, n_path=1000, tr_costs=0.0*0.001,
                                     figure_type=figure_type)
        qis.save_fig(fig, file_name='expected_return_arfima2', local_path=local_path)

        pe.set_seed(8)
        fig = plot_article_mc_figure(process_type=pe.ProcessType.ARFIMA, phis=arfima_phis, delta=-0.01, mean=0.5, long_spans=long_spans,
                                     short_span=None, n_path=1000, tr_costs=0.0*0.001,
                                     figure_type=figure_type)
        qis.save_fig(fig, file_name='expected_return_arfima4', local_path=local_path)

    elif local_test == LocalTests.FIGURE_AUTOCORRELATION:
        fig = plot_autoccorrelations(n=51)
        qis.save_fig(fig, file_name='autoccorrelations', local_path=local_path)

    elif local_test == LocalTests.FIGURE_CONVEXITY:
        fig = plot_convexity(process_type=pe.ProcessType.WHITE_NOISE, phi=-0.03, delta=0.03, long_span=60, annualization_factor=260)
        #qis.save_fig(fig, file_name='white_noise_convexity', local_path=local_path)
        # fig = plot_convexity(process_type=pe.ProcessType.ARFIMA, phi=-0.03, delta=0.03, long_span=30, annualization_factor=260)
        # qis.save_fig(fig, file_name='arfima_convexity', local_path=local_path)

    elif local_test == LocalTests.REPORT_PNL:
        report_process_pnl(process_type=pe.ProcessType.AR_P, phi=0.015, long_spans=long_spans, short_span=None, n_path=1000, tr_costs=0.0000)
        #  report_process_pnl(process_type=pe.ProcessType.MA_Q, phi=0.2, long_spans=long_spans, short_span=5, n_path=100)
        # report_process_pnl(process_type=pe.ProcessType.ARFIMA, ar_params=[-0.038], delta=0.016, long_spans=long_spans, short_span=None, n_path=100, tr_costs=0.0*0.001)
        # report_process_pnl(process_type=pe.ProcessType.ARFIMA, ar_params=[0.088], delta=-0.007, long_spans=long_spans, short_span=5, n_path=100, tr_costs=0.0*0.001)

    elif local_test == LocalTests.GRID_PNL:
        plot_pnl_grid(process_type=pe.ProcessType.AR_P,
                      phis=[-0.015, 0.0, 0.015],
                      long_spans=long_spans, tr_costs=0.0005)

    elif local_test == LocalTests.GRID_PNL_LONG_SHORT:
        plot_pnl_grid_long_short(process_type=pe.ProcessType.ARFIMA,
                                 phi=-0.03,
                                 delta=0.0075,
                                 tr_costs=0.0005)

    elif local_test == LocalTests.WEIGHT:
        weight_long, weight_short = compute_ewm_long_short_weights(long_span=250, short_span=100)
        print(weight_long)
        print(weight_short)

        weight_long, weight_short = compute_ewm_long_short_weights(long_span=250, short_span=None)
        print(weight_long)
        print(weight_short)

        a = np.zeros(1000)
        a[1] = 1.0
        this = qis.compute_ewm_long_short(a=a, init_value=0.0, long_span=250, short_span=20)
        this = this / np.sum(this)
        this = pd.Series(this)
        this_cum = pd.Series(this).cumsum()
        qis.plot_time_series_2ax(df1=this, df2=this_cum,
                                 var_format='{:,.2%}',
                                 var_format_yax2='{:,.2%}')

    elif local_test == LocalTests.CHECK_AUTO_CORR:
        index = qis.TimePeriod('31Dec1925', '31Dec2025').to_pd_datetime_index(freq='B')
        n_path = 100
        returns = pe.generate_paths(process_type=pe.ProcessType.ARFIMA,
                                    phi=np.array([-0.1]),
                                    ar_params=[-0.1],
                                    x0=np.array([0.0]),
                                    n_path=n_path,
                                    m_times=len(index),
                                    delta=-0.03,
                                    mean=0.0,
                                    noise_std=1.0,
                                    dt=1.0 / 260)
        # adjust for vol
        pnl_paths, weights, vols = compute_tf_strat_pnl(returns=returns,
                                                        long_span=100,
                                                        vol_span=33,
                                                        vol_target=0.15,
                                                        short_span=None,
                                                        annualization_factor=260)
        vol_returns = returns / vols
        returns = pd.DataFrame(vol_returns, index=index, columns=[f"path{n+1}" for n in np.arange(n_path)])

        is_cum_autocorr = False
        long_spans = {'1d': 1, '2d': 2, '3d': 3, '1w': 5,  '2w': 10, '1m': 22, '3m': 65, '6m': 130, '1y': 260, '2y': 520}

        if is_cum_autocorr:
            autoc = {}
            for key, span in long_spans.items():
                autoc[f"period={key}"] = qis.compute_autocorrelation_at_int_periods(data=returns, span=span)
            autoc = pd.DataFrame.from_dict(autoc, orient='columns')
        else:
            autoc = qis.compute_path_autocorr_given_lags(a=returns.to_numpy(), lags=list(long_spans.values()))
            autoc = pd.DataFrame(autoc, columns=list(long_spans.keys()), index=returns.columns)
        print(autoc)
        fig, ax = plt.subplots(1, 1, figsize=(10, 8), tight_layout=True)
        qis.plot_errorbar(df=autoc.mean(axis=0).to_frame(),
                          y_std_errors=autoc.std(axis=0).to_frame()/np.sqrt(n_path),
                          title='Lag-1 autocorrelation',
                          var_format='{:.2%}',
                          xlabel='Return sampling period',
                          add_zero_line=True,
                          ax=ax)

    plt.show()


if __name__ == '__main__':

    run_local_test(local_test=LocalTests.FIGURE_CONVEXITY)
