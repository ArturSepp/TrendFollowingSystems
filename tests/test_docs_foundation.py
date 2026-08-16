"""Repository-level guards for the U3a documentation foundation."""

from pathlib import Path
import runpy


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPOSITORY_ROOT / "docs"
CANONICAL_DOCS_URL = "https://artursepp.github.io/TrendFollowingSystems/"


def test_sphinx_configuration_uses_canonical_url_and_myst() -> None:
    config = runpy.run_path(str(DOCS_ROOT / "conf.py"))

    assert config["root_doc"] == "index"
    assert config["source_suffix"] == {".md": "markdown"}
    assert config["extensions"] == ["myst_parser"]
    assert config["html_baseurl"] == CANONICAL_DOCS_URL


def test_landing_page_routes_every_required_destination() -> None:
    landing_page = (DOCS_ROOT / "index.md").read_text(encoding="utf-8")
    required_routes = (
        "quickstart",
        "workflows",
        "api",
        "paper",
        "CHANGELOG.md",
        "github.com/ArturSepp/TrendFollowingSystems",
        "github.com/ArturSepp/TrendFollowingSystems/issues",
        "CITATION.cff",
        "pypi.org/project/trendfollowing/",
        "github.com/ArturSepp/QuantInvestStrats",
    )

    for route in required_routes:
        assert route in landing_page


def test_docs_extra_and_ignored_build_output_are_declared() -> None:
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    gitignore = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "docs = [" in pyproject
    assert '"sphinx>=7.2"' in pyproject
    assert '"myst-parser>=2.0"' in pyproject
    assert "docs/_build/" in gitignore


def test_pages_workflow_builds_checks_and_deploys_documentation() -> None:
    workflow = (
        REPOSITORY_ROOT / ".github" / "workflows" / "docs.yml"
    ).read_text(encoding="utf-8")

    required_contract = (
        'python -m pip install -e ".[docs]"',
        "sphinx-build -W --keep-going -b html docs docs/_build/html",
        "sphinx-build -W --keep-going -b linkcheck docs docs/_build/linkcheck",
        "actions/configure-pages@v5",
        "actions/upload-pages-artifact@v4",
        "actions/deploy-pages@v4",
        "pages: read",
        "pages: write",
        "id-token: write",
        "name: github-pages",
    )

    for entry in required_contract:
        assert entry in workflow
