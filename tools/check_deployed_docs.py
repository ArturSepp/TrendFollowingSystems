"""Audit the deployed trendfollowing documentation without third-party dependencies."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from html.parser import HTMLParser
import re
import sys
import time
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


DEFAULT_ROOT = "https://trendfollowingsystems.readthedocs.io/en/latest/"
PAGE_PATHS = {
    "landing": ("", ""),
    "quickstart": ("quickstart.html", "quickstart.html"),
    "workflows": ("workflows.html", "workflows.html"),
    "api": ("api.html", "api.html"),
    "paper": ("paper.html", "paper.html"),
}
TASK_PAGE_NAMES = ("quickstart", "workflows", "api", "paper")
REQUIRED_EXTERNAL_LINKS = {
    "PyPI": "https://pypi.org/project/trendfollowing/",
    "source": "https://github.com/ArturSepp/TrendFollowingSystems",
    "issues": "https://github.com/ArturSepp/TrendFollowingSystems/issues",
    "changelog": (
        "https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CHANGELOG.md"
    ),
    "citation": (
        "https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff"
    ),
    "paper": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787",
    "qis": "https://github.com/ArturSepp/QuantInvestStrats",
}
USER_AGENT = (
    "trendfollowing-deployed-docs-audit/1.0 "
    "(+https://github.com/ArturSepp/TrendFollowingSystems)"
)
_VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


@dataclass(frozen=True)
class HtmlDocument:
    """Crawler-relevant fields extracted from one server-rendered HTML page."""

    title: str
    description: str
    canonicals: tuple[str, ...]
    robots_directives: tuple[str, ...]
    primary_text: str
    links: tuple[str, ...]
    has_navigation: bool


@dataclass(frozen=True)
class FetchResult:
    """One HTTP response after redirect handling."""

    requested_url: str
    final_url: str
    status: int
    headers: Mapping[str, str]
    text: str


class _AuditHtmlParser(HTMLParser):
    """Extract only the HTML fields needed by the deployed audit."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.description = ""
        self.canonicals: list[str] = []
        self.robots_directives: list[str] = []
        self.primary_parts: list[str] = []
        self.links: list[str] = []
        self.has_navigation = False
        self._in_title = False
        self._primary_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()

        if tag == "title":
            self._in_title = True
        if tag == "main" or attributes.get("role", "").lower() == "main":
            self._primary_depth = 1
        elif self._primary_depth and tag not in _VOID_ELEMENTS:
            self._primary_depth += 1

        role = attributes.get("role", "").lower()
        if tag == "nav" or role == "navigation":
            self.has_navigation = True

        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"].strip())
        if tag == "link" and "canonical" in attributes.get("rel", "").lower().split():
            href = attributes.get("href", "").strip()
            if href:
                self.canonicals.append(href)
        if tag == "meta":
            name = attributes.get("name", "").lower()
            content = attributes.get("content", "").strip()
            if name == "description" and content:
                self.description = content
            if name in {"robots", "googlebot"} and content:
                self.robots_directives.append(content)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in _VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        if self._primary_depth:
            self._primary_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._primary_depth:
            self.primary_parts.append(data)


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _normalise_url(url: str) -> str:
    clean_url, _ = urldefrag(url.strip())
    parsed = urlsplit(clean_url)
    return urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, parsed.query, "")
    )


def parse_html(html: str) -> HtmlDocument:
    """Extract crawler-relevant fields from HTML text."""

    parser = _AuditHtmlParser()
    parser.feed(html)
    parser.close()
    return HtmlDocument(
        title=_collapse_whitespace("".join(parser.title_parts)),
        description=_collapse_whitespace(parser.description),
        canonicals=tuple(_normalise_url(url) for url in parser.canonicals),
        robots_directives=tuple(parser.robots_directives),
        primary_text=_collapse_whitespace(" ".join(parser.primary_parts)),
        links=tuple(parser.links),
        has_navigation=parser.has_navigation,
    )


def _directive_tokens(values: tuple[str, ...]) -> set[str]:
    return {
        token.lower()
        for value in values
        for token in re.split(r"[\s,;]+", value)
        if token
    }


def validate_html(
    page_url: str,
    expected_canonical: str,
    document: HtmlDocument,
    headers: Mapping[str, str],
) -> list[str]:
    """Return crawler and server-rendering defects for one HTML document."""

    errors: list[str] = []
    label = _normalise_url(page_url)
    expected = _normalise_url(expected_canonical)
    if not document.title:
        errors.append(f"{label}: missing server-rendered title")
    if not document.description:
        errors.append(f"{label}: missing server-rendered description")
    if document.canonicals != (expected,):
        errors.append(
            f"{label}: expected one canonical {expected!r}, got {document.canonicals!r}"
        )
    if len(document.primary_text) < 40:
        errors.append(f"{label}: missing substantive server-rendered primary content")
    if not document.has_navigation:
        errors.append(f"{label}: missing server-rendered navigation")

    header_directives = tuple(
        value
        for name, value in headers.items()
        if name.lower() == "x-robots-tag"
    )
    directives = _directive_tokens(document.robots_directives + header_directives)
    for forbidden in ("noindex", "nosnippet"):
        if forbidden in directives:
            errors.append(f"{label}: forbidden crawler directive {forbidden!r}")
    return errors


