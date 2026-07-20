"""
numerical check of the inverse-volatility moments under gaussian returns: compares
the monte carlo mean and variance of the reciprocal realized volatility with the
closed-form inverse-chi moments, which quantifies the attenuation from volatility
normalization
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import qis as qis
from scipy.special import gamma


if __name__ == '__main__':
    n = 240
    n_path = 100000
    x = np.random.normal(0.0, 1.0, size=(n, n_path))
    x2 = np.square(x)
    vol_bar = 0.15
    scale = vol_bar / np.sqrt(n)
    vol = scale*np.sqrt(np.sum(x2, axis=0))
    inv_vol = 1.0 / vol
    qis.plot_histogram(df=pd.Series(inv_vol))
    print(f"e_mc={np.mean(inv_vol)}, var_mc={np.var(inv_vol)}")
    e_an = (1.0/scale)*np.sqrt(0.5)*gamma(n/2.0-0.5)/gamma(n/2)
    var_an = (1.0/scale)**2/(n-2.0) - e_an**2
    print(f"e_an={e_an}, var_an={var_an}, e_an_limit={1.0/vol_bar}")
    plt.show()
