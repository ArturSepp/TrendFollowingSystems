"""Repository-level guards for the U3a documentation foundation."""

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys
from types import SimpleNamespace

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPOSITORY_ROOT / "docs"
CANONICAL_DOCS_URL = "https://trendfollowingsystems.readthedocs.io/en/latest/"
DOCUMENTATION_URL = "https://trendfollowingsystems.readthedocs.io"


def test_sphinx_configuration_uses_canonical_url_and_myst(monkeypatch) -> None:
    monkeypatch.delenv("READTHEDOCS_CANONICAL_URL", raising=False)
    config = runpy.run_path(str(DOCS_ROOT / "conf.py"))

    assert config["root_doc"] == "index"
    assert config["source_suffix"] == {".md": "markdown"}
    assert config["extensions"] == [
        "myst_parser",
        "sphinx_sitemap",
        "sphinx.ext.autodoc",
        "trendfollowing_callouts",
    ]
    assert config["myst_enable_extensions"] == ["dollarmath"]
    assert config["nitpicky"] is True
    assert config["html_baseurl"] == CANONICAL_DOCS_URL
    assert config["html_extra_path"] == ["robots.txt"]
    assert config["sitemap_url_scheme"] == "{link}"
    assert config["myst_html_meta"]["google-site-verification"]


@pytest.mark.parametrize(
    ("service_url", "canonical_url"),
    [
        # stable and latest serve the same pages, so both name latest as canonical
        (
            "https://trendfollowingsystems.readthedocs.io/en/stable/",
            CANONICAL_DOCS_URL,
        ),
        (
            "https://trendfollowingsystems.readthedocs.io/en/1.3.0/",
            "https://trendfollowingsystems.readthedocs.io/en/1.3.0/",
        ),
    ],
)
def test_sphinx_configuration_uses_readthedocs_canonical_override(
    monkeypatch, service_url, canonical_url
) -> None:
    monkeypatch.setenv("READTHEDOCS_CANONICAL_URL", service_url)
    config = runpy.run_path(str(DOCS_ROOT / "conf.py"))
    context = {"pageurl": f"{canonical_url}index.html"}

    config["_use_root_canonical"](
        SimpleNamespace(config=SimpleNamespace(html_baseurl=config["html_baseurl"])),
        "index",
        "page.html",
        context,
        None,
    )

    assert config["html_baseurl"] == canonical_url
    assert context["pageurl"] == canonical_url


def test_built_pages_carry_short_titles_one_description_and_a_page_sitemap(
    monkeypatch, tmp_path
) -> None:
    """Build two pages with the site's templates, metadata and sitemap settings.

    Furo would otherwise end every title with the full ``html_title``, a site-wide description
    would sit beside each page's own, and the sitemap would list the noindex search page.
    """
    for module in ("sphinx", "furo", "myst_parser", "sphinx_sitemap"):
        pytest.importorskip(module)
    monkeypatch.delenv("READTHEDOCS_CANONICAL_URL", raising=False)
    config = runpy.run_path(str(DOCS_ROOT / "conf.py"))
    settings = {
        key: config[key]
        for key in (
            "project",
            "html_title",
            "html_baseurl",
            "myst_html_meta",
            "sitemap_url_scheme",
            "sitemap_excludes",
        )
        if key in config
    }
    source = tmp_path / "source"
    source.mkdir()
    (source / "conf.py").write_text(
        "extensions = ['myst_parser', 'sphinx_sitemap']\n"
        "html_theme = 'furo'\n"
        f"templates_path = [{str(DOCS_ROOT / '_templates')!r}]\n"
        + "".join(f"{key} = {value!r}\n" for key, value in settings.items()),
        encoding="utf-8",
    )
    descriptions = {"index": "The landing page.", "method": "The European system page."}
    (source / "index.md").write_text(
        f"---\nmyst:\n  html_meta:\n    description: {descriptions['index']}\n---\n\n"
        "# Home\n\n```{toctree}\nmethod\n```\n",
        encoding="utf-8",
    )
    (source / "method.md").write_text(
        f"---\nmyst:\n  html_meta:\n    description: {descriptions['method']}\n---\n\n"
        "# The European system\n\nA method.\n",
        encoding="utf-8",
    )
    output = tmp_path / "html"
    result = subprocess.run(
        [sys.executable, "-m", "sphinx", "-W", "-q", "-b", "html", str(source), str(output)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    class Head(HTMLParser):
        """Collect the description tags of a page head."""

        def __init__(self) -> None:
            super().__init__()
            self.descriptions = []

        def handle_starttag(self, tag, attrs) -> None:
            attrs = dict(attrs)
            if tag == "meta" and attrs.get("name") == "description":
                self.descriptions.append(attrs["content"])

    for name, title in (
        ("index", settings["html_title"]),
        ("method", f"The European system - {settings['project']}"),
    ):
        head = (output / f"{name}.html").read_text(encoding="utf-8").split("</head>")[0]
        assert re.findall(r"<title>(.*?)</title>", head) == [title]
        parser = Head()
        parser.feed(head)
        assert parser.descriptions == [descriptions[name]]
    sitemap = (output / "sitemap.xml").read_text(encoding="utf-8")
    assert sorted(re.findall(r"<loc>(.*?)</loc>", sitemap)) == [
        f"{CANONICAL_DOCS_URL}index.html",
        f"{CANONICAL_DOCS_URL}method.html",
    ]


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

    assert f'Documentation = "{DOCUMENTATION_URL}"' in pyproject
    assert f"]({CANONICAL_DOCS_URL})" in readme


def test_robots_file_allows_crawling_and_names_the_canonical_sitemap() -> None:
    robots = (DOCS_ROOT / "robots.txt").read_text(encoding="utf-8")

    assert "User-agent: *" in robots
    assert "Allow: /" in robots
    assert f"Sitemap: {CANONICAL_DOCS_URL}sitemap.xml" in robots


def test_pages_workflow_builds_checks_and_deploys_documentation() -> None:
    workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "docs.yml").read_text(encoding="utf-8")

    profile = json.loads((REPOSITORY_ROOT / ".github/oss-checks.json").read_text())
    assert [
        "-m",
        "sphinx",
        "-E",
        "-W",
        "--keep-going",
        "-b",
        "html",
        "docs",
        "{output}/html",
    ] in profile["docs"]
    required_contract = (
        "uv sync --locked --extra docs",
        "python .github/oss_checks.py docs --working-tree",
        "python -m sphinx -E -W -b linkcheck docs docs/_build/linkcheck",
        "actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d",
        "actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9",
        "actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346",
        "pages: read",
        "pages: write",
        "id-token: write",
        "name: github-pages",
    )

    for entry in required_contract:
        assert entry in workflow
