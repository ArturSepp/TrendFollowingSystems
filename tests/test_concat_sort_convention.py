"""
every axis=1 ``pd.concat`` in the package and the replication code states ``sort=`` explicitly.

``pd.concat(objs, axis=1)`` joins the frames on their index, and whether the resulting union is
sorted has been changing under us. pandas 2.2 sorted the union of DatetimeIndexes whatever
``sort=`` said; pandas 3.0 honours an explicit ``sort=False`` and leaves the union in appearance
order; pandas 3.0 still sorts when no ``sort=`` is passed, under a ``Pandas4Warning`` announcing
that pandas 4 will not. A call that says nothing therefore means one thing today and another
after the next major release.

``papers/`` is covered as well as ``src/trendfollowing/``, and for the stronger reason. A backtest
nav joined to a benchmark on a different calendar is the union case, and under pandas 4 the
exhibit would be built from a panel whose time axis is out of order - no exception, a different
number in a published table. The package's own joins in ``backtests.py`` are the same shape.

So every such call states what it wants: ``sort=True`` where the joined index is dates, which is
what pandas 2.2 did, and ``sort=False`` where it is a lag, a span, a Monte-Carlo path or a fund
label, which pandas has never sorted.

Only ``axis=1`` is covered: an ``axis=0`` concat joins on the columns, which here are instrument
or statistic labels rather than dates.

The check is static - it reads the source with ``ast`` and imports nothing.

To confirm it can fail, drop ``sort=True`` from any concat in
``src/trendfollowing/backtests.py``:
the call site is reported below by file, line and the object being concatenated. That was run
before this file was committed.
"""
# packages
import ast
from pathlib import Path
from typing import List, Optional, Tuple
import pytest

# scripts, tests and code already marked for deletion carry no convention
EXCLUDED_PARTS: Tuple[str, ...] = ('examples', 'tests', 'notebooks', '_to_delete')
COVERED: Tuple[str, ...] = ('src/trendfollowing', 'papers')


def _repo_root() -> Optional[Path]:
    """return the first ancestor holding pyproject.toml, or None off an installed wheel"""
    for parent in Path(__file__).resolve().parents:
        if parent.joinpath('pyproject.toml').is_file():
            return parent
    return None


ROOT = _repo_root()


def _is_pd_concat(node: ast.Call) -> bool:
    """True for a ``pd.concat(...)`` call node"""
    func = node.func
    return (isinstance(func, ast.Attribute) and func.attr == 'concat'
            and isinstance(func.value, ast.Name) and func.value.id == 'pd')


def find_implicit_sort_sites(root: Path) -> List[str]:
    """Return one line per axis=1 pd.concat call under COVERED that omits sort=."""
    offenders = []
    for top in COVERED:
        for path in sorted(root.joinpath(top).rglob('*.py')):
            if any(part in EXCLUDED_PARTS for part in path.parts):
                continue
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not _is_pd_concat(node):
                    continue
                keywords = {kw.arg: kw for kw in node.keywords if kw.arg is not None}
                axis = keywords.get('axis')
                if axis is None or not isinstance(axis.value, ast.Constant):
                    continue
                if axis.value.value not in (1, 'columns') or 'sort' in keywords:
                    continue
                objs = ast.unparse(node.args[0]) if node.args else '<no positional objs>'
                rel = path.relative_to(root).as_posix()
                offenders.append(f"{rel}:{node.lineno}: pd.concat({objs[:60]}, axis=1) "
                                 f"omits sort=")
    return offenders


@pytest.mark.skipif(ROOT is None, reason='repository root not on disk (installed wheel)')
def test_axis1_concat_states_sort() -> None:
    """a concat that does not say whether it sorts means different things in pandas 3 and 4"""
    offenders = find_implicit_sort_sites(ROOT)
    assert not offenders, (
            "axis=1 pd.concat without an explicit sort=; pass sort=True when the index is dates, "
            "sort=False when it is labels:\n" + '\n'.join(offenders))
