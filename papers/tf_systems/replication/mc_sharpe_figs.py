"""
comparison tables and errorbar figures for the analytical sharpe ratio vs monte carlo estimates
figures follow the article style of papers.tf_systems.replication.mc_expected_return_figs: qis.plot_errorbar with mc errorbars and exact analytic markers
tables report analytic vs mc pooled sharpe with 95% confidence intervals per process and filter span
"""
# packages
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from enum import Enum
from typing import Dict, List, Optional
# qis / project
import qis as qis
from qis.plots.utils import get_n_colors
from papers.tf_systems.replication.mc_sharpe import run_verification

LONG_SPANS: Dict[str, int] = {'1w': 5, '2w': 10, '1m': 21, '3m': 63, '6m': 125, '1y': 250, '2y': 500}
LS_CASE = (250.0, 20.0)  # long-short filter of the empirical section

PROCESS_CONFIGS: List[Dict] = [dict(name='wn_mu25', mu_an=0.25),
                               dict(name='wn_mu50', mu_an=0.5),
                               dict(name='ar1_pos', mu_an=0.0, phi=0.05),
                               dict(name='ar1_neg', mu_an=0.0, phi=-0.05),
                               dict(name='arfima_d10', mu_an=0.0, d=0.1),
                               dict(name='arfima_d10_ar05', mu_an=0.0, phi=-0.05, d=0.1),
                               dict(name='arfima_d10_mu50', mu_an=0.5, d=0.1),
                               dict(name='arfima_d10_ar05_mu50', mu_an=0.5, phi=-0.05, d=0.1)]

PROCESS_LABELS: Dict[str, str] = {'wn_mu25': 'White noise, $\\mu^{z}_{an}$=0.25',
                                  'wn_mu50': 'White noise, $\\mu^{z}_{an}$=0.50',
                                  'ar1_pos': 'AR-1, $\\phi$=0.05',
                                  'ar1_neg': 'AR-1, $\\phi$=-0.05',
                                  'arfima_d10': 'ARFIMA, $d$=0.1',
                                  'arfima_d10_ar05': 'ARFIMA, $d$=0.1, $\\phi$=-0.05',
                                  'arfima_d10_mu50': 'ARFIMA, $d$=0.1, $\\mu^{z}_{an}$=0.50',
                                  'arfima_d10_ar05_mu50': 'ARFIMA, $d$=0.1, $\\phi$=-0.05, $\\mu^{z}_{an}$=0.50'}


def compute_sharpe_verification(long_spans: Dict[str, int] = LONG_SPANS,
                                n_paths: int = 1000,  # matched to the per-process figures
                                n_obs: int = 13000,  # kept observations per path, 50 years, matched to the figures
                                base_seed: int = 8,
                                t_dof: Optional[float] = None  # student-t dof for the innovations, None for gaussian
                                ) -> pd.DataFrame:
    """
    run the mc verification grid and attach span labels for reporting
    """
    df = run_verification(spans=[float(x) for x in long_spans.values()],
                          process_configs=PROCESS_CONFIGS,
                          n_paths=n_paths,
                          n_obs=n_obs,
                          short_span_cases=[LS_CASE],
                          t_dof=t_dof,
                          base_seed=base_seed)
    span_labels = {float(v): k for k, v in long_spans.items()}
    labels = []
    for _, row in df.iterrows():
        if not np.isnan(row['short_span']):
            labels.append(f"LS({row['long_span']:0.0f},{row['short_span']:0.0f})")
        else:
            labels.append(span_labels.get(row['long_span'], f"{row['long_span']:0.0f}d"))
    df['span_label'] = labels
    return df


