"""
filter impulse-response figure of the paper: propagation of a unit impulse through (long-short) ewma filters
the figure is saved as signal_weight, matching the paper exhibit
"""
# packages
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from enum import Enum
from typing import Optional
# qis
import qis as qis


def plot_filter_weights(local_path: Optional[str] = None) -> plt.Figure:
    """
    plot the propagation of a unit impulse at t=1 through ewma filters with spans (50), (250), and long-short (250, 50)
    the figure is saved with file name signal_weight when local_path is provided
    """
    data = np.zeros(500)
    data[1] = 1.0
    data = pd.Series(data)
    ds1 = qis.compute_ewm_long_short_filter(data=data, long_span=50, short_span=None, warmup_period=None).rename(f"short span=0, long span=50")
    ds2 = qis.compute_ewm_long_short_filter(data=data, long_span=250, short_span=None, warmup_period=None).rename(f"short span=0, long span=250")
    ds3 = qis.compute_ewm_long_short_filter(data=data, long_span=250, short_span=50, warmup_period=None).rename(f"short span=50, long span=250")
    df = pd.concat([ds1, ds2, ds3], axis=1)
    df.iloc[0, :] = np.nan
    with sns.axes_style("darkgrid"):
        fig, ax = plt.subplots(1, 1, figsize=(11, 5), tight_layout=True)
        qis.plot_line(df=df,
                      y_limits=(0.0, None),
                      x_limits=(0.0, None),
                      title=f"Propagation of unit impulse at time t=1",
                      xlabel='number of periods after t=1',
                      ylabel='Filter value',
                      fontsize=12,
                      framealpha=0.9,
                      ax=ax)
    if local_path is not None:
        qis.save_fig(fig, file_name='signal_weight', local_path=local_path)
    return fig


class LocalTests(Enum):
    FILTER_WEIGHTS = 1


def run_local_test(local_test: LocalTests):
    local_path = os.environ.get("TF_FIGURE_PATH", qis.local_path.get_output_path())  # set TF_FIGURE_PATH to the paper figures folder
    if local_test == LocalTests.FILTER_WEIGHTS:
        plot_filter_weights(local_path=local_path)
        plt.show()


if __name__ == '__main__':
    run_local_test(local_test=LocalTests.FILTER_WEIGHTS)
