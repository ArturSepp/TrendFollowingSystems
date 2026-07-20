"""
monte carlo verification of the analytical sharpe ratio in trendfollowing.analytics.sharpe
simulation mirrors the paper's mc design: daily returns with dt = 1/af, drift mu_an*dt, innovation variance dt,
ewma volatility normalisation with span 33 and one-day lag, variance-preserving (long-short) ewma signal,
daily strategy return f_t = (sigma_target/sqrt(af)) * S_{t-1} * z_t
estimators: pooled sr = sqrt(af)*mean(f)/std(f) over all paths, and the mean of per-path sr with its 95% ci
"""
# packages
import numpy as np
import pandas as pd
from enum import Enum
from typing import Optional, Tuple, List, Dict
from scipy.signal import fftconvolve
# project
from trendfollowing.analytics.filters import span_to_nu, compute_ewm_long_short_weights
from trendfollowing.analytics.autocorrelation import population_acf, ma_weights
from trendfollowing.analytics.sharpe import compute_annualised_sharpe

AF = 260.0  # annualisation factor, trading days per year
VOL_SPAN = 33  # ewma span of the volatility estimator, as in the paper mc design
BURN = 1040  # warm-up observations discarded, 4 years
SIGMA_TARGET = 0.15  # cancels in the sharpe ratio, kept for return-level checks


def simulate_returns(n_paths: int = 1000,
                     n_obs: int = 5200,  # kept observations per path after burn-in
                     mu_an: float = 0.0,  # annualised drift of raw returns
                     phi: float = 0.0,  # ar-1 coefficient
                     d: float = 0.0,  # arfima fractional order
                     seed: int = 8,
                     n_ma: int = 5000,  # truncation of the fractional ma(inf) expansion
                     t_dof: Optional[float] = None  # student-t dof, standardised to unit variance, None for gaussian
                     ) -> np.ndarray:
    """
    simulate daily returns r_t of arfima(1,d,0) with drift: (1-phi*B)(1-B)^d (r_t - mu) = eps_t
    innovations have variance dt = 1/af, so the unit-variance acf matches population_acf
    gaussian innovations by default, standardised student-t with excess kurtosis 6/(t_dof-4) when t_dof is set
    """
    if t_dof is not None and t_dof <= 4.0:
        raise ValueError(f"t_dof must exceed 4 for a finite kurtosis, got {t_dof!r}")
    rng = np.random.default_rng(seed)
    dt = 1.0 / AF

    def draw_innovations(shape: Tuple[int, int]) -> np.ndarray:
        if t_dof is None:
            return rng.standard_normal(shape) * np.sqrt(dt)
        return rng.standard_t(df=t_dof, size=shape) * np.sqrt((t_dof - 2.0) / t_dof) * np.sqrt(dt)

    n_total = n_obs + BURN
    if np.isclose(d, 0.0):
        eps = draw_innovations((n_paths, n_total))
        u = eps
    else:
        eps = draw_innovations((n_paths, n_total + n_ma))
        # ma(inf) weights of (1-B)^{-d}: psi_0 = 1, psi_k = psi_{k-1}*(k-1+d)/k
        psi = np.ones(n_ma + 1)
        for k in np.arange(1, n_ma + 1):
            psi[k] = psi[k - 1] * (k - 1.0 + d) / k
        u = fftconvolve(eps, psi[None, :], mode='valid', axes=1)  # shape (n_paths, n_total)
    if np.isclose(phi, 0.0):
        r = u
    else:
        r = np.empty_like(u)
        r[:, 0] = u[:, 0] / np.sqrt(1.0 - phi ** 2)  # stationary start for the ar recursion
        for t in np.arange(1, r.shape[1]):
            r[:, t] = phi * r[:, t - 1] + u[:, t]
    return r + mu_an * dt


