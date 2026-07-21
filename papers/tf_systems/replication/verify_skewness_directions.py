"""
mc verification of the direction claims in the skewness subsection: positive
autocorrelation and long memory raise the aggregated skewness profile, short-term
mean reversion lowers it, and the hump shape is preserved (span 20, horizons to one year)
runtime: about five minutes
"""
# packages
import numpy as np
from scipy.signal import fftconvolve
# project
from trendfollowing.analytics.filters import span_to_nu
from trendfollowing.analytics.autocorrelation import ma_weights
from trendfollowing.analytics.skewness import skewness_white_noise

SPAN = 20.0
HORIZONS = np.array([5, 11, 20, 60, 250])
SEED = 7


def aggregated_skew(z_panel: np.ndarray, span: float, horizons: np.ndarray) -> np.ndarray:
    """aggregated skewness at the horizons, standardised by the realised variance"""
    nu = span_to_nu(span=span)
    sd_ew = np.sqrt((1.0 - nu) / (1.0 + nu))
    n, steps = z_panel.shape
    warm = int(8 * span)
    ew = np.zeros(n)
    cum = np.zeros(n)
    out = {}
    for t in range(steps):
        if t >= warm:
            cum += (ew / sd_ew) * z_panel[:, t]
            k = t - warm + 1
            if k in set(horizons.tolist()):
                c = cum - cum.mean()
                out[k] = float((c ** 3).mean() / c.std() ** 3)
        ew = nu * ew + (1.0 - nu) * z_panel[:, t]
    return np.array([out[int(k)] for k in horizons])


def cost_invariance_check() -> None:
    """manuscript claim: a 100bp cost rate changes the white-noise skewness by less than 0.002"""
    span = 100.0
    nu = span_to_nu(span=span)
    sd_ew = np.sqrt((1.0 - nu) / (1.0 + nu))
    n = 200_000
    horizons = [10, 55, 250]
    skews = {}
    for cost_rate in [0.0, 0.0100]:  # zero and 100bp per unit of volatility-normalized turnover
        rng = np.random.RandomState(77)  # identical innovations across cost levels
        ew = np.zeros(n)
        for _ in range(int(8 * span)):
            ew = nu * ew + (1.0 - nu) * rng.randn(n)
        cum = np.zeros(n)
        prev_s = ew / sd_ew
        res = {}
        for t in range(1, max(horizons) + 1):
            z = rng.randn(n)
            s_now = ew / sd_ew
            cum += s_now * z - cost_rate * np.abs(s_now - prev_s)
            prev_s = s_now
            ew = nu * ew + (1.0 - nu) * z
            if t in horizons:
                c = cum - cum.mean()
                res[t] = float((c ** 3).mean() / c.std() ** 3)
        skews[cost_rate] = res
    diffs = [abs(skews[0.0100][t] - skews[0.0][t]) for t in horizons]
    print("cost invariance: max |skew(100bp) - skew(0)| =", round(max(diffs), 5))
    assert max(diffs) < 0.002, "costs should leave the skewness almost unchanged"


def run_verification() -> None:
    steps = int(8 * SPAN) + int(HORIZONS.max())
    rng = np.random.RandomState(SEED)
    wn_closed = skewness_white_noise(horizon=HORIZONS, span=SPAN)
    print("horizons:", HORIZONS, "| white-noise closed form:", np.round(wn_closed, 3))

    results = {}
    for phi in [0.05, -0.05]:
        z = np.empty((120_000, steps))
        eps = rng.randn(120_000, steps)
        z[:, 0] = eps[:, 0] / np.sqrt(1 - phi * phi)
        for t in range(1, steps):
            z[:, t] = phi * z[:, t - 1] + eps[:, t]
        results[f"ar1({phi:+0.2f})"] = aggregated_skew(z_panel=z, span=SPAN, horizons=HORIZONS)
        del z, eps

    psi = ma_weights(phi=0.0, d=0.1, n_lags=300)
    blocks = []
    for _ in range(6):
        eps = rng.randn(30_000, steps + 300)
        blocks.append(fftconvolve(eps, psi[None, :], mode='full', axes=1)[:, 300:300 + steps])
        del eps
    z = np.concatenate(blocks)
    del blocks
    results["arfima(d=0.1)"] = aggregated_skew(z_panel=z, span=SPAN, horizons=HORIZONS)
    del z

    for name, skews in results.items():
        print(f"{name}: {np.round(skews, 3)}  (diff to wn: {np.round(skews - wn_closed, 3)})")

    tol = 0.06  # mc tolerance at these path counts
    assert np.all(results["ar1(-0.05)"] - wn_closed < tol), "mean reversion should lower the profile"
    assert np.all((results["ar1(+0.05)"] - wn_closed)[1:] > -tol), "positive autocorrelation should raise the profile"
    assert np.all(results["arfima(d=0.1)"] - wn_closed > 0.0), "long memory should raise the profile"
    for skews in results.values():
        assert skews[1] > skews[0] - tol and skews[1] > skews[-1], "hump shape should be preserved"
    print("all direction checks passed")


def portfolio_skewness_decomposition() -> None:
    """manuscript claims for the sg-figure paragraph: ls(250,20) theory 1.7 at quarterly,
    full-sample portfolio near theory, post-2000 sample well below (requires the packaged data)"""
    import pandas as pd
    import qis
    from trendfollowing.universe import load_data
    from trendfollowing.analytics.filters import compute_ewm_long_short_weights
    from trendfollowing.analytics.skewness import aggregated_third_moment_white_noise

    w_l, w_s = compute_ewm_long_short_weights(long_span=250.0, short_span=20.0)
    nu_l, nu_s = span_to_nu(span=250.0), span_to_nu(span=20.0)
    h = np.arange(1, 8001)
    w = w_l * (1 - nu_l) * nu_l ** (h - 1) - w_s * (1 - nu_s) * nu_s ** (h - 1)
    r = np.array([np.sum(w[:len(w) - k] * w[k:]) for k in h])
    theory_q = aggregated_third_moment_white_noise(signal_weights=w, signal_acf=r, horizon=63) / 63 ** 1.5
    print(f"ls(250,20) white-noise quarterly skewness: {theory_q:0.3f}")
    assert 1.5 < theory_q < 1.9

    prices = load_data()[0]
    f_all = {}
    for ticker in prices.columns:
        ret = qis.to_returns(prices=prices[ticker].dropna(), is_log_returns=False)  # arithmetic daily returns
        vol = np.sqrt(qis.compute_ewm(data=np.square(ret), span=33))
        z = (ret / vol.shift(1)).iloc[250:].dropna()
        sig = w_l * qis.compute_ewm(data=z, span=250.0) - w_s * qis.compute_ewm(data=z, span=20.0)
        f_all[ticker] = (sig.shift(1) * z).iloc[750:].dropna()
    fp = pd.DataFrame(f_all).mean(axis=1).dropna()

    def skew_of(x):
        c = x - x.mean()
        return float((c ** 3).mean() / c.std() ** 3)

    full = skew_of(fp.rolling(63).sum().dropna())
    sub = skew_of(fp.loc['2000-01-01':].rolling(63).sum().dropna())
    print(f"portfolio quarterly skewness: full sample {full:0.2f}, post-2000 {sub:0.2f}")
    assert abs(full - theory_q) < 0.5, "full-sample portfolio should sit near the ls theory"
    assert sub < 0.5 * full, "the post-2000 sample should realize well below the full history"


if __name__ == '__main__':
    run_verification()
    cost_invariance_check()
    portfolio_skewness_decomposition()
