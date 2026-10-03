"""Structural checks of the trendfollowing handbook in docs/.

These tests enforce the mechanical rules of docs/documentation_standard.md: page metadata and
bylines, the section order of methodology chapters and the case study, the eight-row convention
card, references copied verbatim from the single bibliography, a toctree that lists every page
once, API coverage of the top-level exports, cross-references that resolve, GitHub-portable
mathematics and figures drawn only from the approved manuscript figures.
"""

from pathlib import Path
import importlib
import inspect
import re

import pytest
import trendfollowing as tf


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPOSITORY_ROOT / "docs"
FIGURES_ROOT = REPOSITORY_ROOT / "papers" / "tf_systems" / "paper" / "figures"
BYLINE = "*Author: [Artur Sepp](https://github.com/ArturSepp)"
CITATION = "https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff"
SOFTWARE_ENTRY = "Sepp, A., and Lucic, V. trendfollowing:"
PENDING = " [pending publisher check]"

METHODOLOGY_PAGES = (
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
)
CASE_STUDY_PAGES = ("case_study_futures_evidence.md",)
METHODOLOGY_SECTIONS = [
    "Overview",
    "Inputs, notation, and assumptions",
    "Methodology",
    "Worked example",
    "Implementation in trendfollowing",
    "Interpretation and limitations",
    "See also",
    "References",
]
CASE_STUDY_SECTIONS = [
    "Overview",
    "Study design and data",
    "Configuration",
    "Results",
    "What the study does and does not show",
    "Reproduce",
    "See also",
    "References",
]
CONVENTION_ROWS = [
    "Return basis",
    "Normalisation",
    "Signal filter",
    "Moment basis",
    "Annualisation",
    "Timing",
    "Costs",
    "trendfollowing default",
]
FENCE = re.compile(r"^(```|~~~).*?^\1", re.S | re.M)


def read(page: str) -> str:
    return (DOCS_ROOT / page).read_text(encoding="utf-8")


def all_pages() -> list[str]:
    return sorted(path.name for path in DOCS_ROOT.glob("*.md"))


def without_code(text: str) -> str:
    """Remove fenced blocks, so that checks see prose and mathematics only."""
    return FENCE.sub("", text)


def h2_headings(text: str) -> list[str]:
    return [line[3:].strip() for line in without_code(text).splitlines() if line.startswith("## ")]


def section(text: str, heading: str) -> str:
    """Return the body of an H2 section, up to the next H2."""
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    assert match, f"missing section {heading!r}"
    return match.group(1)


def bibliography_entries() -> list[str]:
    entries = []
    for line in read("bibliography.md").splitlines():
        if line.startswith("- "):
            entry = line[2:]
            entries.append(entry[: -len(PENDING)] if entry.endswith(PENDING) else entry)
    return entries


def reference_items(text: str) -> list[str]:
    return [re.sub(r"^\d+\. ", "", line) for line in section(text, "References").splitlines()
            if re.match(r"^\d+\. ", line)]


@pytest.mark.parametrize("page", all_pages())
def test_page_has_description_title_byline_and_software_link(page: str) -> None:
    text = read(page)
    assert text.startswith("---\nmyst:\n  html_meta:\n    description: >-\n"), page
    lines = text.split("\n---\n", 1)[1].lstrip("\n").splitlines()
    assert lines[0].startswith("# "), page
    assert sum(1 for line in without_code(text).splitlines() if line.startswith("# ")) == 1, page
    assert lines[2].startswith(BYLINE), page
    assert CITATION in text, page


@pytest.mark.parametrize("page", METHODOLOGY_PAGES)
def test_methodology_chapter_sections_and_convention_card(page: str) -> None:
    text = read(page)
    assert h2_headings(text) == METHODOLOGY_SECTIONS
    inputs = section(text, "Inputs, notation, and assumptions")
    table = []
    for line in inputs.strip().splitlines():
        if not line.startswith("|"):
            break
        table.append(line)
    assert table[0] == "| Convention | This article |", page
    rows = [line.split("|")[1].strip() for line in table[2:]]
    assert rows == CONVENTION_ROWS, page
    assert "```python" in section(text, "Worked example"), page


