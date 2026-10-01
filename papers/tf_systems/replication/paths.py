"""Frozen reference inputs and external writable paths for paper replication."""

import os
from pathlib import Path
import tempfile

PAPER_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_DIR = PAPER_DIR.parents[1]
REFERENCE_DIR = Path(__file__).resolve().parent / "data" / "reference"


def validate_output_path(value: str) -> Path:
    """Require an absolute destination outside the source checkout and OneDrive."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError("Paper output paths must be absolute")
    path = path.resolve()
    if path == REPOSITORY_DIR or REPOSITORY_DIR in path.parents:
        raise ValueError("Paper outputs must be outside the checkout")
    if any(part.casefold().startswith("onedrive") for part in path.parts):
        raise ValueError("Paper outputs must be outside OneDrive")
    return path


def output_root() -> Path:
    """Use an explicit run root, the configured runtime, or platform local storage."""
    if os.environ.get("TF_PAPER_OUTPUT_PATH"):
        return validate_output_path(os.environ["TF_PAPER_OUTPUT_PATH"])
    if os.environ.get("AGENT_LOCAL_ROOT"):
        root = Path(os.environ["AGENT_LOCAL_ROOT"]) / "outputs" / "tf_systems"
    else:
        root = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "TrendFollowingSystems" / "tf_systems"
    return validate_output_path(str(root))


def get_results_path() -> str:
    """Return and create the mutable cache directory, separate from references."""
    path = output_root() / "results"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_figure_path() -> str:
    """Return a validated figure directory with a trailing separator for old callers."""
    override = os.environ.get("TF_FIGURE_PATH")
    path = validate_output_path(override) if override else output_root() / "figures"
    path.mkdir(parents=True, exist_ok=True)
    return str(path) + os.sep
