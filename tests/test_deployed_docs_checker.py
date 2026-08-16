"""Unit tests for the deployed documentation audit helpers."""

from tools.check_deployed_docs import (
    parse_html,
    parse_sitemap,
    validate_html,
    validate_robots,
)


CANONICAL = "https://example.test/project/quickstart.html"


def _valid_html() -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <title>Quickstart — example documentation</title>
    <meta name="description" content="A deterministic package quickstart.">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{CANONICAL}">
  </head>
  <body>
    <nav><a href="index.html">Home</a></nav>
    <main><h1>Quickstart</h1><p>Install the package and run the first calculation.</p></main>
  </body>
</html>"""


def test_html_parser_and_validator_accept_complete_indexable_page() -> None:
    document = parse_html(_valid_html())

    assert document.title == "Quickstart — example documentation"
    assert document.description == "A deterministic package quickstart."
    assert document.canonicals == (CANONICAL,)
    assert document.has_navigation
    assert "Install the package" in document.primary_text
    assert validate_html(CANONICAL, CANONICAL, document, {}) == []


def test_html_validator_rejects_noindex_and_competing_canonical() -> None:
    document = parse_html(
        _valid_html()
        .replace("index, follow", "noindex, nosnippet")
        .replace(CANONICAL, "https://example.test/competing.html")
    )

    errors = validate_html(CANONICAL, CANONICAL, document, {})

    assert any("canonical" in error for error in errors)
    assert any("noindex" in error for error in errors)
    assert any("nosnippet" in error for error in errors)


def test_sitemap_parser_returns_unique_absolute_urls() -> None:
    sitemap = """<?xml version="1.0" encoding="utf-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.test/project/index.html</loc></url>
  <url><loc>https://example.test/project/quickstart.html</loc></url>
</urlset>"""

    assert parse_sitemap(sitemap) == (
        "https://example.test/project/index.html",
        "https://example.test/project/quickstart.html",
    )


def test_robots_validator_rejects_project_exclusion() -> None:
    expected_sitemap = "https://example.test/project/sitemap.xml"
    valid = f"User-agent: *\nAllow: /\nSitemap: {expected_sitemap}\n"
    blocked = f"User-agent: *\nDisallow: /project/\nSitemap: {expected_sitemap}\n"

    assert validate_robots(valid, expected_sitemap, "/project/") == []
    assert any(
        "blocks" in error for error in validate_robots(blocked, expected_sitemap, "/project/")
    )