@pytest.mark.parametrize("page", CASE_STUDY_PAGES)
def test_case_study_sections(page: str) -> None:
    assert h2_headings(read(page)) == CASE_STUDY_SECTIONS


@pytest.mark.parametrize("page", METHODOLOGY_PAGES + CASE_STUDY_PAGES)
def test_references_copy_bibliography_entries_verbatim(page: str) -> None:
    entries = bibliography_entries()
    items = reference_items(read(page))
    assert items, page
    for item in items:
        assert any(item.startswith(entry) for entry in entries), f"{page}: {item[:80]}"
    assert any(item.startswith(SOFTWARE_ENTRY) for item in items), page


def test_bibliography_entries_are_unique_and_cited() -> None:
    entries = bibliography_entries()
    assert len(entries) == len(set(entries))
    cited = "\n".join(item for page in METHODOLOGY_PAGES + CASE_STUDY_PAGES
                      for item in reference_items(read(page)))
    for entry in entries:
        assert entry in cited, f"uncited bibliography entry: {entry[:80]}"


def test_toctree_lists_every_page_exactly_once() -> None:
    blocks = re.findall(r"```\{toctree\}\n(.*?)```", read("index.md"), re.S)
    listed = [line.strip() for block in blocks for line in block.splitlines()
              if line.strip() and not line.startswith(":")]
    expected = sorted(page[:-3] for page in all_pages() if page != "index.md")
    assert len(listed) == len(set(listed))
    assert sorted(listed) == expected


def autodoc_targets() -> list[str]:
    return re.findall(r"^\.\. auto(?:function|class):: (\S+)", read("api.md"), re.M)


def test_api_reference_covers_every_top_level_export() -> None:
    api = read("api.md")
    exports = [name for name in dir(tf) if not name.startswith("_")
               and not inspect.ismodule(getattr(tf, name))]
    assert exports
    for name in exports:
        assert f"trendfollowing.{name}" in api, name


def test_api_targets_import() -> None:
    targets = autodoc_targets()
    assert len(targets) == len(set(targets))
    for target in targets:
        module_name, _, attribute = target.rpartition(".")
        module = importlib.import_module(module_name)
        assert hasattr(module, attribute), target


def test_cross_references_point_to_documented_objects() -> None:
    targets = set(autodoc_targets())
    for page in all_pages():
        for target in re.findall(r"\{py:(?:func|class)\}`([^`\s][^`]*)`", read(page)):
            assert target in targets, f"{page}: {target}"


@pytest.mark.parametrize("page", all_pages())
def test_mathematics_is_portable_to_github(page: str) -> None:
    prose = without_code(read(page))
    for token in ("\\,", "\\{", "\\}", "\\|", "\\mathsf{T}", "\\intercal"):
        assert token not in prose, f"{page}: {token}"
    for display in re.findall(r"^\$\$\n(.*?)\n\$\$$", prose, re.S | re.M):
        for line in display.splitlines():
            assert not re.match(r"^\s*[-+*>#]", line), f"{page}: {line}"
    # GitHub can pair an underscore after a closing bracket with a later subscript as emphasis;
    # attach subscripts to a letter instead, as in s_t^{\ast} rather than s^{\ast}_t
    for math in re.findall(r"\$\$.*?\$\$|\$[^$\n]+\$", prose, re.S):
        assert not re.search(r"[)}\]]_", math), f"{page}: {math[:80]}"


@pytest.mark.parametrize("page", all_pages())
def test_figures_are_approved_manuscript_figures(page: str) -> None:
    for target in re.findall(r"!\[[^\]]+\]\(([^)]+)\)", read(page)):
        path = (DOCS_ROOT / target).resolve()
        assert path.parent == FIGURES_ROOT.resolve(), f"{page}: {target}"
        assert path.is_file(), f"{page}: {target}"
