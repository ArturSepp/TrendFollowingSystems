"""Offline first success with the trendfollowing public API.

Run from any directory after installing the package:

    python C:/path/to/TrendFollowingSystems/examples/quickstart.py

The calculation uses no data or network access, writes no files, and opens no GUI.
"""

from enum import Enum

import trendfollowing as tf


# First parameters to change when exploring process and filter assumptions.
PHI = 0.05  # AR(1) coefficient of volatility-normalized daily returns.
D = 0.02  # Fractional order of the ARFIMA(0,d,0) process.
LONG_SPAN = 63  # Single-EWMA trend-filter span in trading days.
N_LAGS = 1000  # Population ACF truncation used by the closed forms.

# The paper uses 260 trading days per year. Both examples assume zero underlying drift.
AF = float(tf.AF_DAILY)


class Locals(Enum):
    """Runnable example cases."""

    QUICKSTART = 1


def run_local(local: Locals) -> None:
    """Compute and print two deterministic closed-form Sharpe ratios."""

    ar1_sharpe = tf.sharpe_ar1(
        phi=PHI,
        long_span=LONG_SPAN,
        af=AF,
        n_lags=N_LAGS,
    )
    arfima_sharpe = tf.sharpe_arfima(
        d=D,
        phi=0.0,
        long_span=LONG_SPAN,
        af=AF,
        n_lags=N_LAGS,
    )

    print(f"trendfollowing {tf.__version__}")
    print(
        f"AR(1): phi={PHI:+.3f}, span={LONG_SPAN} days, "
        f"annualized Sharpe={ar1_sharpe:.6f}"
    )
    print(
        f"ARFIMA(0,d,0): d={D:.3f}, span={LONG_SPAN} days, "
        f"annualized Sharpe={arfima_sharpe:.6f}"
    )
    print("Conventions: 260 trading days/year; zero underlying drift; one EWMA filter.")
    print("Try next: change PHI, D, or LONG_SPAN near the top of examples/quickstart.py.")


if __name__ == "__main__":
    run_local(local=Locals.QUICKSTART)
