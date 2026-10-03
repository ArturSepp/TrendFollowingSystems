"""Render the three cached process figures and two cached attribution figures."""

from papers.tf_systems.replication import mc_net_sharpe_paper_figs as process
from papers.tf_systems.replication import cross_system_attribution_figs as attribution


def main() -> None:
    """Read frozen reference inputs; write reviewed candidates outside the checkout."""
    process.run_local(local=process.Locals.PLOT)
    attribution.run_local(local=attribution.Locals.PLOT_FROM_CACHE)


if __name__ == "__main__":
    main()
