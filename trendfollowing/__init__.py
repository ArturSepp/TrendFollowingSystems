"""
trendfollowing: replication package for The Science and Practice of Trend-Following Systems
reference: Sepp, A. and Lucic, V., The Science and Practice of Trend-Following Systems,
https://ssrn.com/abstract=3167787
"""
__version__ = "1.0.0"

from trendfollowing.analytics.filters import (span_to_nu,
                                              compute_ewm_long_short_weights)
from trendfollowing.analytics.autocorrelation import (population_acf,
                                                      compute_psi_nu,
                                                      power_autocorr)
from trendfollowing.analytics.expected_return import (expected_pnl_white_noise,
                                                      expected_pnl_ar1,
                                                      expected_pnl_ma1,
                                                      expected_pnl_arfima,
                                                      expected_turnover)
from trendfollowing.analytics.sharpe import (SignalMoments,
                                             compute_signal_moments,
                                             compute_daily_moments,
                                             compute_annualised_sharpe,
                                             compute_realized_sharpe,
                                             sharpe_white_noise,
                                             sharpe_white_noise_approx,
                                             sharpe_ar1,
                                             sharpe_ar1_approx,
                                             sharpe_arfima,
                                             expected_annual_return)
from trendfollowing.analytics.skewness import (aggregated_third_moment_white_noise,
                                                skewness_white_noise,
                                                skewness_master_curve,
                                                skewness_peak_horizon)

from trendfollowing.conventions import (AF_DAILY,
                                        PPY_QUARTERLY,
                                        PPY_MONTHLY,
                                        compute_daily_annualised_vol)
