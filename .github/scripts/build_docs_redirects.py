"""Build a small GitHub Pages redirect site from the verified Sphinx HTML paths.

SHARED CI CORE v1.2. Keep this file identical in the four legacy Pages repositories.
Only HTTPS Read the Docs destinations are accepted. No documentation or assets are copied.
"""

import argparse
import html
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import quote, urlsplit


def validate_base_url(value: str) -> str:
    """Accept an absolute RTD version root without credentials, query, or fragment."""
    parsed = urlsplit(value)
    hostname = parsed.hostname or ""
    if (
        parsed.scheme != "https"
        or not hostname.endswith(".readthedocs.io")
        or parsed.netloc != hostname
        or parsed.query
        or parsed.fragment
        or not re.fullmatch(r"(?:/[A-Za-z0-9_-]+)*/", parsed.path)
    ):
        raise ValueError("base URL must be an HTTPS readthedocs.io root ending in /")
    return value


def validate_project_prefix(value: str) -> str:
    """Accept one GitHub project path segment, with leading and trailing slashes."""
    if not re.fullmatch(r"/[A-Za-z0-9_-][A-Za-z0-9_.-]*/", value):
        raise ValueError("project prefix must be one repository name between slashes")
    return value


def destination(base_url: str, relative: str) -> str:
    """Map an HTML filename to its fixed RTD destination, encoding path characters."""
    validate_base_url(base_url)
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative:
        raise ValueError("HTML paths must stay beneath the source directory")
    if relative == "index.html":
        return base_url
    return base_url + "/".join(quote(part, safe="-._~") for part in path.parts)


def script_json(value: str) -> str:
    """Quote strings for an inline script without permitting an HTML closing tag."""
    return (
        json.dumps(value, ensure_ascii=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def redirect_script(target: str, project_prefix: str, fallback: bool = False) -> str:
    """Preserve the browser query and fragment; keep fallback paths on the RTD host."""
    prefix = script_json(validate_project_prefix(project_prefix))
    if not fallback:
        return (
            f"window.location.replace({script_json(target)}"
            " + window.location.search + window.location.hash);"
        )
    return f"""(() => {{
  const base = {script_json(validate_base_url(target))};
  const prefix = {prefix};
  const pathname = window.location.pathname;
  let relative = pathname.startsWith(prefix) ? pathname.slice(prefix.length) : "";
  let suffix = "";
  try {{
    const parts = relative.split("/").filter(Boolean).map(decodeURIComponent);
    const unsafe = parts.some(part =>
      part === "." || part === ".." || /[\\\\/\\x00-\\x1f]/.test(part));
    if (!unsafe) {{
      suffix = parts.map(encodeURIComponent).join("/");
      if (relative.endsWith("/") && suffix) suffix += "/";
    }}
  }} catch (_) {{
    suffix = "";
  }}
  if (suffix === "index.html") suffix = "";
  window.location.replace(base + suffix + window.location.search + window.location.hash);
}})();"""


def render_redirect(target: str, project_prefix: str, fallback: bool = False) -> str:
    """Render an accessible redirect with canonical, no-JavaScript, and link fallbacks."""
    escaped = html.escape(target, quote=True)
    script = redirect_script(target, project_prefix, fallback=fallback)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,follow">
  <title>Documentation moved</title>
  <link rel="canonical" href="{escaped}">
  <noscript><meta http-equiv="refresh" content="0; url={escaped}"></noscript>
  <script>{script}</script>
</head>
<body>
  <h1>Documentation moved</h1>
  <p><a href="{escaped}">Continue to the documentation on Read the Docs.</a></p>
</body>
</html>
"""


def build_redirects(source: Path, output: Path, base_url: str, project_prefix: str) -> int:
    """Write redirects to an empty output directory without modifying source content."""
    validate_base_url(base_url)
    validate_project_prefix(project_prefix)
    source, output = source.resolve(), output.resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("source and output directories must not overlap")
    if not (source / "index.html").is_file():
        raise ValueError("source must contain a rendered Sphinx index.html")
    if output.exists() and any(output.iterdir()):
        raise ValueError("output must be empty; use a dedicated build directory")
    pages = sorted(source.rglob("*.html"))
    for page in pages:
        if page.is_symlink() or source not in page.resolve().parents:
            raise ValueError("source HTML must not link outside the rendered documentation")
    output.mkdir(parents=True, exist_ok=True)
    count = 0
    for page in pages:
        relative = page.relative_to(source)
        if relative.as_posix() == "404.html":
            continue
        target = destination(base_url, relative.as_posix())
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_redirect(target, project_prefix), encoding="utf-8")
        count += 1
    (output / "404.html").write_text(
        render_redirect(base_url, project_prefix, fallback=True), encoding="utf-8"
    )
    (output / ".nojekyll").touch()
    return count


def main() -> None:
    """Build the redirect payload using explicit repository and destination arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--project-prefix", required=True)
    args = parser.parse_args()
    count = build_redirects(args.source, args.output, args.base_url, args.project_prefix)
    print(f"Built {count} page redirects and a 404 fallback to {args.base_url}")


if __name__ == "__main__":
    main()
