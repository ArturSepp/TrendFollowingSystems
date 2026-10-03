"""Frozen-input preservation and separation of publication assets from new runs."""

import hashlib
import json
from pathlib import Path
import re

import pytest

from papers.tf_systems.replication import paths


def test_reference_hashes():
    """All nine costly reference caches retain the exact original bytes."""
    manifest = json.loads((paths.REFERENCE_DIR / "sha256.json").read_text())
    assert len(manifest) == 9
    for name, expected in manifest.items():
        assert hashlib.sha256((paths.REFERENCE_DIR / name).read_bytes()).hexdigest() == expected


def test_manuscript_dependencies_are_approved():
    """All twelve referenced figures and the class are explicitly approved."""
    text = (paths.PAPER_DIR / "paper/TrendFollowing_PaperA_SIFIN_v1.tex").read_text(encoding="utf-8")
    names = re.findall(r"\\includegraphics(?:\[[^]]*\])?\s*\{([^}]+)\}", text)
    assert len(names) == 12
    allowed = set((paths.PAPER_DIR / ".gitignore").read_text().splitlines())
    for name in names + ["siamonline250211.cls"]:
        assert (paths.PAPER_DIR / "paper" / name).is_file()
        assert "!/paper/" + name in allowed


@pytest.mark.parametrize("target", ["relative/output", "checkout", "onedrive"])
def test_outputs_cannot_overwrite_source(monkeypatch, tmp_path, target):
    """Invalid overrides must fail before creating output directories."""
    value = target
    if target == "checkout":
        value = str(paths.REFERENCE_DIR)
    elif target == "onedrive":
        value = str(tmp_path / "OneDrive" / "output")
    monkeypatch.setenv("TF_PAPER_OUTPUT_PATH", value)
    with pytest.raises(ValueError):
        paths.get_results_path()


def test_external_output_and_reference_input_are_separate(monkeypatch, tmp_path):
    """Runtime overrides move new results only, never immutable cache reads."""
    monkeypatch.setenv("TF_PAPER_OUTPUT_PATH", str(tmp_path))
    monkeypatch.delenv("TF_FIGURE_PATH", raising=False)
    assert Path(paths.get_results_path()) == tmp_path / "results"
    assert Path(paths.get_figure_path()) == tmp_path / "figures"
    assert (paths.REFERENCE_DIR / "grid_cache.pkl").is_file()


def test_cached_inputs_load_from_unrelated_directory(monkeypatch, tmp_path):
    """The relocated readers must work without the old resources or cwd paths."""
    from papers.tf_systems.replication import mc_net_sharpe_paper_figs as process
    from papers.tf_systems.replication.cross_system_attribution_figs import compute_cross_system_tables
    monkeypatch.chdir(tmp_path)
    for name in process.FIGS:
        frames = process._frames_for(name, str(paths.REFERENCE_DIR))
        assert frames and all(not frame.empty for frame in frames.values())
    tables = compute_cross_system_tables(None, cache_file=str(paths.REFERENCE_DIR / "grid_cache.pkl"))
    assert set(tables) == {"predicted", "predicted_ac", "realized_eu", "realized_am", "realized_ts"}
    assert all(not frame.empty for frame in tables.values())


def test_generation_routes_to_external_results(monkeypatch, tmp_path):
    """A generation dispatch cannot overwrite the published cache directory."""
    from papers.tf_systems.replication import mc_net_sharpe_paper_figs as process
    monkeypatch.setenv("TF_PAPER_OUTPUT_PATH", str(tmp_path))
    monkeypatch.delenv("TF_FIGURE_PATH", raising=False)
    calls = []
    monkeypatch.setattr(process, "compute_parts", lambda name, parts_path: calls.append((name, Path(parts_path))))
    process.run_local(local=process.Locals.COMPUTE_AR)
    assert calls == [("expected_return_ar", tmp_path / "results")]
    with pytest.raises(ValueError):
        process.run_local(local=process.Locals.COMPUTE_AR, parts_path=str(paths.REFERENCE_DIR))


def test_explicit_missing_run_does_not_fall_back_to_reference(tmp_path):
    """Missing newly generated data is reported, rather than mixed with old results."""
    from papers.tf_systems.replication import mc_net_sharpe_paper_figs as process
    with pytest.raises(FileNotFoundError):
        process._frames_for("expected_return_ar", str(tmp_path))