def parse_sitemap(xml_text: str) -> tuple[str, ...]:
    """Parse and structurally validate a URL-set sitemap."""

    root = ET.fromstring(xml_text)
    if root.tag.rsplit("}", maxsplit=1)[-1] != "urlset":
        raise ValueError("sitemap root must be urlset")
    urls = tuple(
        _normalise_url(element.text or "")
        for element in root.iter()
        if element.tag.rsplit("}", maxsplit=1)[-1] == "loc"
    )
    if not urls:
        raise ValueError("sitemap contains no URLs")
    if any(not urlsplit(url).scheme or not urlsplit(url).netloc for url in urls):
        raise ValueError("sitemap URLs must be absolute")
    if len(urls) != len(set(urls)):
        raise ValueError("sitemap contains duplicate URLs")
    return urls


def validate_robots(
    text: str,
    expected_sitemap: str,
    project_path: str,
) -> list[str]:
    """Return defects in the public robots policy for this project path."""

    errors: list[str] = []
    lines = [line.split("#", maxsplit=1)[0].strip() for line in text.splitlines()]
    directives = [
        (name.strip().lower(), value.strip())
        for line in lines
        if line and ":" in line
        for name, value in [line.split(":", maxsplit=1)]
    ]
    if ("user-agent", "*") not in directives:
        errors.append("robots.txt: missing User-agent: * policy")
    sitemap_urls = {
        _normalise_url(value) for name, value in directives if name == "sitemap"
    }
    expected = _normalise_url(expected_sitemap)
    if expected not in sitemap_urls:
        errors.append(f"robots.txt: missing canonical sitemap {expected!r}")

    normalised_path = "/" + project_path.strip("/") + "/"
    for name, value in directives:
        if name != "disallow" or not value:
            continue
        if value.strip() == "/":
            rule = "/"
        else:
            rule = "/" + value.strip("/")
            if value.endswith("/"):
                rule += "/"
        if rule == "/" or normalised_path.startswith(rule) or rule.startswith(normalised_path):
            errors.append(f"robots.txt: rule {value!r} blocks project path {normalised_path!r}")
    return errors


def _fetch(url: str, attempts: int, retry_delay: float, timeout: float) -> FetchResult:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
                headers = {name.lower(): value for name, value in response.headers.items()}
                return FetchResult(
                    requested_url=url,
                    final_url=response.geturl(),
                    status=response.getcode(),
                    headers=headers,
                    text=payload.decode(charset, errors="replace"),
                )
        except (HTTPError, URLError, TimeoutError) as error:
            last_error = error
            if attempt < attempts:
                time.sleep(retry_delay)
    raise RuntimeError(f"failed to fetch {url!r} after {attempts} attempts: {last_error}")


def _content_type(result: FetchResult) -> str:
    return result.headers.get("content-type", "").split(";", maxsplit=1)[0].strip().lower()


def _same_origin_and_prefix(url: str, root: str) -> bool:
    candidate = urlsplit(_normalise_url(url))
    base = urlsplit(_normalise_url(root))
    return (
        candidate.scheme == base.scheme
        and candidate.netloc == base.netloc
        and candidate.path.startswith(base.path)
    )


