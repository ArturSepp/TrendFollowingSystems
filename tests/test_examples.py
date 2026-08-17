"""Smoke and drift tests for the public root examples."""

from importlib.metadata import version
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest
import trendfollowing as tf
from trendfollowing.systems.european import run_european_tf_system
from trendfollowing.universe import load_data


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = REPOSITORY_ROOT / "examples"
QUICKSTART = EXAMPLES_ROOT / "quickstart.py"
CLOSED_FORM_GUIDE = REPOSITORY_ROOT / "docs" / "closed_form_analytics.md"
PREDICT_SHARPE_GUIDE = REPOSITORY_ROOT / "docs" / "predict_sharpe_from_acf.md"
PUBLIC_ANALYTICS_SYMBOLS = (
    "population_acf",
    "compute_annualised_sharpe",
    "expected_annual_return",
    "expected_turnover",
    "skewness_white_noise",
    "sharpe_white_noise",
    "sharpe_white_noise_approx",
    "sharpe_ar1",
    "sharpe_ar1_approx",
    "sharpe_arfima",
)
PREDICTION_GUIDE_SYMBOLS = (
    ("tf.compute_annualised_sharpe", tf.compute_annualised_sharpe),
    ("tf.compute_realized_sharpe", tf.compute_realized_sharpe),
    ("trendfollowing.universe.load_data", load_data),
    ("trendfollowing.systems.european.run_european_tf_system", run_european_tf_system),
)
EXPECTED_QUICKSTART_LINES = (
    "AR(1): phi=+0.050, span=63 days, annualized Sharpe=0.200195",
    "ARFIMA(0,d,0): d=0.020, span=63 days, annualized Sharpe=0.288820",
    "Conventions: 260 trading days/year; zero underlying drift; one EWMA filter.",
    "Try next: change PHI, D, or LONG_SPAN near the top of examples/quickstart.py.",
)
CLAIMED_EXAMPLES = (
    (
        "analytic_sharpe_vs_span.py",
        ("gross    net",),
        {"example_arfima_interior_optimum.png"},
    ),
    (
        "predict_sharpe_from_acf.py",
        (
            "ES1 Index       0.227     0.206",
            "TY1 Comdty      0.942     0.649",
            "GC1 Comdty      0.283     0.234",
            "C 1 Comdty      0.625     0.620",
        ),
        set(),
    ),
    (
        "backtest_european_system.py",
        ("sharpe       1.095",),
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


def test_closed_form_guide_routes_to_public_api_and_authoritative_example() -> None:
    assert tf.AF_DAILY == 260
    for name in PUBLIC_ANALYTICS_SYMBOLS:
        assert callable(getattr(tf, name, None)), name

    guide = CLOSED_FORM_GUIDE.read_text(encoding="utf-8")
    landing_page = (REPOSITORY_ROOT / "docs" / "index.md").read_text(encoding="utf-8")

    for name in PUBLIC_ANALYTICS_SYMBOLS:
        assert f"`tf.{name}`" in guide
    for term in (
        "white noise",
        "AR(1)",
        "ARFIMA",
        "empirical ACF",
        "arithmetic simple-excess-return Sharpe",
        "`long_span`",
        "`short_span`",
        "`sr_underlying`",
        "`af`",
        "Failure modes",
        "Non-goals",
    ):
        assert term in guide
    assert "examples/analytic_sharpe_vs_span.py" in guide
    assert "python examples/analytic_sharpe_vs_span.py" in guide
    assert "closed_form_analytics" in landing_page


def test_prediction_guide_routes_to_built_symbols_and_authoritative_example() -> None:
    for label, symbol in PREDICTION_GUIDE_SYMBOLS:
        assert callable(symbol), label

    guide = PREDICT_SHARPE_GUIDE.read_text(encoding="utf-8")
    landing_page = (REPOSITORY_ROOT / "docs" / "index.md").read_text(encoding="utf-8")

    for label, _ in PREDICTION_GUIDE_SYMBOLS:
        assert f"`{label}`" in guide
    for term in (
        "point-in-time",
        "in-sample descriptive",
        "Volatility normalization",
        "`vol.shift(1)`",
        "lags 1 through 779",
        "`sr_underlying`",
        "`ddof=1`",
        "arithmetic simple-excess-return Sharpe",
        "replication result",
        "not a promise of future performance",
        "Data coverage",
        "Missing observations",
        "Estimation risk",
    ):
        assert term in guide
    assert "examples/predict_sharpe_from_acf.py" in guide
    assert "python examples/predict_sharpe_from_acf.py" in guide
    assert "predict_sharpe_from_acf" in landing_page


def test_quickstart_runs_offline_without_output_files(tmp_path: Path) -> None:
    stdout, elapsed = _run_example(QUICKSTART, tmp_path, timeout=60.0)

    assert stdout.splitlines()[0] == f"trendfollowing {version('trendfollowing')}"
    for expected_line in EXPECTED_QUICKSTART_LINES:
        assert expected_line in stdout
    assert elapsed < 60.0
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("filename", "expected_outputs", "expected_files"),
    CLAIMED_EXAMPLES,
)
def test_claimed_examples_run_headlessly_from_temporary_directory(
    filename: str,
    expected_outputs: tuple[str, ...],
    expected_files: set[str],
    tmp_path: Path,
) -> None:
    stdout, _ = _run_example(EXAMPLES_ROOT / filename, tmp_path, timeout=120.0)

    for expected_output in expected_outputs:
        assert expected_output in stdout
    assert {path.name for path in tmp_path.iterdir()} == expected_files