def build_comparison_tables(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    per-process comparison table with span labels as index: analytic, mc pooled, mc 95% ci, absolute error
    """
    tables = {}
    for config in PROCESS_CONFIGS:
        name = config['name']
        data = df.loc[df['process'] == name]
        columns = dict(analytic=data['sr_analytic'].to_numpy(),
                       mc=data['sr_mc_pooled'].to_numpy(),
                       mc_ci95=data['pooled_ci95'].to_numpy(),
                       abs_error=data['abs_error'].to_numpy())
        if 'sr_analytic_kappa' in data.columns and data['sr_analytic_kappa'].notna().any():
            columns['analytic_kappa'] = data['sr_analytic_kappa'].to_numpy()
        table = pd.DataFrame(columns, index=data['span_label'].to_numpy())
        table.index.name = 'span'
        tables[name] = table
    return tables


def print_comparison_tables(tables: Dict[str, pd.DataFrame]) -> None:
    """
    print per-process comparison tables with 4-decimal formatting
    """
    for name, table in tables.items():
        print(f"\n{PROCESS_LABELS[name]}")
        print(table.to_string(float_format=lambda x: f"{x:0.4f}"))


def comparison_table_to_latex(tables: Dict[str, pd.DataFrame],
                              process_order: Optional[List[str]] = None,
                              ) -> str:
    """
    single latex table: rows are filter spans, column pairs per process are analytic and mc with 95% ci
    """
    if process_order is None:
        process_order = ['wn_mu50', 'ar1_pos', 'arfima_d10', 'arfima_d10_ar05']
    index = tables[process_order[0]].index
    header1 = 'Span'
    header2 = ''
    for name in process_order:
        header1 += f" & \\multicolumn{{2}}{{c}}{{{PROCESS_LABELS[name]}}}"
        header2 += " & Analytic & MC $\\pm$ CI"
    lines = ["\\begin{tabular}{l" + "cc" * len(process_order) + "}",
             "\\hline",
             header1 + " \\\\",
             header2 + " \\\\",
             "\\hline"]
    for span in index:
        row = str(span)
        for name in process_order:
            t = tables[name].loc[span]
            row += f" & ${t['analytic']:0.3f}$ & ${t['mc']:0.3f} \\pm {t['mc_ci95']:0.3f}$"
        lines.append(row + " \\\\")
    lines += ["\\hline", "\\end{tabular}"]
    return "\n".join(lines)


def plot_sharpe_verification_figure(df: pd.DataFrame,
                                    long_spans: Dict[str, int] = LONG_SPANS
                                    ) -> plt.Figure:
    """
    2x2 article figure: mc errorbars with exact analytic markers per process family, long-short case in the last panel
    """
    span_index = list(long_spans.keys())

    def get_series(name: str, column: str) -> pd.Series:
        data = df.loc[(df['process'] == name) & (df['short_span'].isna())]
        return pd.Series(data[column].to_numpy(), index=data['span_label'].to_numpy()).reindex(span_index)

    panels = [([('wn_mu25', '$\\mu^{z}_{an}$=0.25'), ('wn_mu50', '$\\mu^{z}_{an}$=0.50')], 'White noise with drift'),
              ([('ar1_pos', '$\\phi$=0.05'), ('ar1_neg', '$\\phi$=-0.05')], 'AR-1 process'),
              ([('arfima_d10', '$d$=0.1'), ('arfima_d10_ar05', '$d$=0.1, $\\phi$=-0.05')], 'ARFIMA process'),
              ([('arfima_d10_mu50', '$d$=0.1, $\\mu^{z}_{an}$=0.50'), ('arfima_d10_ar05_mu50', '$d$=0.1, $\\phi$=-0.05, $\\mu^{z}_{an}$=0.50')], 'ARFIMA process with drift')]

    with sns.axes_style('darkgrid'):
        fig, axs = plt.subplots(2, 2, figsize=(16, 12), tight_layout=True)
        axs = qis.to_flat_list(axs)
        kwargs = dict(legend_loc='upper center',
                      capsize=10,
                      fontsize=12,
                      framealpha=0.9,
                      marker='_',
                      exact_marker='o',
                      var_format='{:.2f}',
                      xlabel='Signal span',
                      add_zero_line=True)
        for idx, (variables, panel_title) in enumerate(panels):
            mcs, stds, exacts = {}, {}, {}
            for name, label in variables:
                mcs[f"Monte-Carlo, {label}"] = get_series(name, 'sr_mc_pooled')
                stds[f"Monte-Carlo, {label}"] = get_series(name, 'pooled_ci95')
                exacts[f"Analytic, {label}"] = get_series(name, 'sr_analytic')
            colors = get_n_colors(n=len(variables))
            qis.plot_errorbar(df=pd.DataFrame.from_dict(mcs, orient='columns'),
                              y_std_errors=pd.DataFrame.from_dict(stds, orient='columns'),
                              exact=pd.DataFrame.from_dict(exacts, orient='columns'),
                              title=f"({qis.idx_to_alphabet(idx + 1)}) {panel_title}",
                              colors=colors,
                              exact_colors=colors,
                              ax=axs[idx],
                              **kwargs)
    return fig


class LocalTests(Enum):
    SHARPE_VERIFICATION = 1
    STUDENT_T_ROBUSTNESS = 2


def run_local_test(local_test: LocalTests):
    local_path = os.environ.get("TF_FIGURE_PATH", qis.local_path.get_output_path())  # set TF_FIGURE_PATH to the paper figures folder
    if local_test == LocalTests.SHARPE_VERIFICATION:
        df = compute_sharpe_verification()
        df.to_csv(f"{local_path}sharpe_verification.csv", index=False)
        tables = build_comparison_tables(df=df)
        print_comparison_tables(tables=tables)
        latex = comparison_table_to_latex(tables=tables)
        with open(f"{local_path}sharpe_verification_table.tex", 'w') as f:
            f.write(latex)
        fig = plot_sharpe_verification_figure(df=df)
        qis.save_fig(fig, file_name='sharpe_mc_verification', local_path=local_path)

    elif local_test == LocalTests.STUDENT_T_ROBUSTNESS:
        df_gauss = compute_sharpe_verification()
        df_t = compute_sharpe_verification(t_dof=6.0)
        keys = ['process', 'mu_an', 'phi', 'd', 'long_span', 'short_span']
        for df_ in (df_gauss, df_t):
            df_['short_span'] = df_['short_span'].fillna(0.0)
        merged = df_gauss[keys + ['sr_analytic', 'sr_mc_pooled', 'pooled_ci95']].merge(
            df_t[keys + ['sr_mc_pooled', 'pooled_ci95']], on=keys, suffixes=('_gauss', '_t6'))
        merged['t6_minus_gauss'] = merged['sr_mc_pooled_t6'] - merged['sr_mc_pooled_gauss']
        merged['t6_minus_analytic'] = merged['sr_mc_pooled_t6'] - merged['sr_analytic']
        merged.to_csv(f"{local_path}sharpe_verification_t6.csv", index=False)
        with open(f"{local_path}sharpe_verification_t6_table.tex", 'w') as f:
            f.write(merged.round(3).to_latex(index=False))
        print(merged.to_string(float_format=lambda x: f"{x:0.4f}"))


if __name__ == '__main__':
    run_local_test(local_test=LocalTests.SHARPE_VERIFICATION)
