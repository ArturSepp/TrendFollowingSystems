"""
exploratory trading of simulated ar(p) processes: the pnl of the one-step ar
forecast with linear or sign sizing, with pacf diagnostics of the simulated paths
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
# packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from enum import Enum
from numba import njit
from statsmodels.graphics.tsaplots import plot_pacf, pacf

# qis
import qis

# internal projects
from trendfollowing.processes.path_engine import set_seed, simulate_ar_p_paths


@njit
def trade_ar1(xt: np.ndarray,
              phi: np.ndarray,
              is_ar_sizing: bool = True
              ) -> np.ndarray:
    """
    cumulative pnl of trading the one-step ar(p) forecast on each path, with the
    size equal to the forecast (linear sizing) or its sign
    """
    m_times, n_path = xt.shape
    p = phi.shape[0]
    phi_ = np.ascontiguousarray(phi[::-1].T)  # revert, diable NumbaPerformanceWarning
    pnl = np.zeros((m_times, n_path))

    for t in np.arange(p, m_times):
        forecast_1 = phi_ @ np.ascontiguousarray(xt[t-p: t, :])
        if is_ar_sizing:
            size = forecast_1
        else:
            size = np.sign(forecast_1)
        pnl[t, :] = pnl[t-1, :] + size * xt[t, :]

    return pnl


def sharpe_ratio(pnl: np.ndarray) -> np.ndarray:
    """
    annualized sharpe ratio of the pnl increments per path, sqrt(252) mean over std
    """
    diff_pnl = pnl[1:] - pnl[:-1]
    stdev = np.std(diff_pnl, axis=0)
    mean = np.mean(diff_pnl, axis=0)
    return np.sqrt(252) * mean / stdev


class LocalTests(Enum):
    """
    runnable example cases
    """
    AR1 = 1
    TRADE_AR1 = 2
    OU_SECONDS_PATHS = 3
    OU_DAILY_PATHS = 4


def run_local_test(local_test: LocalTests):
    """Run local tests for development and debugging purposes.

    These are integration tests that download real data and generate reports.
    Use for quick verification during development.
    """

    set_seed(1)

    if local_test == LocalTests.AR1:
        #phi = np.array([-0.5])
        #x0 = np.array([1.0])
        phi = np.array([-0.6, 0.3])
        x0 = np.array([0.0, 0.0])

        n_path = 100
        n_path_cut = 20
        paths = simulate_ar_p_paths(phi=phi,
                                    x0=x0,
                                    n_path=n_path,
                                    m_times=1000,
                                    c=0.0,
                                    noise_std=1.0)
        acfs, m_acf, std_acf = qis.estimate_acf_from_paths(paths=paths, is_pacf=True)
        paths = pd.DataFrame(paths, columns=[f"path{p+1}" for p in range(n_path)])

        with sns.axes_style("darkgrid"):
            fig, axs = plt.subplots(2, 2, figsize=(18, 10), tight_layout=True)
        qis.plot_line(df=paths.iloc[:, :n_path_cut], ax=axs[0][0])
        qis.plot_histogram(df=paths.iloc[:, :n_path_cut], ax=axs[0][1])
        plot_pacf(paths.iloc[:, 0], lags=10, title=f"path0", ax=axs[1][0])
        # peb.errorbar(df=m_acf, y_std_errors=std_acf, var_format='{:.2%}', ax=axs[1][1])
        qis.df_boxplot_by_index(df=acfs, ax=axs[1][1])
        print(pacf(paths.iloc[:, 0], nlags=10))

    elif local_test == LocalTests.TRADE_AR1:

        #phi1 = -0.4
        #phi = np.array([-0.6, 0.3])

        # phi = np.array([0.5])
        phi = np.array([-0.4, 0.1, 0.1])
        phi = np.array([-0.5, 0.25])

        title = r'$\phi=$(' + ', '.join([f"{x:0.2f}" for x in phi]) + ')'

        n_path = 1000
        m_times = 1000
        xt = simulate_ar_p_paths(phi=phi,
                                 n_path=n_path,
                                 m_times=m_times,
                                 mean=0.0,
                                 noise_std=1.0)

        name1 = 'Forecast Size'
        name2 = 'Sign Size'
        stats = {name1: True, name2: False}
        sharpes = []
        final_pnls = []
        pnls = {}
        for key, is_ar_sizing in stats.items():
            pnl = trade_ar1(xt=xt, phi=phi, is_ar_sizing=is_ar_sizing)
            pnls[key] = pd.DataFrame(pnl[:, :50])
            final_pnls.append(pd.Series(pnl[-1, :], name=key))
            sharpes.append(pd.Series(sharpe_ratio(pnl=pnl), name=key))
        final_pnls = pd.concat(final_pnls, axis=1)
        sharpes = pd.concat(sharpes, axis=1)

        with sns.axes_style("darkgrid"):
            fig, axs = plt.subplots(2, 3, figsize=(18, 10), tight_layout=True)
            fig.suptitle(title)

        kwargs = dict(legend_loc=None)

        acfs, m_acf, std_acf = qis.estimate_acf_from_paths(paths=xt, is_pacf=True)
        qis.df_boxplot_by_index(df=acfs, title='Partial AFC', ylabel=r'$\rho$', y_limits=(-1, 1), ax=axs[0][0])
        acfs, m_acf, std_acf = qis.estimate_acf_from_paths(paths=xt, is_pacf=False)
        qis.df_boxplot_by_index(df=acfs, title='AFC', ylabel=r'$\rho$', y_limits=(-1, 1), ax=axs[1][0])

        qis.plot_line(df=pnls[name1], title=f"P&L path: {name1}", ax=axs[0][1], **kwargs)
        qis.plot_line(df=pnls[name2], title=f"P&L path: {name2}", ax=axs[1][1], **kwargs)

        qis.plot_histogram(df=final_pnls, title='Paths Final P&L', ax=axs[0][2])
        qis.plot_histogram(df=sharpes, title='Paths Sharpe', ax=axs[1][2])

        # fu.save_fig(fig=fig, file_name='ar1_m5p25')

    plt.show()


if __name__ == '__main__':

    local_test = LocalTests.TRADE_AR1

    run_local_test(local_test=local_test)