def sr_underlying_analytic(mu_an: float,
                           phi: float = 0.0,
                           d: float = 0.0
                           ) -> float:
    """
    annualised sharpe of the vol-normalised returns implied by the process: sr_z = mu_an / sqrt(gamma_0)
    gamma_0 is the process variance under unit-variance innovations
    """
    if np.isclose(d, 0.0):
        gamma0 = 1.0 / (1.0 - phi ** 2)
    else:
        from scipy.special import gamma as sp_gamma, hyp2f1
        c0 = sp_gamma(1.0 - 2.0 * d) / np.square(sp_gamma(1.0 - d))
        if np.isclose(phi, 0.0):
            gamma0 = c0
        else:
            # sowell variance of arfima(1,d,0): V_{phi,d} = gamma0_tilde * F(1, 1+d; 1-d; phi) / (1+phi)
            # FLAG: the previous expression c0*(2F(1,d,1-d;phi)-1)/((1-phi)F(1,1+d,1-d;phi)) reduces
            # identically to c0 by the hypergeometric identity 2F(1,d,1-d;x)-1=(1-x)F(1,1+d,1-d;x),
            # so it silently ignored phi; verified against the direct acf double sum and mc variance
            gamma0 = c0 * hyp2f1(1.0, 1.0 + d, 1.0 - d, phi) / (1.0 + phi)
    return mu_an / np.sqrt(gamma0)


def compute_vol_norm_returns_mc(returns: np.ndarray,
                                vol_span: int = VOL_SPAN,
                                return_vols: bool = False  # also return the post-update vols sigma_t
                                ) -> np.ndarray:
    """
    z_t = r_t / sigma_{t-1} with ewma variance sigma^2_t = (1-nu)*r_t^2 + nu*sigma^2_{t-1}, lagged one day
    """
    nu = span_to_nu(vol_span)
    n_paths, n_total = returns.shape
    var = np.full(n_paths, np.mean(np.square(returns[:, :vol_span]), axis=1))  # warm start at short-sample variance
    z = np.empty_like(returns)
    vols = np.empty_like(returns) if return_vols else None
    for t in np.arange(n_total):
        z[:, t] = returns[:, t] / np.sqrt(var)
        var = (1.0 - nu) * np.square(returns[:, t]) + nu * var
        if return_vols:
            vols[:, t] = np.sqrt(var)
    if return_vols:
        return z, vols
    return z


def compute_signal_mc(z: np.ndarray,
                      long_span: float,
                      short_span: Optional[float] = None
                      ) -> np.ndarray:
    """
    variance-preserving (long-short) ewma signal S_t = l1*L1_t - l2*L2_t on vol-normalised returns
    """
    l1, l2 = compute_ewm_long_short_weights(long_span=long_span, short_span=short_span)
    nu1 = span_to_nu(long_span)
    n_paths, n_total = z.shape
    ewma1 = np.zeros(n_paths)
    signal = np.empty_like(z)
    if short_span is None:
        for t in np.arange(n_total):
            ewma1 = (1.0 - nu1) * z[:, t] + nu1 * ewma1
            signal[:, t] = l1 * ewma1
    else:
        nu2 = span_to_nu(short_span)
        ewma2 = np.zeros(n_paths)
        for t in np.arange(n_total):
            ewma1 = (1.0 - nu1) * z[:, t] + nu1 * ewma1
            ewma2 = (1.0 - nu2) * z[:, t] + nu2 * ewma2
            signal[:, t] = l1 * ewma1 - l2 * ewma2
    return signal


def compute_strategy_returns_mc(z: np.ndarray,
                                signal: np.ndarray
                                ) -> np.ndarray:
    """
    f_t = (sigma_target/sqrt(af)) * S_{t-1} * z_t, burn-in removed
    """
    f = (SIGMA_TARGET / np.sqrt(AF)) * signal[:, :-1] * z[:, 1:]
    return f[:, BURN:]


