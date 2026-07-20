"""
estimate
"""
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import qis as qis
from qis.plots.utils import align_x_limits_axs, align_y_limits_axs
from qis.utils.df_groups import convert_df_column_to_df_by_groups
from typing import Dict, List
from enum import Enum

from trendfollowing.universe import load_data
from trendfollowing.systems.european import run_european_tf_system
from trendfollowing.systems.backtest_utils import compute_path_stats

# add paths
os.environ["R_HOME"] = r"C:\Program Files\R\R-4.4.2"
os.environ["PATH"] = r"C:\Program Files\R\R-4.4.2\bin\x64" + ";" + os.environ["PATH"]
R_SOURCE_PATH = os.environ.get("TF_R_SOURCE_PATH", "Estimate_ARFIMA.R")  # set to the location of the R estimation script
#import rpy2.robjects as ro
#from rpy2.robjects import pandas2ri
#pandas2ri.activate()


def fit_arfima(data: pd.Series) -> pd.DataFrame:
    """
    wrapper for r function
    """
    print(f"arifma fit for {data.name}")
    r = ro.r
    r.source(R_SOURCE_PATH)
    df_data = data.loc[np.isfinite(data)].to_frame('Close')
    output = r.fit_arfima(df_data)
    print(output)
    array = rlist_to_array(output)

    df = pd.DataFrame(array,
                      columns=['Estimate', 'Std. Error', 'Th. Std. Err.', 'z-value', 'Pr(>|z|)])'],
                      index=['phi(1)', 'd.f', 'Fitted mean'])

    return df


def rlist_to_array(r):
    """
    Returns a R named list as a Python dictionary
    """
    # In case `r` is not a named list
    try:
        # No more names, just return the value!
        if r.names == ro.NULL:
            # If more than one value, return numpy array (or list)
            if len(list(r)) > 1:
                return np.array(r)
            # Just one value, return the value
            else:
                return list(r)[0]
        # Create dictionary to hold named list as key-value
        dic = {}
        for n in list(r.names):
            dic[n] = rlist_to_array(r[r.names.index(n)])
        return dic
    # Uh-oh `r` is not a named list, just return `r` as is
    except:
        return r


def estimate_universe(returns: pd.DataFrame) -> pd.DataFrame:
    dfs = []
    for asset in returns.columns:
        data = returns[asset].dropna()
        if len(data.index) > 100:
            df = fit_arfima(data)
            df.insert(loc=0, column='asset', value=asset)
            dfs.append(df)
    dfs = pd.concat(dfs)
    return dfs


def analyse_params(params: Dict[str, pd.DataFrame]):
    with sns.axes_style("darkgrid"):
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        qis.df_dict_boxplot_by_columns(dfs=params,
                                       hue_var_name='instruments',
                                       y_var_name='long memory parameter',
                                       ylabel='weights',
                                       legend_loc='upper center',
                                       yvar_format='{:.2f}',
                                       showmedians=True,
                                       # add_y_median_labels=True,
                                       ncols=2,
                                       ax=ax)


