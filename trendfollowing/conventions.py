"""
shared return conventions of the trend-following papers.

both papers fix the same conventions, and this module is their single source:

annualisation. daily statistics annualise with AF_DAILY = 260 trading days, the
convention of the sifin paper's table 6 and analytic verifications. qis infers
252 from the calendar density of the futures panel, so the papers pass the
explicit constant instead of relying on inference. quarterly and monthly
statistics annualise with 4 and 12.

sharpe ratios. arithmetic convention throughout: sqrt(a) times the mean over
the standard deviation of periodic simple excess returns. the joim paper's
regime decomposition (proposition 1) is exact only under arithmetic means, and
the sifin paper's analytic sharpe ratios use the same convention.

returns and navs. daily futures data are stored as prices built from log
returns, and returns are extracted with qis.to_returns with the is_log_returns
flag stated at the call. periodic returns for regime sampling are arithmetic
simple returns at calendar anchors via qis.to_returns(freq=...). navs compound
arithmetically via qis.returns_to_nav.
"""
# packages
import numpy as np
import pandas as pd
from typing import Union
# qis
import qis as qis

AF_DAILY = 260.0  # trading days per year, the paper convention (not the qis-inferred 252)
PPY_QUARTERLY = 4.0
PPY_MONTHLY = 12.0


def compute_daily_annualised_vol(navs: Union[pd.Series, pd.DataFrame]
                                 ) -> Union[float, pd.Series]:
    """annualised volatility of daily arithmetic returns under the paper convention"""
    returns = qis.to_returns(prices=navs, is_log_returns=False)
    return returns.std() * np.sqrt(AF_DAILY)
