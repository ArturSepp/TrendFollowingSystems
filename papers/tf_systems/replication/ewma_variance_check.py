"""
verify the moment structure of the EWMA-of-squared-strategy-returns proposal for the TF Sharpe ratio
objects checked per (innovation, phi, span):
  1) E[V_t] = E[p_t^2] where V_t = EWMA_nu(p^2) and p_t = S_{t-1} z_t  (linearity claim, distribution-free)
  2) Gaussian analytic E[p^2] = B_nu + 2 A_nu^2  (Isserlis, prop:dailyvar with mu=0, theta=1)
  3) Student-t analytic E[p^2] = Gaussian + Delta, Delta = kappa (1-nu)^2 sum nu^{i+j} kappa4(z_t,z_t,z_{t-1-i},z_{t-1-j})
  4) self-normalised Sharpe of q_t = p_t / sqrt(V_{t-1})  vs the analytic SR and vs the sign-system benchmark
notation follows the manuscript: nu = 1 - 2/(span+1), S = unit-mass EWMA, A_nu, B_nu of eq:sr_ab
"""
# packages
import numpy as np
from scipy.signal import lfilter
from typing import Tuple, Dict

A_DAYS = 260  # annualisation factor, trading days per year
SEED = 8


def analytic_moments(nu: float, phi: float) -> Dict[str, float]:
    """closed-form A_nu, B_nu, E[p], Var[p], E[p^2] under as:gauss with mu=0, theta=1, AR-1 acf rho(m)=phi^m"""
    psi = nu * phi / (1.0 - nu * phi)  # Psi_nu for AR-1
    a_nu = (1.0 - nu) / nu * psi
    b_nu = (1.0 - nu) / (1.0 + nu) * (1.0 + 2.0 * psi)
    e_p = a_nu
    var_p = b_nu + a_nu ** 2
    e_p2 = b_nu + 2.0 * a_nu ** 2
    return dict(a_nu=a_nu, b_nu=b_nu, e_p=e_p, var_p=var_p, e_p2=e_p2)


def kappa4_correction(nu: float, phi: float, kappa_eps: float, n_lags: int = 800) -> float:
    """Delta = kappa*(1-nu)^2 sum_{i,j} nu^{i+j} k4(z_t,z_t,z_{t-1-i},z_{t-1-j}) for AR-1 with iid innovations
    k4 for the linear process z_t = sum_s psi_s eps_{t-s}, psi_s = sqrt(1-phi^2) phi^s:
    k4(i,j) = kappa_eps * sum_{s>=1+max(i,j)} psi_s^2 psi_{s-1-i} psi_{s-1-j}
            = kappa_eps * (1-phi^2)/(1+phi^2) * phi^{2 + 4*max(i,j) - i - j}
    the double sum over (i,j) is evaluated numerically on a truncated grid
    """
    ii, jj = np.meshgrid(np.arange(n_lags), np.arange(n_lags), indexing='ij')
    mx = np.maximum(ii, jj)
    log_terms = (ii + jj) * np.log(nu) + (2 + 4 * mx - ii - jj) * np.log(phi)
    grid = np.exp(log_terms)
    k4_scale = kappa_eps * (1.0 - phi ** 2) / (1.0 + phi ** 2)
    return float((1.0 - nu) ** 2 * k4_scale * grid.sum())


def kappa4_direct_check(nu: float, phi: float, kappa_eps: float) -> float:
    """brute-force psi-sum version of k4(i,j) on a small grid as a cross-check of the closed inner form"""
    n_i, n_s = 120, 4000
    psi = np.sqrt(1.0 - phi ** 2) * phi ** np.arange(n_s)
    total = 0.0
    for i in range(n_i):
        for j in range(n_i):
            s0 = 1 + max(i, j)
            k4 = kappa_eps * np.sum(psi[s0:] ** 2 * psi[s0 - 1 - i:n_s - 1 - i] * psi[s0 - 1 - j:n_s - 1 - j])
            total += nu ** (i + j) * k4
    return float((1.0 - nu) ** 2 * total)


