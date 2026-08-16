"""
monte carlo path generation for the return processes of the paper: white noise,
ar(p), ma(q), and arfima, with a common seeded interface used by the verification
exhibits
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import qis as qis
from typing import List, Union, Optional
from numba import njit
from statsmodels.graphics.tsaplots import plot_pacf, pacf
from enum import Enum

import trendfollowing.processes.arfima as arfima


@njit
def set_seed(value):
    """
    set seed for numba space
    """
    np.random.seed(value)


class ProcessType(Enum):
    """
    enum of the supported return-generating processes
    """
    WHITE_NOISE = 1
    AR_P = 2
    MA_Q = 3
    ARFIMA = 4


def generate_paths(process_type: ProcessType = ProcessType.AR_P,
                   phi: Union[np.ndarray, float] = None,
                   ar_params: Optional[List[float]] = None,
                   delta: float = 0.1,
                   x0: np.ndarray = None,
                   n_path: int = 1,
                   m_times: int = 100,
                   mean: float = 0.0,
                   noise_std: float = 1.0,
                   dt: float = 1.0
                   ) -> np.ndarray:

    """
    dispatch the path simulation by process type with common shape and seed handling
    """
    if ar_params is None:
        ar_params = [0.0]
    if process_type == ProcessType.WHITE_NOISE:
        paths = simulate_white_noise_paths(x0=x0,
                                           n_path=n_path,
                                           m_times=m_times,
                                           mean=mean,
                                           noise_std=noise_std,
                                           dt=dt)
    elif process_type == ProcessType.AR_P:
        paths = simulate_ar_p_paths(phi=phi,
                                    x0=x0,
                                    n_path=n_path,
                                    m_times=m_times,
                                    mean=mean,
                                    noise_std=noise_std,
                                    dt=dt)

    elif process_type == ProcessType.MA_Q:
        paths = simulate_ma_q_paths(phi=phi,
                                    x0=x0,
                                    n_path=n_path,
                                    m_times=m_times,
                                    drift=mean,
                                    noise_std=noise_std,
                                    dt=dt)

    elif process_type == ProcessType.ARFIMA:
        paths = simulate_arfima_paths(ar_params=ar_params,
                                      d=delta,
                                      n_path=n_path,
                                      m_times=m_times,
                                      mean=mean,
                                      noise_std=noise_std,
                                      dt=dt)
    else:
        raise NotImplementedError

    return paths


@njit
def simulate_white_noise_paths(x0: np.ndarray = None,
                               n_path: int = 1,
                               m_times: int = 100,
                               mean: float = 0.0,
                               noise_std: float = 1.0,
                               dt: float = 1.0
                               ) -> np.ndarray:
    """
    white noise returns
    """
    noise = np.sqrt(dt)*np.random.normal(0.0, noise_std, size=(m_times, n_path))
    drift_dt = mean * dt
    xt = drift_dt + noise
    return xt


@njit
def simulate_ar_p_paths(phi: np.ndarray,
                        x0: np.ndarray = None,
                        n_path: int = 1,
                        m_times: int = 100,
                        mean: float = 0.0,
                        noise_std: float = 1.0,
                        dt: float = 1.0
                        ) -> np.ndarray:

    """
    simulate ar(p) paths x_t = c + sum_i phi_i x_{t-i} + noise_std eps_t
    """
    noise = np.sqrt(dt)*np.random.normal(0.0, noise_std, size=(m_times, n_path))
    drift_dt = mean * dt
    p = phi.shape[0]
    if x0 is None:
        x0 = np.zeros(p)

    xt = np.zeros((m_times, n_path))
    for path in range(n_path):
        xt[:p, path] = x0

    phi_ = np.ascontiguousarray(phi[::-1].T)  # revert, diable NumbaPerformanceWarning
    for t in np.arange(p, m_times):
        xt[t, :] = drift_dt + phi_ @ np.ascontiguousarray(xt[t-p: t, :]) + noise[t, :]

    return xt


@njit
def simulate_ma_q_paths(phi: np.ndarray,
                        x0: np.ndarray = None,
                        n_path: int = 1,
                        m_times: int = 100,
                        mean: float = 0.0,
                        noise_std: float = 1.0,
                        dt: float = 1.0
                        ) -> np.ndarray:

    """
    simulate ma(q) paths x_t = c + eps_t + sum_i theta_i eps_{t-i}
    """
    noise = np.sqrt(dt)*np.random.normal(0.0, noise_std, size=(m_times, n_path))
    drift_dt = mean * dt
    p = phi.shape[0]
    if x0 is None:
        x0 = np.zeros(p)

    xt = np.zeros((m_times, n_path))
    for path in range(n_path):
        xt[:p, path] = x0

    phi_ = np.ascontiguousarray(phi[::-1].T)  # revert, diable NumbaPerformanceWarning
    for t in np.arange(p, m_times):
        xt[t, :] = drift_dt + phi_ @ np.ascontiguousarray(noise[t-p: t, :]) + noise[t, :]

    return xt


def simulate_arfima_paths(ar_params: Optional[List[float]] = None,
                          d: float = 0.15,
                          n_path: int = 1,
                          m_times: int = 100,
                          mean: float = 0.0,
                          noise_std: float = 1.0,
                          dt: float = 1.0
                          ) -> np.ndarray:

    """
    simulate arfima(p,d,q) paths via the fractional-differencing engine of processes.arfima
    """
    noise = np.zeros((m_times, n_path))
    drift_dt = mean * dt
    for n in range(n_path):
        noise[:, n] = arfima.arfima(ar_params=ar_params, d=d, ma_params=[], n_points=m_times, warmup=2 ** 16)
    xt = drift_dt + np.sqrt(dt)*noise_std*noise
    return xt


class LocalTests(Enum):
    """
    runnable example cases
    """
    AR1 = 1
    ARFIMA = 2


def run_local_test(local_test: LocalTests):
    """Run local tests for development and debugging purposes.

    These are integration tests that download real data and generate reports.
    Use for quick verification during development.
    """

    set_seed(1)
    n_path = 100
    m_times = 1000
    n_path_cut = 20

    if local_test == LocalTests.AR1:
        phi = np.array([0.5])
        x0 = np.array([0.0])
        #phi = np.array([-0.6, 0.3])
        #x0 = np.array([0.0, 0.0])

        paths = simulate_ar_p_paths(phi=phi,
                                    x0=x0,
                                    n_path=n_path,
                                    m_times=m_times,
                                    mean=0.0,
                                    noise_std=1.0)

    elif local_test == LocalTests.ARFIMA:
        paths = simulate_arfima_paths(ar_params=[0.0],
                                      d=0.1,
                                      n_path=n_path,
                                      m_times=m_times,
                                      mean=0.0,
                                      noise_std=1.0)

    else:
        raise NotImplementedError

    acfs, m_acf, std_acf = qis.estimate_acf_from_paths(paths=paths, is_pacf=True)
    print(acfs)
    print(m_acf)
    print(std_acf)

    paths = pd.DataFrame(paths, columns=[f"path{p + 1}" for p in range(n_path)])

    fig, axs = plt.subplots(2, 2, figsize=(18, 10), tight_layout=True)
    qis.plot_line(df=paths.iloc[:, :n_path_cut], ax=axs[0][0])
    qis.plot_histogram(df=paths.iloc[:, :n_path_cut], ax=axs[0][1])
    plot_pacf(paths.iloc[:, 0], lags=10, title=f"path0", ax=axs[1][0])
    # peb.errorbar(df=m_acf, y_std_errors=std_acf, var_format='{:.2%}', ax=axs[1][1])
    qis.df_boxplot_by_index(df=acfs, ax=axs[1][1])
    print(pacf(paths.iloc[:, 0], nlags=10))

    plt.show()


if __name__ == '__main__':

    run_local_test(local_test=LocalTests.ARFIMA)