def plot_params_boxplot(descriptive_df: pd.DataFrame,
                        local_path: str,
                        group_order: List[str] = None
                        ) -> plt.Figure:

    params_dict = {'d.f': ('(A) Fractional order d', '{:.2f}', 1.0),
                   'phi(1)': ('(B) AR-1 coefficient phi', '{:.2f}', 1.0),
                   'Fitted mean': ('(C) Mean annualised', '{:.0%}', np.sqrt(260))}

    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(1, len(params_dict.keys()), figsize=(14, 6), tight_layout=True)

        for idx, (param_name, (title, xvar_format, multiplier)) in enumerate(params_dict.items()):
            df1 = qis.load_df_from_excel(file_name='arifram_estimates_20241114_1962_2004', local_path=f"{local_path}//arfima",
                                         sheet_name=param_name)
            df1 = df1.loc[df1['Std. Error'] < np.nanquantile(df1['Std. Error'], q=0.8), :]  # exlude outliers with high std

            df2 = qis.load_df_from_excel(file_name='arifram_estimates_20241114_2004_2024', local_path=f"{local_path}//arfima",
                                         sheet_name=param_name)
            df2 = df2.loc[df2['Std. Error'] < np.nanquantile(df2['Std. Error'], q=0.8), :]  # exlude outliers with high std

            print(f"{param_name}-1")
            print(df1)
            print(f"{param_name}-2")
            print(df2)
            df1['Estimate'] *= multiplier
            df2['Estimate'] *= multiplier
            dfs1 = convert_df_column_to_df_by_groups(df=df1, group_data=descriptive_df['group_data'],
                                                         column='Estimate', group_order=group_order)
            dfs2 = convert_df_column_to_df_by_groups(df=df2, group_data=descriptive_df['group_data'],
                                                         column='Estimate', group_order=group_order)

            params = {'1965-2004': dfs1,
                      '2005-2025': dfs2}
            qis.df_dict_boxplot_by_columns(dfs=params,
                                           hue_var_name='group',
                                           y_var_name=title,
                                           ylabel='estimate',
                                           hue='estimation period',
                                           title=title,
                                           x_rotation=90,
                                           showmedians=True,
                                           yvar_format=xvar_format,
                                           fontsize=12,
                                           ax=axs[idx])
            axs[idx].axhline(y=0, linewidth=2, color='orange')

    return fig


def plot_params_vs_pnl(prices: pd.DataFrame,
                       volume_costs: pd.DataFrame,
                       local_path: str,
                       ) -> plt.Figure:

    params_dict = {'d.f': ('Fractional order', '{:.2f}', 1.0),
                   'phi(1)': ('AR-1 coefficient', '{:.2f}', 1.0),
                   'Fitted mean': ('Mean annualised', '{:.0%}', np.sqrt(260))}

    e_backtest_outputs = run_european_tf_system(prices=prices,
                                                long_span=250,
                                                short_span=20,
                                                vol_span=33,
                                                vol_target=0.05,
                                                portfolio_covar_span=None,
                                                portfolio_target_vol=0.15,
                                                volume_costs=volume_costs)

    total_pnl, pnl_an, vol_an, sharpe = compute_path_stats(pnl_paths=e_backtest_outputs.instrument_pnl.to_numpy())
    sharpe = pd.Series(sharpe, index=prices.columns, name='sharpe')
    sharpe = sharpe.drop('MES1 Index')
    print(sharpe)

    # figs = []
    with sns.axes_style("darkgrid"):
        fig, axs = plt.subplots(3, 2, figsize=(16, 8), tight_layout=True)
        for idx, (param_name, (title, xvar_format, multiplier)) in enumerate(params_dict.items()):
            df1 = qis.load_df_from_excel(file_name='arifram_estimates_20241114_1962_2004', local_path=f"{local_path}//arfima",
                                         sheet_name=param_name)
            df1 = df1.loc[df1['Std. Error'] < np.nanquantile(df1['Std. Error'], q=0.8), :]  # exlude outliers with high std

            df2 = qis.load_df_from_excel(file_name='arifram_estimates_20241114_2004_2024', local_path=f"{local_path}//arfima",
                                         sheet_name=param_name)
            df2 = df2.loc[df2['Std. Error'] < np.nanquantile(df2['Std. Error'], q=0.8), :]  # exlude outliers with high std

            print(f"{param_name}-1")
            print(df1)
            print(f"{param_name}-2")
            print(df2)

            kwargs = dict(xvar_format=xvar_format, yvar_format='{:.2f}', full_sample_order=1,
                          fontsize=14)
            df_1 = pd.concat([multiplier*df1['Estimate'].rename(title), sharpe], axis=1).dropna()
            qis.plot_scatter(df=df_1,
                             # title=f"Period 1962-2004",
                             title=f"({qis.idx_to_alphabet(idx+1)}1)  {title}: Period 1962-2004",
                             ax=axs[idx, 0],
                             **kwargs)

            df_2 = pd.concat([multiplier*df2['Estimate'].rename(title), sharpe], axis=1).dropna()
            qis.plot_scatter(df=df_2,
                             title=f"({qis.idx_to_alphabet(idx+1)}2) {title}: Period 2005-2024",
                             ax=axs[idx, 1],
                             **kwargs)
            axs[idx, 0].axvline(x=0, linewidth=2, color='orange')
            axs[idx, 1].axvline(x=0, linewidth=2, color='orange')
            # align_x_limits_axs(axs)
            align_y_limits_axs(axs[idx, :])
            # qis.set_suptitle(fig, title=f"{title}")

    return fig