def estimate_gross_net_sharpe_mc(returns: np.ndarray,
                                 long_span: float = 250.0,
                                 short_span: Optional[float] = 20.0,
                                 net_cost: float = 0.0020,  # cost per unit of volatility-normalised turnover
                                 ) -> Tuple[float, float, float]:
    """
    pooled gross and net sharpe of the (long-short) system through the full pipeline
    turnover follows eq tur1: U_t = sqrt(a)*sigma_t*|w_t - w_{t-1}| with w_t = S_t*sigma_target/(sqrt(a)*sigma_t)
    returns (sr_gross_pooled, sr_net_pooled, annualised mean turnover)
    """
    z, vols = compute_vol_norm_returns_mc(returns=returns, return_vols=True)
    signal = compute_signal_mc(z=z, long_span=long_span, short_span=short_span)
    f = (SIGMA_TARGET / np.sqrt(AF)) * signal[:, :-1] * z[:, 1:]
    weights = SIGMA_TARGET / np.sqrt(AF) * signal / vols
    u = np.sqrt(AF) * vols[:, 1:] * np.abs(weights[:, 1:] - weights[:, :-1])
    f, u = f[:, BURN:], u[:, BURN:]
    sr_gross = float(np.sqrt(AF) * np.mean(f) / np.std(f))
    sr_net = float(np.sqrt(AF) * (np.mean(f) - net_cost * np.mean(u)) / np.std(f))
    return sr_gross, sr_net, float(AF * np.mean(u))


def estimate_sharpe_mc(f: np.ndarray) -> Tuple[float, float, float, float]:
    """
    pooled sr with a block-based 95% ci, and the mean of per-path srs with its 95% ci
    """
    sr_pooled = np.sqrt(AF) * np.mean(f) / np.std(f)
    sr_paths = np.sqrt(AF) * np.mean(f, axis=1) / np.std(f, axis=1)
    ci = 1.96 * np.std(sr_paths) / np.sqrt(f.shape[0])
    n_blocks = 10
    blocks = np.array_split(np.arange(f.shape[0]), n_blocks)
    sr_blocks = np.array([np.sqrt(AF) * np.mean(f[b]) / np.std(f[b]) for b in blocks])
    ci_pooled = 1.96 * np.std(sr_blocks) / np.sqrt(n_blocks)
    return float(sr_pooled), float(ci_pooled), float(np.mean(sr_paths)), float(ci)


def run_verification(spans: List[float],
                     process_configs: List[Dict],
                     n_paths: int = 1000,
                     n_obs: int = 5200,
                     short_span_cases: Optional[List[Tuple[float, float]]] = None,  # (long, short) pairs
                     base_seed: int = 8,
                     t_dof: Optional[float] = None,  # student-t dof for the innovations, None for gaussian
                     analytic_kappa: Optional[float] = None  # excess kurtosis for an extra analytic column, None to skip
                     ) -> pd.DataFrame:
    """
    analytic vs mc sharpe over the grid of processes and filter spans, one simulation per process reused across spans
    """
    rows = []
    for idx, config in enumerate(process_configs):
        mu_an, phi, d = config['mu_an'], config.get('phi', 0.0), config.get('d', 0.0)
        r = simulate_returns(n_paths=n_paths,
                             n_obs=n_obs,
                             mu_an=mu_an,
                             phi=phi,
                             d=d,
                             seed=base_seed + idx,
                             t_dof=t_dof)
        z = compute_vol_norm_returns_mc(returns=r)
        rho = population_acf(n_lags=2000, phi=phi, d=d)
        psi = ma_weights(phi=phi, d=d) if analytic_kappa is not None else None
        sr_z = sr_underlying_analytic(mu_an=mu_an, phi=phi, d=d)
        z_kept = z[:, BURN:]
        mean_z, var_z = float(np.mean(z_kept)), float(np.var(z_kept))
        sr_z_measured = np.sqrt(AF) * mean_z / np.sqrt(var_z)
        cases = [(span, None) for span in spans]
        if short_span_cases is not None:
            cases += [(ls, ss) for (ls, ss) in short_span_cases]
        for (long_span, short_span) in cases:
            signal = compute_signal_mc(z=z, long_span=long_span, short_span=short_span)
            f = compute_strategy_returns_mc(z=z, signal=signal)
            sr_pooled, ci_pooled, sr_path_mean, ci = estimate_sharpe_mc(f=f)
            sr_analytic = compute_annualised_sharpe(rho=rho,
                                                    long_span=long_span,
                                                    short_span=short_span,
                                                    sr_underlying=sr_z,
                                                    af=AF)
            sr_analytic_matched = compute_annualised_sharpe(rho=rho,
                                                            long_span=long_span,
                                                            short_span=short_span,
                                                            sr_underlying=sr_z_measured,
                                                            variance=var_z,
                                                            af=AF)
            if analytic_kappa is not None:
                sr_analytic_kappa = compute_annualised_sharpe(rho=rho,
                                                              long_span=long_span,
                                                              short_span=short_span,
                                                              sr_underlying=sr_z,
                                                              kappa=analytic_kappa,
                                                              ma_weights=psi,
                                                              af=AF)
            else:
                sr_analytic_kappa = np.nan
            rows.append(dict(process=config['name'],
                             mu_an=mu_an,
                             phi=phi,
                             d=d,
                             long_span=long_span,
                             short_span=short_span if short_span is not None else np.nan,
                             sr_analytic=sr_analytic,
                             sr_analytic_matched=sr_analytic_matched,
                             sr_analytic_kappa=sr_analytic_kappa,
                             sr_mc_pooled=sr_pooled,
                             pooled_ci95=ci_pooled,
                             sr_mc_path_mean=sr_path_mean,
                             path_ci95=ci,
                             abs_error=np.abs(sr_analytic - sr_pooled)))
    return pd.DataFrame(rows)


