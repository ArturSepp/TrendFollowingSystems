"""
single entry point to reproduce all figures of The Science and Practice of Trend-Following Systems
simulation figures require no data, and data figures run from the dataset shipped in trendfollowing/resources
figures are saved to TF_FIGURE_PATH if set, and to the qis output path otherwise, with file names matching the paper exhibits
"""
# packages
import os
from enum import Enum
from typing import List, Optional, Tuple
# qis
import qis as qis


class PaperFigure(Enum):
    """
    paper figures keyed to the includegraphics file names of the manuscript
    """
    SIGNAL_WEIGHT = 1              # signal_weight: filter impulse responses
    MC_EXPECTED_RETURN = 2         # legacy module for the extra variants (ar_mean, arfima2, arfima4)
    MC_EXPECTED_RETURN_PAPER = 16  # expected_return_{white_noise, ar, arfima1} in the manuscript print style
    CROSS_SYSTEM_ATTRIBUTION = 17  # tf_prediction_scatter, tf_prediction_medians
    AUTOCORRELATIONS = 3           # autoccorrelations: population acfs of the processes
    MC_SHARPE_VERIFICATION = 4     # sharpe_mc_verification + comparison tables (csv, latex)
    TF_ILLUSTRATIONS = 5           # ES1_short_signals, ES1_am_signal, ES1_tsmom_signal
    ATR_VS_VOL = 6                 # atr_vs_vol, atr_vs_vol_ts (requires bbg_fetch)
    UNIVERSE_TABLE = 7             # universe_table, UniversePrices
    COST_ASSUMPTIONS = 13          # cost_assumptions: transaction-cost table implemented in the backtests
    GRID_BACKTESTS = 8             # european_grid, american_grid_spans, tsmom_grid
    SG_BACKTEST = 9                # tf_sg_backtest_paper
    LONG_TERM_BACKTEST = 10        # lt_backtest, lt_backtest_vol_target
    SHARPE_SKEWNESS = 11           # sharpe_skeweness
    ARFIMA_ESTIMATION = 12         # arfima parameter exhibits (requires futures data and an R installation)
    AUTOCORR_ATTRIBUTION = 14      # autocorr_attribution: empirical attribution of tf sharpe to acf and drift
    STUDENT_T_MC = 15              # sharpe_verification_t6: mc robustness to student-t innovations
    AGGREGATED_SKEWNESS = 18   # aggregated_skewness: closed form, mc, and empirical panel (requires futures data)


SIMULATION_FIGURES: List[PaperFigure] = [PaperFigure.SIGNAL_WEIGHT,
                                         PaperFigure.MC_EXPECTED_RETURN,
                                         PaperFigure.MC_EXPECTED_RETURN_PAPER,
                                         PaperFigure.AUTOCORRELATIONS,
                                         PaperFigure.MC_SHARPE_VERIFICATION]

DATA_FIGURES: List[PaperFigure] = [PaperFigure.AGGREGATED_SKEWNESS,
                                   PaperFigure.TF_ILLUSTRATIONS,
                                   PaperFigure.ATR_VS_VOL,
                                   PaperFigure.UNIVERSE_TABLE,
                                   PaperFigure.COST_ASSUMPTIONS,
                                   PaperFigure.GRID_BACKTESTS,
                                   PaperFigure.SG_BACKTEST,
                                   PaperFigure.LONG_TERM_BACKTEST,
                                   PaperFigure.SHARPE_SKEWNESS,
                                   PaperFigure.ARFIMA_ESTIMATION,
                                   PaperFigure.AUTOCORR_ATTRIBUTION,
                                   PaperFigure.CROSS_SYSTEM_ATTRIBUTION,
                                   PaperFigure.STUDENT_T_MC]


