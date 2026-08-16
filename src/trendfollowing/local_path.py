"""Resolve immutable package resources and external writable folders.

The futures dataset is read from package data unless ``TF_RESOURCE_PATH`` is set.
Paper caches and generated output remain outside the installed package. In a source
checkout their relative settings resolve against the repository root; in an installed
environment they resolve under ``~/.trendfollowing``.
"""
# packages
import os
import yaml
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Dict

_SETTINGS_PATH = Path(__file__).parent.joinpath('settings.yaml')
_REPO_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def get_paths() -> Dict[str, str]:
    """read path specs in settings.yaml; cached after first call.
    call get_paths.cache_clear() to force a re-read."""
    with open(_SETTINGS_PATH) as settings:
        settings_data = yaml.safe_load(settings)
    return settings_data


def _external_root() -> Path:
    """Repository root for a checkout, otherwise a user-owned data directory."""
    source_package = _REPO_ROOT.joinpath('src', 'trendfollowing')
    if _REPO_ROOT.joinpath('pyproject.toml').is_file() and source_package.is_dir():
        return _REPO_ROOT
    return Path.home().joinpath('.trendfollowing')


def _resolve_external(key: str, env_var: str = None) -> str:
    """Absolute external path for a settings key, with an environment override.

    Raises:
        KeyError: if the key is missing from settings.yaml
    """
    if env_var is not None and os.environ.get(env_var):
        path = Path(os.environ[env_var])
    else:
        path = Path(get_paths()[key])
        if not path.is_absolute():
            path = _external_root().joinpath(path)
    return str(path) + os.sep


def get_resource_path() -> str:
    """Read-only package resource root."""
    return str(files('trendfollowing').joinpath('resources')) + os.sep


def get_universe_data_path() -> str:
    """Bundled futures data, or the explicit ``TF_RESOURCE_PATH`` override."""
    if os.environ.get('TF_RESOURCE_PATH'):
        path = Path(os.environ['TF_RESOURCE_PATH'])
    else:
        path = files('trendfollowing').joinpath('resources', 'futures')
    return str(path) + os.sep


def get_papers_data_path(paper: str = None, subfolder: str = None) -> str:
    """paper replication caches, not shipped with pip install.
    get_papers_data_path('smart_diversification', 'data') ->
    <root>/resources/papers/smart_diversification/data/"""
    path = _resolve_external('PAPERS_DATA_PATH', env_var='TF_PAPERS_PATH')
    if paper is not None:
        path = os.path.join(path, paper, '')
    if subfolder is not None:
        path = os.path.join(path, subfolder, '')
    os.makedirs(path, exist_ok=True)
    return path


def get_output_path() -> str:
    """output folder for figures, reports, and ad-hoc saves"""
    path = _resolve_external('OUTPUT_PATH', env_var='TF_OUTPUT_PATH')
    os.makedirs(path, exist_ok=True)
    return path