class LocalTests(Enum):
    ESTIMATE1 = 1
    MULTI_ESTIMATE = 2
    PARAMS_BOXPLOT = 3
    PARAMS_VS_PNL = 4


def run_local_test(local_test: LocalTests):
    """Run local tests for development and debugging purposes.

    These are integration tests that download real data and generate reports.
    Use for quick verification during development.
    """

    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    import matplotlib.pyplot as plt
    local_path = os.environ.get("TF_FIGURE_PATH", qis.local_path.get_output_path())  # set TF_FIGURE_PATH to the paper figures folder


    #time_period = qis.TimePeriod(start='31Dec1998', end='08Nov2024')
    #time_period = qis.TimePeriod(start='31Dec2009', end='08Nov2024')
    # time_period = qis.TimePeriod(start='31Dec2004', end='08Nov2024')
    time_period = qis.TimePeriod(start='31Dec1961', end='31Dec2004')
    #time_period = qis.TimePeriod(start='31Dec1961', end='08Nov2024')
    # time_period = None

    prices, volume_costs, benchmark_prices, descriptive_df, group_order = load_data(time_period=time_period)

    returns = qis.to_returns(prices=prices, is_log_returns=True, freq=None)
    ra_returns, _, _ = qis.compute_ra_returns(returns=returns, span=33, vol_target=0.15, is_log_returns_to_arithmetic=True)
    ra_returns.index.name = 'Date'

    if local_test == LocalTests.ESTIMATE1:
        data = ra_returns['ES1 Index'].dropna().to_frame('Close')
        df = fit_arfima(data)  # calling the function with passing arguments
        print(df)

    elif local_test == LocalTests.MULTI_ESTIMATE:
        # ra_returns = ra_returns.drop(['XU1 Index', 'WN1 Comdty'], axis=1)
        df = estimate_universe(returns=ra_returns) # .iloc[:, :20])
        df = df.reset_index(names='params')
        gr_data = df.groupby('params', axis=0)
        data = {}
        for key, df1 in gr_data:
            df1 = df1.set_index('asset', drop=True)
            print(key)
            print(df1)
            print(df1.describe())
            data[key] = df1
        qis.save_df_to_excel(data=data, file_name='arifram_estimates', local_path=qis.get_output_path(), add_current_date=True)

        df1 = gr_data.get_group('phi(1)').set_index('asset', drop=True)['Estimate']
        qis.plot_bars(df=df1)

    elif local_test == LocalTests.PARAMS_BOXPLOT:

        fig = plot_params_boxplot(descriptive_df=descriptive_df, local_path=local_path, group_order=group_order)
        qis.save_fig(fig, file_name=f"param_boxplot", local_path=f"{local_path}new_figures//")

    elif local_test == LocalTests.PARAMS_VS_PNL:

        fig = plot_params_vs_pnl(prices=prices, volume_costs=volume_costs, local_path=local_path)
        #for idx, fig in enumerate(figs):
        #    qis.save_fig(fig, file_name=f"{idx+1}_param_by_period", local_path=f"{local_path}Figures//")
        qis.save_fig(fig, file_name=f"return_vs_params", local_path=f"{local_path}new_figures//")

    plt.show()


if __name__ == '__main__':

    local_test = LocalTests.PARAMS_VS_PNL

    run_local_test(local_test=local_test)
