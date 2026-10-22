"""Unit tests for the deployed documentation audit helpers."""

from dataclasses import replace
from pathlib import Path

import pytest
import tools.check_deployed_docs as audit

from tools.check_deployed_docs import (
    DEFAULT_ROOT,
    PAGE_PATHS,
    parse_html,
    parse_sitemap,
    validate_html,
    validate_robots,
)


CANONICAL = "https://example.test/project/quickstart.html"


def test_deployed_audit_defaults_to_readthedocs() -> None:
    assert DEFAULT_ROOT == "https://trendfollowingsystems.readthedocs.io/en/latest/"
    assert PAGE_PATHS["landing"] == ("", "")


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


def _quickstart_html() -> str:
    return """<main><article>
<p>Verified setup: <strong>trendfollowing 1.4.0</strong> on <strong>Python 3.11</strong>.</p>
<p>Requires patched Pillow 13.0.0 or newer.</p>
<pre>python -m pip install <span>"trendfollowing==1.4.0"</span>
Invoke-WebRequest 'https://raw.githubusercontent.com/ArturSepp/TrendFollowingSystems/2248d9bf866c3b2067c2e4ad1ef9cf7121d80fc5/examples/quickstart.py'
python quickstart.py</pre>
</article></main>"""


def test_quickstart_audit_accepts_syntax_highlighting_and_current_source() -> None:
    assert audit.validate_quickstart(parse_html(_quickstart_html())) == []
    source = Path(__file__).resolve().parents[1].joinpath('docs/quickstart.md').read_text(
        encoding='utf-8')
    # The deployed contract must be advanced deliberately with the released workflow.
    assert f'trendfollowing=={audit.QUICKSTART_VERSION}' in source
    assert f'Python {audit.QUICKSTART_PYTHON}' in source
    assert f'Pillow {audit.QUICKSTART_PILLOW} or newer' in source
    assert audit.QUICKSTART_SCRIPT in source


@pytest.mark.parametrize(('old', 'new', 'error_fragment'), [
    ('trendfollowing 1.4.0', 'trendfollowing 1.3.1', 'setup'),
    ('Python 3.11', 'Python 3.12', 'setup'),
    ('trendfollowing==1.4.0', 'trendfollowing==1.3.1', 'install'),
    ('trendfollowing==1.4.0', 'trendfollowing', 'install'),
    ('Pillow 13.0.0', 'Pillow 12.3.0', 'Pillow'),
    ('2248d9bf866c3b2067c2e4ad1ef9cf7121d80fc5', 'main', 'script'),
    ('2248d9bf866c3b2067c2e4ad1ef9cf7121d80fc5',
     'b1d75d974dc1f08c63fd9763f84147779090e3bc', 'script'),
])
def test_quickstart_audit_rejects_stale_instructions(old, new, error_fragment) -> None:
    errors = audit.validate_quickstart(parse_html(_quickstart_html().replace(old, new)))
    assert any(error_fragment in error for error in errors), errors


def test_correct_sidebar_cannot_mask_stale_quickstart_or_extra_old_command() -> None:
    current = _quickstart_html()
    stale = current.replace('trendfollowing==1.4.0', 'trendfollowing==1.3.1')
    html = '<aside>' + current.replace('<main>', '').replace('</main>', '') + '</aside>'
    errors = audit.validate_quickstart(parse_html(html + stale))
    assert any('install' in error for error in errors)
    conflicting = current.replace('</pre>', '\npython -m pip install trendfollowing==1.3.1</pre>')
    assert any('install' in error for error in audit.validate_quickstart(parse_html(conflicting)))
    same_command = current.replace('trendfollowing==1.4.0',
                                   'trendfollowing==1.4.0 trendfollowing==1.3.1')
    assert any('install' in error for error in audit.validate_quickstart(parse_html(same_command)))
    bad_floor = current.replace('</article>', '<p>The package supports Python 3.10.</p></article>')
    assert any('setup' in error for error in audit.validate_quickstart(parse_html(bad_floor)))
    assert audit.validate_quickstart(parse_html('<main>Build succeeded</main>'))


def test_live_audit_checks_both_channels_and_cli_fails_on_stale_content(monkeypatch) -> None:
    visited = []

    def fetch(url, attempts, retry_delay, timeout):
        visited.append(url)
        html = _quickstart_html()
        if '/stable/' in url:
            html = html.replace('trendfollowing==1.4.0', 'trendfollowing==1.3.1')
        return audit.FetchResult(url, url, 200, {'content-type': 'text/html'}, html)

    monkeypatch.setattr(audit, '_fetch', fetch)
    assert audit.main(['--quickstarts']) == 1
    assert visited == [root + 'quickstart.html' for root in audit.QUICKSTART_ROOTS]


@pytest.mark.parametrize('failure', ['unavailable', 'redirect', 'not-html', 'status'])
def test_live_audit_fails_closed_but_still_checks_second_channel(monkeypatch, failure) -> None:
    visited = []

    def fetch(url, attempts, retry_delay, timeout):
        visited.append(url)
        if '/latest/' in url and failure == 'unavailable':
            raise RuntimeError('failed to fetch latest')
        result = audit.FetchResult(url, url, 200, {'content-type': 'text/html'}, _quickstart_html())
        if '/latest/' in url:
            if failure == 'redirect':
                result = replace(result, final_url=url.replace('/latest/', '/stable/'))
            elif failure == 'not-html':
                result = replace(result, headers={'content-type': 'application/json'})
            elif failure == 'status':
                result = replace(result, status=503)
        return result

    monkeypatch.setattr(audit, '_fetch', fetch)
    errors, summary = audit.audit_quickstarts()
    assert errors
    assert len(visited) == 2
    assert summary['quickstart_pages'] == 2