def simulate_config(phi: float,
                    span: int,
                    innovation: str,  # 'gauss' or 't6'
                    n_paths: int = 1000,
                    n_obs: int = 13000,  # kept observations per path, matching the paper config
                    n_burn: int = 3000,
                    chunk: int = 1000,
                    rng_seed: int = SEED,
                    ) -> Dict[str, float]:
    """pooled MC moments of p, p^2, V=EWMA(p^2), q=p/sqrt(V_lag), and the sign system, with 10-block CIs"""
    nu = 1.0 - 2.0 / (span + 1.0)
    df = 6.0
    rng = np.random.default_rng(rng_seed)
    t_total = n_burn + n_obs
    block_means_p, block_means_p2, block_means_v, block_means_q = [], [], [], []
    sum_q, sum_q2, sum_sgn, sum_sgn2, n_kept = 0.0, 0.0, 0.0, 0.0, 0
    for start in range(0, n_paths, chunk):
        n_c = min(chunk, n_paths - start)
        if innovation == 'gauss':
            eps = rng.standard_normal((n_c, t_total))
        else:
            eps = rng.standard_t(df, size=(n_c, t_total)) * np.sqrt((df - 2.0) / df)  # unit-variance t
        z = lfilter([np.sqrt(1.0 - phi ** 2)], [1.0, -phi], eps, axis=1)  # unit-variance AR-1
        s = lfilter([1.0 - nu], [1.0, -nu], z, axis=1)  # unit-mass EWMA signal
        p = np.empty_like(z)
        p[:, 0] = 0.0
        p[:, 1:] = s[:, :-1] * z[:, 1:]  # daily strategy return kernel, l*sigma scale set to 1
        v = lfilter([1.0 - nu], [1.0, -nu], p ** 2, axis=1)  # same-span EWMA of squared strategy returns
        q = np.empty_like(p)
        q[:, 0] = 0.0
        q[:, 1:] = p[:, 1:] / np.sqrt(v[:, :-1])  # self-normalised return
        sgn = np.sign(s)
        p_sgn = np.empty_like(p)
        p_sgn[:, 0] = 0.0
        p_sgn[:, 1:] = sgn[:, :-1] * z[:, 1:]  # binary (sign) system on the same signal
        kp, kp2, kv, kq, ksgn = (x[:, n_burn:] for x in (p, p ** 2, v, q, p_sgn))
        n_blocks_chunk = max(1, n_c // 100)
        for b in range(n_blocks_chunk):
            sl = slice(b * 100, (b + 1) * 100)
            block_means_p.append(kp[sl].mean())
            block_means_p2.append(kp2[sl].mean())
            block_means_v.append(kv[sl].mean())
            block_means_q.append(kq[sl].mean())
        sum_q += kq.sum()
        sum_q2 += (kq ** 2).sum()
        sum_sgn += ksgn.sum()
        sum_sgn2 += (ksgn ** 2).sum()
        n_kept += kp.size
    bp, bp2, bv, bq = (np.array(x) for x in (block_means_p, block_means_p2, block_means_v, block_means_q))
    nb = len(bp)
    mean_q = sum_q / n_kept
    std_q = np.sqrt(sum_q2 / n_kept - mean_q ** 2)
    mean_sgn = sum_sgn / n_kept
    std_sgn = np.sqrt(sum_sgn2 / n_kept - mean_sgn ** 2)
    return dict(nu=nu,
                mc_e_p=bp.mean(), ci_p=1.96 * bp.std(ddof=1) / np.sqrt(nb),
                mc_e_p2=bp2.mean(), ci_p2=1.96 * bp2.std(ddof=1) / np.sqrt(nb),
                mc_e_v=bv.mean(), ci_v=1.96 * bv.std(ddof=1) / np.sqrt(nb),
                sr_selfnorm=np.sqrt(A_DAYS) * mean_q / std_q,
                sr_sign=np.sqrt(A_DAYS) * mean_sgn / std_sgn)


def run_all() -> None:
    print(f"{'innov':6s} {'phi':>5s} {'span':>4s} | {'E[p] an':>9s} {'E[p] mc':>9s} | "
          f"{'E[p2] an':>9s} {'E[p2] mc':>9s} {'E[V] mc':>9s} | {'SR an':>6s} {'SR_q mc':>7s} {'SR_sgn mc':>9s} {'SR_sgn an':>9s}")
    configs = [('gauss', 0.05, 21, 1000), ('t6', 0.05, 21, 1000),
               ('gauss', 0.05, 250, 1000), ('t6', 0.05, 250, 1000),
               ('gauss', 0.20, 21, 4000), ('t6', 0.20, 21, 4000)]
    for innov, phi, span, n_paths in configs:
        nu = 1.0 - 2.0 / (span + 1.0)
        an = analytic_moments(nu=nu, phi=phi)
        e_p2_an = an['e_p2']
        if innov == 't6':
            e_p2_an += kappa4_correction(nu=nu, phi=phi, kappa_eps=3.0)
        sr_an = np.sqrt(A_DAYS) * an['e_p'] / np.sqrt(an['var_p'])
        sr_sign_an = np.sqrt(A_DAYS) * np.sqrt(2.0 / np.pi) * an['a_nu'] / np.sqrt(an['b_nu'])  # Price theorem, Gaussian
        mc = simulate_config(phi=phi, span=span, innovation=innov, n_paths=n_paths)
        print(f"{innov:6s} {phi:5.2f} {span:4d} | {an['e_p']:9.5f} {mc['mc_e_p']:9.5f} | "
              f"{e_p2_an:9.5f} {mc['mc_e_p2']:9.5f} {mc['mc_e_v']:9.5f} | "
              f"{sr_an:6.3f} {mc['sr_selfnorm']:7.3f} {mc['sr_sign']:9.3f} {sr_sign_an:9.3f}")
        print(f"{'':29s} ci(p)={mc['ci_p']:.5f} ci(p2)={mc['ci_p2']:.5f} ci(V)={mc['ci_v']:.5f}")
    d_num = kappa4_correction(nu=1.0 - 2.0 / 22.0, phi=0.20, kappa_eps=3.0)
    d_direct = kappa4_direct_check(nu=1.0 - 2.0 / 22.0, phi=0.20, kappa_eps=3.0)
    print(f"\nkappa4 correction cross-check at phi=0.20, span=21: grid={d_num:.6f}, direct psi-sum={d_direct:.6f}")


if __name__ == '__main__':
    run_all()


def k_loading_series(nu: float, psi: np.ndarray) -> float:
    """general kurtosis loading K_nu = sum_{s>=1} psi_s^2 c_{s-1}^2 with c_u = (1-nu) sum_{m<=u} nu^m psi_{u-m}"""
    c = (1.0 - nu) * lfilter([1.0], [1.0, -nu], psi)  # c_u, ewma convolution of the ma weights
    return float(np.sum(psi[1:] ** 2 * c[:-1] ** 2))


def k_loading_ar1(nu: float, phi: float) -> float:
    """closed form of K_nu for the AR-1 process with psi_s = sqrt(1-phi^2) phi^s"""
    bracket = (phi ** 4 / (1.0 - phi ** 4)
               - 2.0 * nu * phi ** 3 / (1.0 - nu * phi ** 3)
               + nu ** 2 * phi ** 2 / (1.0 - nu ** 2 * phi ** 2))
    return (1.0 - nu) ** 2 * (1.0 - phi ** 2) ** 2 / (phi - nu) ** 2 * bracket


def run_k_table() -> None:
    """closed form vs series vs kappa4 grid, and relative sr effect kappa*K/(2*(B+A^2)) across paper spans"""
    print(f"\n{'span':>5s} {'K series':>12s} {'K closed':>12s} {'K grid/kappa':>12s} {'sr effect %':>11s}")
    phi, kappa = 0.05, 3.0
    for span in [5, 10, 21, 42, 63, 125, 250]:
        nu = 1.0 - 2.0 / (span + 1.0)
        psi = np.sqrt(1.0 - phi ** 2) * phi ** np.arange(4000)
        k_series = k_loading_series(nu=nu, psi=psi)
        k_closed = k_loading_ar1(nu=nu, phi=phi)
        k_grid = kappa4_correction(nu=nu, phi=phi, kappa_eps=1.0)  # unit kappa gives K on the grid
        an = analytic_moments(nu=nu, phi=phi)
        sr_effect = 100.0 * 0.5 * kappa * k_closed / (an['b_nu'] + an['a_nu'] ** 2)
        print(f"{span:5d} {k_series:12.3e} {k_closed:12.3e} {k_grid:12.3e} {sr_effect:11.3f}")
    k_stress = k_loading_ar1(nu=1.0 - 2.0 / 22.0, phi=0.20)
    print(f"stress phi=0.20 span=21: kappa*K closed = {3.0 * k_stress:.6f} (mc-verified grid: 0.000961)")


run_k_table()