def audit_site(
    root: str,
    attempts: int = 3,
    retry_delay: float = 1.0,
    timeout: float = 15.0,
) -> tuple[list[str], dict[str, int]]:
    """Audit deployed priority pages, crawler controls, navigation, and sitemap."""

    root = root.rstrip("/") + "/"
    parsed_root = urlsplit(root)
    if parsed_root.scheme != "https" or not parsed_root.netloc:
        return [f"root must be an absolute HTTPS URL: {root!r}"], {}

    errors: list[str] = []
    pages: dict[str, tuple[FetchResult, HtmlDocument, str]] = {}
    for name, (request_path, canonical_path) in PAGE_PATHS.items():
        requested_url = urljoin(root, request_path)
        canonical_url = urljoin(root, canonical_path)
        try:
            result = _fetch(requested_url, attempts, retry_delay, timeout)
        except RuntimeError as error:
            errors.append(str(error))
            continue
        if result.status != 200:
            errors.append(f"{requested_url}: expected HTTP 200, got {result.status}")
        if _normalise_url(result.final_url) != _normalise_url(requested_url):
            errors.append(f"{requested_url}: unexpected redirect to {result.final_url}")
        if _content_type(result) != "text/html":
            errors.append(f"{requested_url}: expected text/html, got {_content_type(result)!r}")
        document = parse_html(result.text)
        errors.extend(validate_html(requested_url, canonical_url, document, result.headers))
        pages[name] = (result, document, canonical_url)

    sitemap_url = urljoin(root, "sitemap.xml")
    robots_url = urljoin(root, "robots.txt")
    sitemap_urls: tuple[str, ...] = ()
    try:
        sitemap_result = _fetch(sitemap_url, attempts, retry_delay, timeout)
        if sitemap_result.status != 200:
            errors.append(f"{sitemap_url}: expected HTTP 200, got {sitemap_result.status}")
        if _normalise_url(sitemap_result.final_url) != _normalise_url(sitemap_url):
            errors.append(f"{sitemap_url}: unexpected redirect to {sitemap_result.final_url}")
        if _content_type(sitemap_result) not in {"application/xml", "text/xml"}:
            errors.append(
                f"{sitemap_url}: expected an XML content type, got "
                f"{_content_type(sitemap_result)!r}"
            )
        try:
            sitemap_urls = parse_sitemap(sitemap_result.text)
        except (ET.ParseError, ValueError) as error:
            errors.append(f"{sitemap_url}: invalid sitemap: {error}")
    except RuntimeError as error:
        errors.append(str(error))

    try:
        robots_result = _fetch(robots_url, attempts, retry_delay, timeout)
        if robots_result.status != 200:
            errors.append(f"{robots_url}: expected HTTP 200, got {robots_result.status}")
        if _normalise_url(robots_result.final_url) != _normalise_url(robots_url):
            errors.append(f"{robots_url}: unexpected redirect to {robots_result.final_url}")
        if _content_type(robots_result) != "text/plain":
            errors.append(
                f"{robots_url}: expected text/plain, got {_content_type(robots_result)!r}"
            )
        errors.extend(validate_robots(robots_result.text, sitemap_url, parsed_root.path))
    except RuntimeError as error:
        errors.append(str(error))

    expected_canonicals = {
        _normalise_url(urljoin(root, canonical_path))
        for _, canonical_path in PAGE_PATHS.values()
    }
    missing_from_sitemap = expected_canonicals.difference(sitemap_urls)
    if missing_from_sitemap:
        errors.append(
            "sitemap.xml: missing priority canonical URLs: "
            + ", ".join(sorted(missing_from_sitemap))
        )
    for sitemap_entry in sitemap_urls:
        if not _same_origin_and_prefix(sitemap_entry, root):
            errors.append(f"sitemap.xml: URL is outside the canonical HTTPS root: {sitemap_entry}")

    landing = pages.get("landing")
    if landing:
        landing_result, landing_document, _ = landing
        landing_links = {
            _normalise_url(urljoin(landing_result.final_url, href))
            for href in landing_document.links
        }
        for name in TASK_PAGE_NAMES:
            expected = _normalise_url(pages[name][2]) if name in pages else ""
            if expected and expected not in landing_links:
                errors.append(f"landing page: no internal link to {name} page {expected}")

    all_links = {
        _normalise_url(urljoin(result.final_url, href))
        for result, document, _ in pages.values()
        for href in document.links
        if href and not href.startswith(("mailto:", "javascript:"))
    }
    for label, required_url in REQUIRED_EXTERNAL_LINKS.items():
        if _normalise_url(required_url) not in all_links:
            errors.append(f"deployed docs: missing required {label} link {required_url}")

    summary = {
        "priority_pages": len(pages),
        "sitemap_urls": len(sitemap_urls),
        "external_link_routes": len(REQUIRED_EXTERNAL_LINKS),
    }
    return errors, summary


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=DEFAULT_ROOT,
        help="Canonical deployed documentation root",
    )
    parser.add_argument("--attempts", type=int, default=3, help="Bounded attempts per URL")
    parser.add_argument("--retry-delay", type=float, default=1.0, help="Seconds between attempts")
    parser.add_argument("--timeout", type=float, default=15.0, help="Seconds per HTTP request")
    args = parser.parse_args(argv)
    if args.attempts < 1:
        parser.error("--attempts must be at least 1")
    if args.retry_delay < 0:
        parser.error("--retry-delay must be non-negative")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return args


def main(argv: list[str] | None = None) -> int:
    """Run the command-line deployed documentation audit."""

    args = _parse_args(argv)
    errors, summary = audit_site(
        root=args.root,
        attempts=args.attempts,
        retry_delay=args.retry_delay,
        timeout=args.timeout,
    )
    if errors:
        print("FAIL: deployed documentation audit", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("PASS: deployed documentation audit")
    print(f"- root: {args.root.rstrip('/') + '/'}")
    print(f"- priority HTML pages: {summary['priority_pages']}")
    print(f"- sitemap URLs: {summary['sitemap_urls']}")
    print(f"- required outbound routes: {summary['external_link_routes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
