"""Smoke and drift tests for the public root examples."""

from importlib.metadata import version
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = REPOSITORY_ROOT / "examples"
QUICKSTART = EXAMPLES_ROOT / "quickstart.py"
EXPECTED_QUICKSTART_LINES = (
    "AR(1): phi=+0.050, span=63 days, annualized Sharpe=0.200195",
    "ARFIMA(0,d,0): d=0.020, span=63 days, annualized Sharpe=0.288820",
    "Conventions: 260 trading days/year; zero underlying drift; one EWMA filter.",
    "Try next: change PHI, D, or LONG_SPAN near the top of examples/quickstart.py.",
)
CLAIMED_EXAMPLES = (
    (
        "analytic_sharpe_vs_span.py",
        "gross    net",
        {"example_arfima_interior_optimum.png"},
    ),
    ("predict_sharpe_from_acf.py", "ES1 Index", set()),
    (
        "backtest_european_system.py",
        "sharpe       1.095",
        {"example_european_backtest.png"},
    ),
)


def _run_example(script: Path, working_directory: Path, timeout: float) -> tuple[str, float]:
    environment = os.environ.copy()
    environment["MPLBACKEND"] = "Agg"
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=working_directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    return completed.stdout, time.perf_counter() - started


def test_root_quickstart_is_the_single_documented_source(tmp_path: Path) -> None:
    docs = (REPOSITORY_ROOT / "docs" / "quickstart.md").read_text(encoding="utf-8")
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")

    assert EXAMPLES_ROOT.is_dir()
    assert QUICKSTART.is_file()
    assert not (REPOSITORY_ROOT / "src" / "trendfollowing" / "examples").exists()
    assert "{literalinclude} ../examples/quickstart.py" in docs
    assert ":language: python" in docs
    assert "examples/quickstart.py" in readme


def test_quickstart_runs_offline_without_output_files(tmp_path: Path) -> None:
    stdout, elapsed = _run_example(QUICKSTART, tmp_path, timeout=60.0)

    assert stdout.splitlines()[0] == f"trendfollowing {version('trendfollowing')}"
    for expected_line in EXPECTED_QUICKSTART_LINES:
        assert expected_line in stdout
    assert elapsed < 60.0
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("filename", "expected_output", "expected_files"),
    CLAIMED_EXAMPLES,
)
def test_claimed_examples_run_headlessly_from_temporary_directory(
    filename: str,
    expected_output: str,
    expected_files: set[str],
    tmp_path: Path,
) -> None:
    stdout, _ = _run_example(EXAMPLES_ROOT / filename, tmp_path, timeout=120.0)

    assert expected_output in stdout
    assert {path.name for path in tmp_path.iterdir()} == expected_files
