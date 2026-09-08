"""Exercise static URL mapping and the actual browser JavaScript without a network."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from build_docs_redirects import (
    build_redirects,
    destination,
    redirect_script,
    render_redirect,
    validate_base_url,
    validate_project_prefix,
)


BASE = "https://example.readthedocs.io/en/latest/"
PREFIX = "/Example/"


def run_browser_script(script: str, path: str, query: str = "", fragment: str = "") -> str:
    """Evaluate the emitted JavaScript with a minimal window.location object in Node."""
    harness = """
const fs = require('node:fs');
const vm = require('node:vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
let result;
const location = {...input.location, replace: value => { result = value; }};
vm.runInNewContext(input.script, {window: {location}}, {timeout: 1000});
process.stdout.write(JSON.stringify(result));
"""
    result = subprocess.run(
        ["node", "-e", harness],
        input=json.dumps(
            {
                "script": script,
                "location": {
                    "pathname": path,
                    "search": query,
                    "hash": fragment,
                },
            }
        ),
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    return json.loads(result.stdout)


class RedirectTests(unittest.TestCase):
    """Catch broken deep links, lost fragments, unsafe paths, and source-copy regressions."""

    def test_homepage_and_encoded_deep_page(self):
        self.assertEqual(destination(BASE, "index.html"), BASE)
        self.assertEqual(destination(BASE, "guide/schema.html"), BASE + "guide/schema.html")
        self.assertEqual(destination(BASE, "a #b.html"), BASE + "a%20%23b.html")
        for value in ["../outside.html", "/outside.html", "..\\outside.html"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                destination(BASE, value)

    def test_only_explicit_rtd_destinations_and_project_prefixes(self):
        for value in [
            "http://example.readthedocs.io/en/latest/",
            "https://evil.test/",
            "https://example.readthedocs.io.evil.test/",
            "https://user@example.readthedocs.io/",
            BASE + "?next=evil",
            BASE + "#fragment",
            BASE + "../other/",
        ]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_base_url(value)
        for value in ["//evil.test/", "/../", "Example", "/a/b/"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_project_prefix(value)

    def test_browser_preserves_query_and_fragment(self):
        target = destination(BASE, "schema.html")
        actual = run_browser_script(
            redirect_script(target, PREFIX), "/Example/schema.html", "?q=expiry", "#strike-grid"
        )
        self.assertEqual(actual, BASE + "schema.html?q=expiry#strike-grid")

    def test_404_strips_only_the_exact_project_prefix(self):
        script = redirect_script(BASE, PREFIX, fallback=True)
        self.assertEqual(
            run_browser_script(script, "/Example/old/page.html", "", "#rules"),
            BASE + "old/page.html#rules",
        )
        self.assertEqual(run_browser_script(script, "/Example/index.html"), BASE)
        self.assertEqual(run_browser_script(script, "/Example/guide/"), BASE + "guide/")
        self.assertEqual(run_browser_script(script, "/ExampleOther/page.html"), BASE)
        self.assertEqual(run_browser_script(script, "/Example/%2e%2e/elsewhere"), BASE)
        self.assertEqual(run_browser_script(script, "/Example/%2f%2fevil.test"), BASE)
        self.assertEqual(run_browser_script(script, "/Example/%5cevil.test"), BASE)
        self.assertEqual(run_browser_script(script, "/Example/%broken"), BASE)

    def test_html_and_script_escape_untrusted_characters(self):
        target = BASE + 'x?test="&</script><script>oops</script>'
        rendered = render_redirect(target, PREFIX)
        self.assertNotIn("<script>oops", rendered)
        self.assertIn("&quot;&amp;&lt;/script&gt;", rendered)
        self.assertIn('rel="canonical"', rendered)
        self.assertIn('<noscript><meta http-equiv="refresh"', rendered)
        self.assertIn('name="robots" content="noindex,follow"', rendered)
        self.assertEqual(run_browser_script(redirect_script(target, PREFIX), "/Example/x"), target)

    def test_payload_has_redirects_and_never_copies_source_or_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "source", root / "redirects"
            (source / "guide").mkdir(parents=True)
            (source / "index.html").write_text("original homepage", encoding="utf-8")
            (source / "guide/schema.html").write_text("original guide", encoding="utf-8")
            (source / "image.png").write_bytes(b"unchanged binary")
            self.assertEqual(build_redirects(source, output, BASE, PREFIX), 2)
            self.assertEqual(
                {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()},
                {"index.html", "guide/schema.html", "404.html", ".nojekyll"},
            )
            self.assertNotIn("original guide", (output / "guide/schema.html").read_text())
            self.assertEqual((source / "image.png").read_bytes(), b"unchanged binary")
            with self.assertRaises(ValueError):
                build_redirects(source, output, BASE, PREFIX)
            with self.assertRaises(ValueError):
                build_redirects(source, source / "nested", BASE, PREFIX)


if __name__ == "__main__":
    unittest.main()
