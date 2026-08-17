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
    assert config["extensions"] == ["myst_parser", "sphinx_sitemap"]
    assert config["html_baseurl"] == CANONICAL_DOCS_URL
    assert config["html_extra_path"] == ["robots.txt"]
    assert config["sitemap_url_scheme"] == "{link}"
    assert config["myst_html_meta"]["google-site-verification"]


def test_landing_page_routes_every_required_destination() -> None:
    landing_page = (DOCS_ROOT / "index.md").read_text(encoding="utf-8")
    required_routes = (
        "quickstart",
        "choosing_a_backtesting_tool",
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


def test_package_choice_guide_has_dated_neutral_source_contract() -> None:
    guide = (DOCS_ROOT / "choosing_a_backtesting_tool.md").read_text(encoding="utf-8")

    required_content = (
        "2026-08-17",
        "## Overlap and different design goals",
        "## Capability matrix",
        "## Workflow-based decision guide",
        "## Where `trendfollowing` is specialized",
        "## Where broader tools are a better fit",
        "## Methodology, versions, sources, and limitations",
        "pysystemtrade 1.8.2",
        "vectorbt 1.1.0",
        "Backtesting.py 0.6.6",
        "Not identified",
        "No universal winner",
        "https://github.com/pst-group/pysystemtrade",
        "https://github.com/polakowo/vectorbt",
        "https://github.com/kernc/backtesting.py",
        "Apache 2.0 with Commons Clause",
        "AGPL-3.0",
    )

    for entry in required_content:
        assert entry in guide


def test_docs_extra_and_ignored_build_output_are_declared() -> None:
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    gitignore = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "docs = [" in pyproject
    assert '"sphinx>=7.2"' in pyproject
    assert '"myst-parser>=2.0"' in pyproject
    assert '"sphinx-sitemap>=2.9"' in pyproject
    assert "docs/_build/" in gitignore


def test_public_entry_points_use_the_canonical_docs_url() -> None:
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")

    assert f'Documentation = "{CANONICAL_DOCS_URL}"' in pyproject
    assert f"]({CANONICAL_DOCS_URL})" in readme


def test_robots_file_allows_crawling_and_names_the_canonical_sitemap() -> None:
    robots = (DOCS_ROOT / "robots.txt").read_text(encoding="utf-8")

    assert "User-agent: *" in robots
    assert "Allow: /" in robots
    assert f"Sitemap: {CANONICAL_DOCS_URL}sitemap.xml" in robots


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
