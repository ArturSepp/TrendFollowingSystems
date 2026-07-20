"""
mc parts for the redesigned tab:t6: ls(250,20) only, pooled gross (gated against the printed table) and pooled net at c=20bp
each part is independent (per-config seed = 8 + idx), pickled for assembly
usage: python t6_ls_parts.py <idx> <g|t>
"""
# packages
import gc
import sys
import time
import pickle
import numpy as np
# project
# run from the repository root with the package installed
from papers.tf_systems.replication.mc_sharpe import simulate_returns, compute_signal_mc, BURN, SIGMA_TARGET, AF

C_NET = 0.0020
CONFIGS = [
    dict(mu_an=0.25, phi=0.0, d=0.0), dict(mu_an=0.50, phi=0.0, d=0.0),
    dict(mu_an=0.0, phi=0.05, d=0.0), dict(mu_an=0.0, phi=-0.05, d=0.0),
    dict(mu_an=0.0, phi=0.0, d=0.1), dict(mu_an=0.0, phi=-0.05, d=0.1),
    dict(mu_an=0.50, phi=0.0, d=0.1), dict(mu_an=0.50, phi=-0.05, d=0.1),
]
PRINTED_GROSS = {  # ls(250,20) pooled mc values of the current table, (gaussian, t6) per row
    0: (0.065, 0.061), 1: (0.234, 0.225), 2: (-0.000, -0.002), 3: (0.002, 0.003),
    4: (0.670, 0.664), 5: (0.640, 0.635), 6: (0.781, 0.776), 7: (0.763, 0.757),
}


def part(idx: int, innovation: str) -> None:
    cfg = CONFIGS[idx]
    t_dof = None if innovation == 'g' else 6.0
    t0 = time.time()
    returns = simulate_returns(n_paths=1000, n_obs=13000, mu_an=cfg['mu_an'], phi=cfg['phi'], d=cfg['d'],
                               seed=8 + idx, t_dof=t_dof)
    # vol normalisation with vol tracking, replicating the module recursion line by line
    from papers.tf_systems.replication import mc_sharpe as ms
    z = ms.compute_vol_norm_returns_mc(returns=returns)
    n_paths, n_total = returns.shape
    vol_span = 33.0
    nu_v = 1.0 - 2.0 / (vol_span + 1.0)
    var = np.mean(np.square(returns[:, :33]), axis=1)  # module warm start
    vols_post = np.empty_like(returns)
    z_chk = np.empty_like(returns)
    for t in range(n_total):
        z_chk[:, t] = returns[:, t] / np.sqrt(var)
        var = (1.0 - nu_v) * np.square(returns[:, t]) + nu_v * var
        vols_post[:, t] = np.sqrt(var)
    assert np.allclose(z_chk, z, atol=1e-10), "vol-norm replication mismatch"
    del z_chk, returns
    gc.collect()

    signal = compute_signal_mc(z=z, long_span=250.0, short_span=20.0)
    f = (SIGMA_TARGET / np.sqrt(AF)) * signal[:, :-1] * z[:, 1:]
    weights = SIGMA_TARGET / np.sqrt(AF) * signal / vols_post
    u = np.sqrt(AF) * vols_post[:, 1:] * np.abs(weights[:, 1:] - weights[:, :-1])  # eq:tur1 with the sqrt(a) factor
    f = f[:, BURN:]
    u = u[:, BURN:]
    del z, signal, weights, vols_post
    gc.collect()

    sr_gross = float(np.sqrt(AF) * np.mean(f) / np.std(f))
    a_u = float(AF * np.mean(u))
    sr_net = float(np.sqrt(AF) * (np.mean(f) - C_NET * np.mean(u)) / np.std(f))
    want = PRINTED_GROSS[idx][0 if innovation == 'g' else 1]
    gate_ok = abs(round(sr_gross, 3) - want) < 1e-9
    out = dict(idx=idx, innovation=innovation, sr_gross=sr_gross, sr_net=sr_net, a_turnover=a_u, gate_ok=gate_ok,
               want=want, f_mean=float(np.mean(f)), f_std=float(np.std(f)), u_mean=float(np.mean(u)))
    with open(f'./results/t6_part_{idx}_{innovation}.pkl', 'wb') as fh:
        pickle.dump(out, fh)
    flag = 'GATE OK' if gate_ok else f'GATE FAIL (want {want})'
    print(f"idx={idx} {innovation}: gross {sr_gross:.3f} [{flag}], net {sr_net:.3f}, aU {a_u:.1%}, {time.time()-t0:.0f}s", flush=True)


if __name__ == '__main__':
    part(int(sys.argv[1]), sys.argv[2])
