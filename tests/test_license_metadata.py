"""Keep the MIT release identity and retained source attribution consistent."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_first_party_license_and_metadata_agree():
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert re.search(r'^license = "MIT"$', project, re.MULTILINE)
    assert re.search(r'^license: MIT$', citation, re.MULTILINE)
    assert 'license-files = ["LICENSE", "NOTICE"]' in project
    assert license_text.startswith("MIT License\n")
    assert "Copyright (c) 2026 Artur Sepp and Vladimir Lucic" in license_text
    assert "Permission is hereby granted, free of charge" in license_text
    assert "The above copyright notice and this permission notice" in license_text
    assert 'THE SOFTWARE IS PROVIDED "AS IS"' in license_text


def test_retained_upstream_notice_and_historical_scope():
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Aleksejus Kononovicius" in notice
    assert "8bcde20ba113185e9e1f8c6afaf83c55f957cd03" in notice
    assert "This is free and unencumbered software released into the public domain." in notice
    assert "Copyright (c) 2024 Artur Sepp" in notice
    assert "Permission is hereby granted, free of charge" in notice
    assert "Earlier published releases" in readme
    assert "third-party market data" in readme
