"""Sphinx configuration for the trendfollowing documentation site."""

import os
from importlib.metadata import PackageNotFoundError, version as distribution_version


project = "trendfollowing"
author = "Artur Sepp and Vladimir Lucic"
copyright = "2026, Artur Sepp and Vladimir Lucic"

try:
    release = distribution_version("trendfollowing")
except PackageNotFoundError:
    release = "development"
version = release

extensions = ["myst_parser", "sphinx_sitemap"]
source_suffix = {".md": "markdown"}
root_doc = "index"
language = "en"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
nitpicky = True

html_theme = "alabaster"
html_title = "trendfollowing documentation"
html_short_title = "trendfollowing"
html_baseurl = os.environ.get(
    "READTHEDOCS_CANONICAL_URL",
    "https://trendfollowingsystems.readthedocs.io/en/latest/",
)
html_extra_path = ["robots.txt"]
html_theme_options = {
    "description": "Closed-form trend-following analytics and reproducible futures evidence",
    "github_button": True,
    "github_repo": "TrendFollowingSystems",
    "github_type": "star",
    "github_user": "ArturSepp",
    "page_width": "1100px",
    "sidebar_width": "270px",
}

myst_heading_anchors = 3
myst_html_meta = {
    "description lang=en": (
        "trendfollowing provides closed-form trend-following analytics, reference system "
        "implementations, and reproducible futures evidence in Python."
    ),
    "keywords": (
        "trend-following, time-series momentum, managed futures, quantitative finance, Python"
    ),
    "google-site-verification": "cddUZk3Gsd1MySw42Rwuq_rMzUDcMNkJWekObx-QS9Y",
}

sitemap_url_scheme = "{link}"
sitemap_indent = 2


def _use_root_canonical(app, pagename, templatename, context, doctree) -> None:
    """Use the HTTPS site root, rather than index.html, as the landing canonical."""
    if pagename == "index":
        context["pageurl"] = app.config.html_baseurl


def setup(app) -> None:
    """Register documentation build hooks."""
    app.connect("html-page-context", _use_root_canonical)


linkcheck_retries = 2
linkcheck_timeout = 30
linkcheck_workers = 5
# SSRN serves the paper to browsers but rejects Sphinx's automated checker with HTTP 403.
linkcheck_ignore = [
    r"https://papers\.ssrn\.com/sol3/papers\.cfm\?abstract_id=3167787",
]
linkcheck_request_headers = {
    "*": {
        "User-Agent": (
            "Mozilla/5.0 (compatible; trendfollowing-docs-linkcheck/1.0; "
            "+https://github.com/ArturSepp/TrendFollowingSystems)"
        )
    }
}