class LocalTests(Enum):
    VERIFY_SHARPE = 1


def run_local_test(local_test: LocalTests):
    if local_test == LocalTests.VERIFY_SHARPE:
        spans = [5.0, 10.0, 21.0, 63.0, 125.0, 250.0, 500.0]
        process_configs = [dict(name='white_noise', mu_an=0.5),
                           dict(name='white_noise', mu_an=0.25),
                           dict(name='ar1_pos', mu_an=0.0, phi=0.05),
                           dict(name='ar1_neg', mu_an=0.0, phi=-0.05),
                           dict(name='ar1_pos_drift', mu_an=0.5, phi=0.05),
                           dict(name='arfima_trend', mu_an=0.0, d=0.1),
                           dict(name='arfima_mixed', mu_an=0.0, phi=-0.05, d=0.1)]
        df = run_verification(spans=spans,
                              process_configs=process_configs,
                              short_span_cases=[(250.0, 20.0)])
        print(df.to_string(float_format=lambda x: f"{x:0.4f}"))


if __name__ == '__main__':
    run_local_test(local_test=LocalTests.VERIFY_SHARPE)


def plot_verification(df: pd.DataFrame,
                      file_name: Optional[str] = None
                      ) -> 'plt.Figure':
    """
    sr vs filter span: analytic curves and mc pooled estimates with 95% cis, one panel per process family
    """
    import matplotlib.pyplot as plt
    panels = [('wn_mu50', 'White noise, $\\mu^{z}_{an}=0.5$'),
              (('ar1_pos', 'ar1_neg'), 'AR-1, $\\phi=\\pm 0.05$, $\\mu^{z}_{an}=0$'),
              ('arfima_d10', 'ARFIMA(0,d,0), $d=0.1$'),
              ('arfima_d10_ar-05', 'ARFIMA(1,d,0), $d=0.1$, $\\phi=-0.05$')]
    fig, axs = plt.subplots(2, 2, figsize=(14, 8), tight_layout=True)
    for ax, (keys, title) in zip(axs.flatten(), panels):
        keys = (keys,) if isinstance(keys, str) else keys
        for key in keys:
            data = df.loc[(df['process'] == key) & (df['short_span'].isna())].sort_values('long_span')
            ax.plot(data['long_span'], data['sr_analytic'], '-', lw=1.5, label=f"analytic")
            ax.errorbar(data['long_span'], data['sr_mc_pooled'], yerr=data['pooled_ci95'],
                        fmt='o', ms=4, capsize=3, label=f"MC (95% CI)")
        ax.set_xscale('log')
        ax.set_xticks([5, 10, 21, 63, 125, 250, 500])
        ax.set_xticklabels(['1w', '2w', '1m', '3m', '6m', '1y', '2y'])
        ax.axhline(0.0, color='gray', lw=0.5)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel('filter span')
        ax.set_ylabel('annualised Sharpe ratio')
        ax.legend(fontsize=8)
    if file_name is not None:
        fig.savefig(file_name, dpi=160)
    return fig
