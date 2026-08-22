"""Development runner for simulated return paths."""

from enum import Enum

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import qis as qis
from statsmodels.graphics.tsaplots import pacf, plot_pacf

from trendfollowing.processes.path_engine import (
    set_seed,
    simulate_ar_p_paths,
    simulate_arfima_paths,
)


class Locals(Enum):
    """Runnable path-simulation development cases."""

    AR1 = 1
    ARFIMA = 2


def run_local(local: Locals) -> None:
    """Run the selected local path-simulation workflow."""
    set_seed(1)
    n_path = 100
    m_times = 1000
    n_path_cut = 20

    if local == Locals.AR1:
        phi = np.array([0.5])
        x0 = np.array([0.0])
        paths = simulate_ar_p_paths(
            phi=phi, x0=x0, n_path=n_path, m_times=m_times, mean=0.0, noise_std=1.0
        )
    elif local == Locals.ARFIMA:
        paths = simulate_arfima_paths(
            ar_params=[0.0], d=0.1, n_path=n_path, m_times=m_times, mean=0.0, noise_std=1.0
        )
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
    plot_pacf(paths.iloc[:, 0], lags=10, title="path0", ax=axs[1][0])
    qis.df_boxplot_by_index(df=acfs, ax=axs[1][1])
    print(pacf(paths.iloc[:, 0], nlags=10))
    plt.show()


if __name__ == '__main__':
    run_local(local=Locals.ARFIMA)
