"""
tests that the release version locations agree.

Installed metadata, runtime metadata, `pyproject.toml`, `CITATION.cff`, and the `@software`
BibTeX entry in `README.md` all expose release identity. Updating one copy while leaving another
behind is a provenance defect for a replication package, not merely a typo.

`date-released` is checked for shape rather than value. A bare year passes a human's glance and
sorts wrong wherever the field is read as a date, Zenodo included.

`yaml` is not a declared dependency and does not need to be: `qis` is mandatory and requires
`PyYAML`, so it is present wherever `trendfollowing` is.
"""
# packages
import re
from importlib.metadata import version as distribution_version
from pathlib import Path
from typing import Optional
import pytest
import yaml

import trendfollowing

REPO_ROOT: Path = Path(__file__).resolve().parent.parent

PROJECT_VERSION = re.compile(r'^\s*version\s*=\s*["\']([^"\']+)["\']', flags=re.M)
PROJECT_DESCRIPTION = re.compile(r'^\s*description\s*=\s*["\']([^"\']+)["\']', flags=re.M)
SOFTWARE_ENTRY = re.compile(r'@software\{.*?\n\}', flags=re.S)
BIBTEX_VERSION = re.compile(r'version\s*=\s*\{([^}]+)\}')
BIBTEX_TITLE = re.compile(r'title\s*=\s*\{([^}]+)\}')

CANONICAL_ROLE = (
    'trendfollowing — closed-form trend-following analytics, reference system implementations, '
    'and reproducible futures evidence in Python for quantitative researchers and practitioners.'
)
BOUNDARY = (
    'It is a research and replication library, not a broker integration or general-purpose '
    'execution engine; portfolio analytics and reporting are delegated to qis.'
)


def _pyproject_version() -> str:
    """
    the [project] version string.

    Parsed with a regular expression rather than tomllib, which arrived in 3.11 while the
    supported floor is 3.10.

    Returns:
        the version

    Raises:
        AssertionError: when the table is no longer where the parser expects it
    """
    text = REPO_ROOT.joinpath('pyproject.toml').read_text(encoding='utf-8')
    match = PROJECT_VERSION.search(text.split('[project]', 1)[-1])
    assert match is not None, "pyproject.toml no longer has a '[project] version' entry"
    return match.group(1)


def _pyproject_description() -> str:
    """The package-index summary from the project table."""
    text = REPO_ROOT.joinpath('pyproject.toml').read_text(encoding='utf-8')
    match = PROJECT_DESCRIPTION.search(text.split('[project]', 1)[-1])
    assert match is not None, "pyproject.toml has no '[project] description' entry"
    return match.group(1)


def _citation_field(name: str) -> Optional[str]:
    """
    one top-level field of CITATION.cff.

    Args:
        name: the key to read

    Returns:
        the value as a string, or None when the key is absent
    """
    data = yaml.safe_load(REPO_ROOT.joinpath('CITATION.cff').read_text(encoding='utf-8'))
    value = data.get(name)
    return None if value is None else str(value)


def _readme_software_entry() -> str:
    """The software BibTeX entry in the README.

    Returns:
        The complete entry.

    Raises:
        AssertionError: When the entry is missing.
    """
    text = REPO_ROOT.joinpath('README.md').read_text(encoding='utf-8')
    entry = SOFTWARE_ENTRY.search(text)
    assert entry is not None, (
        "README.md has no '@software' BibTeX entry. The paper entry cites the results; the "
        "software entry cites the code that produced them, and a replication needs both")
    return entry.group(0)


def _readme_bibtex_version() -> str:
    """The version field of the README software entry."""
    match = BIBTEX_VERSION.search(_readme_software_entry())
    assert match is not None, (
        "the '@software' entry in README.md carries no version field, so a reader citing it "
        "cannot say which release they replicated")
    return match.group(1).strip()


def _collapse(text: str) -> str:
    """Collapse Markdown/YAML wrapping and remove Markdown code ticks."""
    return ' '.join(text.replace('`', '').split())


def test_citation_cff_matches_pyproject():
    """the version a citing reader copies is the version that was released."""
    citation = _citation_field('version')
    pyproject = _pyproject_version()
    assert citation == pyproject, f"CITATION.cff says {citation}, pyproject.toml says {pyproject}"


def test_readme_bibtex_matches_pyproject():
    """the README's software entry names the same release as the package metadata."""
    readme = _readme_bibtex_version()
    pyproject = _pyproject_version()
    assert readme == pyproject, (
        f"the README @software entry says {readme}, pyproject.toml says {pyproject}")


def test_runtime_version_matches_installed_distribution_and_pyproject():
    """Runtime version comes from installed metadata rather than a stale literal."""
    installed = distribution_version('trendfollowing')
    assert installed == _pyproject_version()
    assert trendfollowing.__version__ == installed


def test_primary_identity_surfaces_align():
    """README, package-index summary, and citation metadata describe one package."""
    readme = REPO_ROOT.joinpath('README.md').read_text(encoding='utf-8')
    citation = yaml.safe_load(REPO_ROOT.joinpath('CITATION.cff').read_text(encoding='utf-8'))
    readme_intro = _collapse(readme.split('[![PyPI]', 1)[0])

    assert _pyproject_description() == CANONICAL_ROLE
    assert readme_intro == _collapse(f'# trendfollowing {CANONICAL_ROLE} {BOUNDARY}')
    assert citation['title'] == 'trendfollowing'
    assert _collapse(citation['abstract']) == _collapse(f'{CANONICAL_ROLE} {BOUNDARY}')

    bibtex_title = BIBTEX_TITLE.search(_readme_software_entry())
    assert bibtex_title is not None
    assert bibtex_title.group(1).strip() == 'trendfollowing'


def test_installation_and_qis_floor_match_package_metadata():
    """The primary install command and dependency floor cannot drift from metadata."""
    readme = REPO_ROOT.joinpath('README.md').read_text(encoding='utf-8')
    pyproject = REPO_ROOT.joinpath('pyproject.toml').read_text(encoding='utf-8')
    installation = readme.split('## Installation', 1)[1].split('## Quickstart', 1)[0]

    assert installation.index('pip install trendfollowing') < installation.index('git clone')
    assert '"qis>=5.0.9"' in pyproject
    assert '`qis` >= 5.0.9' in installation


def test_citation_cff_date_released_is_a_date():
    """date-released is an ISO date; a bare year reads as one and sorts as none."""
    date_released = _citation_field('date-released')
    assert date_released is not None, "CITATION.cff has no date-released field"
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', date_released), (
        f"date-released must be YYYY-MM-DD, got {date_released!r}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
