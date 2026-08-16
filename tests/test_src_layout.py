"""
repository layout guards for the installable package and public examples.

The repository root stays on ``sys.path`` so pytest can import the non-installed ``papers.*``
replication modules. That exception must not allow a legacy root ``trendfollowing/`` directory
to shadow the package selected by setuptools.
"""
from pathlib import Path

import trendfollowing


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_PACKAGE = REPO_ROOT.joinpath('src', 'trendfollowing')
LEGACY_PACKAGE = REPO_ROOT.joinpath('trendfollowing')
ROOT_EXAMPLES = REPO_ROOT.joinpath('examples')


def test_installable_package_uses_src_layout() -> None:
    """only src/trendfollowing holds the installable package source."""
    assert SRC_PACKAGE.is_dir(), "src/trendfollowing is missing"
    assert SRC_PACKAGE.joinpath('__init__.py').is_file()
    assert not LEGACY_PACKAGE.exists(), (
        "the legacy root trendfollowing/ directory can shadow an installed package")


def test_checkout_import_does_not_resolve_from_legacy_root() -> None:
    """the papers.* pythonpath exception cannot mask a root package."""
    module_path = Path(trendfollowing.__file__).resolve()
    assert not module_path.is_relative_to(LEGACY_PACKAGE), (
        f"trendfollowing imported from legacy source path {module_path}")


def test_examples_stay_at_repository_root() -> None:
    """user examples remain root artifacts rather than installed package modules."""
    assert ROOT_EXAMPLES.is_dir(), "root examples/ directory is missing"
    assert any(ROOT_EXAMPLES.glob('*.py')), "root examples/ contains no Python examples"
    assert not SRC_PACKAGE.joinpath('examples').exists(), (
        "examples must stay at repository root, not inside src/trendfollowing")
