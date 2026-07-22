"""
local_path uses settings.yaml to return absolute paths for resource and output folders,
the same approach as qis.local_path.

relative entries in settings.yaml resolve against the repo root, taken as the parent of
this package folder, so a source checkout works with no configuration. a pip-installed
package needs settings.yaml edited to absolute local paths (see the resource roadmap).

environment overrides take precedence over settings.yaml:
    TF_RESOURCE_PATH   overrides UNIVERSE_DATA_PATH (the packaged-futures location)
    TF_PAPERS_PATH     overrides PAPERS_DATA_PATH
    TF_OUTPUT_PATH     overrides OUTPUT_PATH
"""
# packages
import os
import yaml
from functools import lru_cache
from pathlib import Path
from typing import Dict

_SETTINGS_PATH = Path(__file__).parent.joinpath('settings.yaml')
_REPO_ROOT = Path(__file__).parent.parent


@lru_cache(maxsize=1)
def get_paths() -> Dict[str, str]:
    """read path specs in settings.yaml; cached after first call.
    call get_paths.cache_clear() to force a re-read."""
    with open(_SETTINGS_PATH) as settings:
        settings_data = yaml.safe_load(settings)
    return settings_data


def _resolve(key: str, env_var: str = None) -> str:
    """absolute path for a settings key, with optional environment override.

    Raises:
        KeyError: if the key is missing from settings.yaml
    """
    if env_var is not None and os.environ.get(env_var):
        path = Path(os.environ[env_var])
    else:
        path = Path(get_paths()[key])
        if not path.is_absolute():
            path = _REPO_ROOT.joinpath(path)
    return str(path) + os.sep


def get_resource_path() -> str:
    """root resources folder from settings.yaml"""
    return _resolve('RESOURCE_PATH')


def get_universe_data_path() -> str:
    """futures prices and costs, the minimal dataset for running the package"""
    return _resolve('UNIVERSE_DATA_PATH', env_var='TF_RESOURCE_PATH')


def get_papers_data_path(paper: str = None, subfolder: str = None) -> str:
    """paper replication caches, not shipped with pip install.
    get_papers_data_path('smart_diversification', 'data') ->
    <root>/resources/papers/smart_diversification/data/"""
    path = _resolve('PAPERS_DATA_PATH', env_var='TF_PAPERS_PATH')
    if paper is not None:
        path = os.path.join(path, paper, '')
    if subfolder is not None:
        path = os.path.join(path, subfolder, '')
    os.makedirs(path, exist_ok=True)
    return path


def get_output_path() -> str:
    """output folder for figures, reports, and ad-hoc saves"""
    path = _resolve('OUTPUT_PATH', env_var='TF_OUTPUT_PATH')
    os.makedirs(path, exist_ok=True)
    return path
