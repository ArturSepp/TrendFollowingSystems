"""Sphinx configuration for the trendfollowing documentation site.

The methodology chapters form one book, the trendfollowing handbook, in the style of the qis and
optimalportfolios handbooks. Three local mechanisms support it:

1. ``_ext/trendfollowing_callouts.py`` renders ``> **Insight.**`` and ``> **Pitfall.**``
   blockquotes as admonitions, so the Markdown sources stay portable to GitHub and VS Code.
2. ``api.md`` documents the public objects with autodoc, grouped by the chapter that explains
   them. The package docstrings are plain-text formula notes rather than reStructuredText, so
   ``_docstring_as_literal`` renders each one verbatim instead of parsing it as markup.
3. ``_templates/page.html`` names the package versions of the build in the page footer, and
   ``_templates/base.html`` titles pages other than the homepage ``<page title> - trendfollowing``.
"""

import os
import sys

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 metadata tests use the compatible parser.
    import tomli as tomllib
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DOCS_DIR / "_ext"))

project = "trendfollowing"
author = "Artur Sepp and Vladimir Lucic"
copyright = "2026, Artur Sepp and Vladimir Lucic"

release = tomllib.loads(
    (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
)["project"]["version"]
version = release

extensions = [
    "myst_parser",
    "sphinx_sitemap",
    "sphinx.ext.autodoc",
    "trendfollowing_callouts",
]
source_suffix = {".md": "markdown"}
root_doc = "index"
language = "en"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
templates_path = ["_templates"]
nitpicky = True
# Signatures reference numpy, pandas, qis and typing objects that have no inventory in this
# offline build; only references into trendfollowing itself are checked.
nitpick_ignore_regex = [(r"py:.*", r"^(?!trendfollowing\b).*")]

# Dollar math keeps the chapter sources portable across MyST, GitHub and VS Code.
myst_enable_extensions = ["dollarmath"]
myst_heading_anchors = 3

autodoc_typehints = "signature"
autodoc_member_order = "bysource"

html_theme = "furo"
html_title = "trendfollowing - closed-form trend-following analytics"
html_short_title = "trendfollowing"
html_baseurl = os.environ.get(
    "READTHEDOCS_CANONICAL_URL",
    "https://trendfollowingsystems.readthedocs.io/en/latest/",
)
html_extra_path = ["robots.txt"]
html_static_path = ["_static"]
html_css_files = ["trendfollowing.css"]
html_theme_options = {
    "source_repository": "https://github.com/ArturSepp/TrendFollowingSystems/",
    "source_branch": "main",
    "source_directory": "docs/",
}

# Every page states its own description in its front matter. A site-wide description here would
# be emitted beside it as a second description tag on every page.
myst_html_meta = {
    "keywords": (
        "trend-following, time-series momentum, managed futures, quantitative finance, Python"
    ),
    "google-site-verification": "cddUZk3Gsd1MySw42Rwuq_rMzUDcMNkJWekObx-QS9Y",
}

sitemap_url_scheme = "{link}"
sitemap_indent = 2
# The search page is marked noindex and the general index only lists links to other pages.
sitemap_excludes = ["search.html", "genindex.html"]

# The PDF prints the methodology chapters as one book; xelatex reads the Unicode of the prose.
latex_engine = "xelatex"
latex_documents = [
    ("index", "trendfollowing.tex", "The trendfollowing handbook", author, "manual")
]
latex_elements = {"papersize": "a4paper"}

# Packages whose versions the footer names, with their usual spelling.
BUILD_PACKAGES = {
    "qis": "qis",
    "numpy": "NumPy",
    "pandas": "pandas",
    "scipy": "SciPy",
    "numba": "Numba",
}


def _build_versions() -> str:
    """Name the package versions of this build for the footer of every page.

    The package itself is named by the source version in ``pyproject.toml``, because the pages
    document the checkout being built; a dependency missing from the environment is left out.
    """
    from importlib.metadata import PackageNotFoundError, version as installed_version

    names = []
    for distribution, label in BUILD_PACKAGES.items():
        try:
            names.append(f"{label} {installed_version(distribution)}")
        except PackageNotFoundError:
            continue
    built_with = ", ".join(names[:-1]) + f" and {names[-1]}" if len(names) > 1 else "".join(names)
    return f"Built from trendfollowing {release}" + (f" with {built_with}." if names else ".")


html_context = {"build_versions": _build_versions()}


def _use_root_canonical(app, pagename, templatename, context, doctree) -> None:
    """Use the HTTPS site root, rather than index.html, as the landing canonical."""
    if pagename == "index":
        context["pageurl"] = app.config.html_baseurl


def _docstring_as_literal(app, what, name, obj, options, lines) -> None:
    """Render a package docstring verbatim as a literal block.

    The docstrings of trendfollowing are plain-text formula notes such as
    ``rho(m) = phi^m`` or ``|phi| < 1``, which reStructuredText would misread as references,
    substitutions or lists. A literal block keeps their exact text and layout.
    """
    if not lines:
        return
    body = [f"   {line}" if line.strip() else "" for line in lines]
    lines[:] = ["::", ""] + body + [""]


def setup(app) -> None:
    """Register documentation build hooks."""
    app.connect("html-page-context", _use_root_canonical)
    app.connect("autodoc-process-docstring", _docstring_as_literal)


linkcheck_retries = 2
linkcheck_timeout = 30
linkcheck_workers = 5
# SSRN serves the paper to browsers but rejects Sphinx's automated checker with HTTP 403.
# DOI redirects commonly end at publisher pages that answer HTTP 403 to automated clients,
# although the DOI itself remains valid; source links into this repository are checked locally.
linkcheck_ignore = [
    r"https://papers\.ssrn\.com/sol3/papers\.cfm\?abstract_id=3167787",
    r"https://doi\.org/.*",
    r"https://github\.com/ArturSepp/TrendFollowingSystems/(?:blob|tree)/main/.*",
]
linkcheck_request_headers = {
    "*": {
        "User-Agent": (
            "Mozilla/5.0 (compatible; trendfollowing-docs-linkcheck/1.0; "
            "+https://github.com/ArturSepp/TrendFollowingSystems)"
        )
    }
}
