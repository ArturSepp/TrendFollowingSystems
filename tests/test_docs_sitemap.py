"""Build the real site configuration and compare sitemap entries with canonical tags."""

from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree

import pytest

ROOT = next((p for p in Path(__file__).resolve().parents
             if (p / "docs/conf.py").is_file()), None)
if ROOT is None:
    pytest.skip("documentation sources are absent from an installed wheel", allow_module_level=True)
BASE = "https://trendfollowingsystems.readthedocs.io/en/"
CHECK_HELPERS = False


class Head(HTMLParser):
    """Collect rendered canonical links from a page head."""

    def __init__(self):
        super().__init__()
        self.canonicals = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "link" and attributes.get("rel") == "canonical":
            self.canonicals.append(attributes["href"])


@pytest.mark.parametrize("channel", [None, "latest", "stable", "0.1.0"],
                         ids=["local", "latest", "stable", "tagged"])
def test_sitemap_agrees_with_rendered_canonicals(monkeypatch, tmp_path, channel):
    """Keep root aliases, version channels and incremental builds consistent."""
    pytest.importorskip("sphinx")
    pytest.importorskip("furo")
    if channel is None:
        monkeypatch.delenv("READTHEDOCS_CANONICAL_URL", raising=False)
    else:
        monkeypatch.setenv("READTHEDOCS_CANONICAL_URL", BASE + channel + "/")
    base = BASE + (channel or "latest") + "/"
    source = tmp_path / "source"
    source.mkdir()
    output = tmp_path / "html"
    index = "Home\n====\n\n.. toctree::\n\n   chapter\n"
    if CHECK_HELPERS:
        index += "   hidden\n   moved\n"
        (source / "hidden.rst").write_text(
            "Hidden\n======\n\n.. meta::\n   :robots: noindex, follow\n", encoding="utf-8")
        (source / "moved.rst").write_text(
            "Moved\n=====\n\n.. meta::\n   :http-equiv=refresh: 0; url=chapter.html\n",
            encoding="utf-8")
    (source / "index.rst").write_text(index, encoding="utf-8")
    (source / "chapter.rst").write_text("Chapter\n=======\n\nText.\n", encoding="utf-8")

    def build():
        """Use this package's complete configuration with a small offline source tree."""
        result = subprocess.run(
            [sys.executable, "-m", "sphinx", "-W", "-q", "-b", "html",
             "-c", str(ROOT / "docs"), "-D", "source_suffix=.rst", str(source), str(output)],
            capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, result.stdout + result.stderr

    def locations():
        """Read actual output and require a sitemap that does not repeat URLs."""
        file = output / "sitemap.xml"
        assert file.is_file(), "the HTML build must publish a canonical page sitemap"
        urls = [n.text for n in ElementTree.parse(file).iter(
            "{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        assert len(urls) == len(set(urls))
        return set(urls)

    build()
    assert locations() == {base, base + "chapter.html"}
    for name, canonical in (("index", base), ("chapter", base + "chapter.html")):
        head = Head()
        head.feed((output / (name + ".html")).read_text(encoding="utf-8").split("</head>")[0])
        assert head.canonicals == [canonical]
    # An incremental build must retain unchanged pages, not just its new page.
    (source / "second.rst").write_text("Second\n======\n\nNew page.\n", encoding="utf-8")
    (source / "index.rst").write_text(index + "   second\n", encoding="utf-8")
    build()
    assert locations() == {base, base + "chapter.html", base + "second.html"}