def reproduce_figure(figure: PaperFigure) -> None:
    """
    dispatch one paper figure to its generating module
    imports are local so that missing private data packages fail only the figures that need them
    """
    if figure == PaperFigure.SIGNAL_WEIGHT:
        from papers.tf_systems.replication.filter_figs import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.FILTER_WEIGHTS)
    elif figure == PaperFigure.MC_EXPECTED_RETURN:
        from papers.tf_systems.replication.mc_expected_return_figs import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.ARTICLE_FIGURES)
    elif figure == PaperFigure.AUTOCORRELATIONS:
        from papers.tf_systems.replication.mc_expected_return_figs import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.FIGURE_AUTOCORRELATION)
    elif figure == PaperFigure.MC_SHARPE_VERIFICATION:
        from papers.tf_systems.replication.mc_sharpe_figs import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.SHARPE_VERIFICATION)
    elif figure == PaperFigure.TF_ILLUSTRATIONS:
        from papers.tf_systems.replication.illustrate_systems import run_local_test, LocalTests
        for local_test in [LocalTests.EUROPEAN_SHORT, LocalTests.AMERICAN, LocalTests.TSMOM]:
            run_local_test(local_test=local_test)
    elif figure == PaperFigure.AGGREGATED_SKEWNESS:
        from papers.tf_systems.replication.aggregated_skewness_fig import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.PAPER_FIGURE)
    elif figure == PaperFigure.ATR_VS_VOL:
        from papers.tf_systems.replication.atr_vs_vol import run_local_test, LocalTests
        for local_test in [LocalTests.SCATTER_FIGURE, LocalTests.TIME_SERIES_FIGURE]:
            run_local_test(local_test=local_test)
    elif figure == PaperFigure.UNIVERSE_TABLE:
        from papers.tf_systems.replication.backtest_figs import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.UNIVERSE_TABLE)
    elif figure == PaperFigure.COST_ASSUMPTIONS:
        from papers.tf_systems.replication.backtest_figs import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.COST_ASSUMPTIONS)
    elif figure == PaperFigure.AUTOCORR_ATTRIBUTION:
        from papers.tf_systems.replication.autocorr_attribution import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.ATTRIBUTION_FIGURE)
    elif figure == PaperFigure.STUDENT_T_MC:
        from papers.tf_systems.replication.mc_sharpe_figs import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.STUDENT_T_ROBUSTNESS)
    elif figure == PaperFigure.MC_EXPECTED_RETURN_PAPER:
        from papers.tf_systems.replication import mc_net_sharpe_paper_figs as mnf
        for case in [mnf.LocalTests.COMPUTE_WHITE_NOISE, mnf.LocalTests.COMPUTE_AR,
                     mnf.LocalTests.COMPUTE_ARFIMA, mnf.LocalTests.PLOT]:
            mnf.run_local_test(case)

    elif figure == PaperFigure.CROSS_SYSTEM_ATTRIBUTION:
        from papers.tf_systems.replication import cross_system_attribution_figs as csf
        csf.run_local_test(csf.LocalTests.COMPUTE_AND_PLOT)

    elif figure == PaperFigure.GRID_BACKTESTS:
        # [TODO: regenerate the grid figures with the turnover panel replacing the Bear-Sharpe panel]
        from papers.tf_systems.replication.backtest_figs import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.GRID_BACKTEST)
    elif figure == PaperFigure.SG_BACKTEST:
        from papers.tf_systems.replication.backtest_figs import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.JOINT_BACKTEST_CG)
    elif figure == PaperFigure.LONG_TERM_BACKTEST:
        from papers.tf_systems.replication.backtest_figs import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.LONG_TERM_BACKTEST)
    elif figure == PaperFigure.SHARPE_SKEWNESS:
        from papers.tf_systems.replication.backtest_figs import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.SKEWENESS_VOL_TARGET)
    elif figure == PaperFigure.ARFIMA_ESTIMATION:
        from papers.tf_systems.replication.estimate_arfima import run_local_test, LocalTests
        run_local_test(local_test=LocalTests.UNIVERSE)
    else:
        raise ValueError(f"unmapped figure, got {figure!r}")


def reproduce_all_figures(figures: Optional[List[PaperFigure]] = None,
                          include_data_dependent: bool = True,  # data figures run from the packaged dataset; atr needs terminal access
                          local_path: Optional[str] = None,  # figure output folder, defaults to TF_FIGURE_PATH or the qis output path
                          ) -> Tuple[List[PaperFigure], List[Tuple[PaperFigure, str]]]:
    """
    reproduce the paper figures and report which figures were generated and which were skipped
    simulation figures always run, and data-dependent figures run only when include_data_dependent is true
    """
    if local_path is not None:
        os.environ["TF_FIGURE_PATH"] = local_path
    if figures is None:
        figures = SIMULATION_FIGURES + (DATA_FIGURES if include_data_dependent else [])
    completed, skipped = [], []
    for figure in figures:
        try:
            reproduce_figure(figure=figure)
            completed.append(figure)
        except (ImportError, FileNotFoundError, KeyError) as e:
            skipped.append((figure, f"{type(e).__name__}: {e}"))
    print(f"completed: {[f.name for f in completed]}")
    for figure, reason in skipped:
        print(f"skipped {figure.name}: {reason}")
    return completed, skipped


class LocalTests(Enum):
    SIMULATION_ONLY = 1
    ALL_FIGURES = 2


def run_local_test(local_test: LocalTests):
    if local_test == LocalTests.SIMULATION_ONLY:
        reproduce_all_figures(include_data_dependent=False)
    elif local_test == LocalTests.ALL_FIGURES:
        reproduce_all_figures(include_data_dependent=True)


if __name__ == '__main__':
    run_local_test(local_test=LocalTests.SIMULATION_ONLY)
