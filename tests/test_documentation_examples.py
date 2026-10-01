"""Execute the worked examples of the handbook chapters.

Every ``python`` block of a methodology chapter or of the case study runs offline, in one
namespace per page, in the order of the page. A block preceded by the comment
``<!-- docs-test: skip -->`` is schematic and is not executed. The blocks assert every number
their page quotes, so a change in the package that moves a documented value fails here.
"""

from pathlib import Path
import re
import warnings

import pytest


DOCS_ROOT = Path(__file__).resolve().parents[1] / "docs"
EXECUTED_PAGES = (
    "notation_and_conventions.md",
    "ewma_filters.md",
    "volatility_normalisation.md",
    "return_processes.md",
    "pnl_decomposition.md",
    "sharpe_ratio_closed_form.md",
    "sharpe_under_processes.md",
    "turnover_and_net_sharpe.md",
    "aggregated_skewness.md",
    "european_system.md",
    "american_system.md",
    "tsmom_system.md",
    "futures_universe_and_costs.md",
    "sharpe_inference.md",
    "case_study_futures_evidence.md",
)
PYTHON_BLOCK = re.compile(r"(<!-- docs-test: skip -->[ \t]*\n)?```python\n(.*?)\n```", re.S)


def python_blocks(page: str) -> list[str]:
    """Return the executable python blocks of a page, in order."""
    text = (DOCS_ROOT / page).read_text(encoding="utf-8")
    return [match.group(2) for match in PYTHON_BLOCK.finditer(text) if not match.group(1)]


@pytest.mark.parametrize("page", EXECUTED_PAGES)
def test_handbook_page_examples_run(page: str) -> None:
    blocks = python_blocks(page)
    assert blocks, f"{page} has no executable python block"
    namespace = {"__name__": f"docs_{Path(page).stem}"}
    with warnings.catch_warnings():
        # The CSV reader of the packaged data infers its date format; that is not an error here.
        warnings.simplefilter("ignore", UserWarning)
        for index, block in enumerate(blocks):
            exec(compile(block, f"docs/{page} [python block {index}]", "exec"), namespace)
