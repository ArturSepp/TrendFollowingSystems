"""Tests for the installed futures-resource contract."""

import os
from importlib.resources import files
from pathlib import Path

import pandas as pd
import pytest

import trendfollowing.universe as universe
from trendfollowing.local_path import get_universe_data_path


REQUIRED_FUTURES_FILES = {
    "tf_system_data_benchmark_prices.csv",
    "tf_system_data_descriptive_df.csv",
    "tf_system_data_ohlc_es1.csv",
    "tf_system_data_ohlc_gc1.csv",
    "tf_system_data_ohlc_ty1.csv",
    "tf_system_data_prices.csv",
    "tf_system_data_usd_returns.csv",
    "tf_system_data_volume_costs.csv",
}


def test_default_futures_path_is_bundled(monkeypatch):
    monkeypatch.delenv("TF_RESOURCE_PATH", raising=False)
    bundled = files("trendfollowing").joinpath("resources", "futures")

    assert bundled.is_dir()
    assert REQUIRED_FUTURES_FILES <= {entry.name for entry in bundled.iterdir()}
    assert Path(get_universe_data_path()).resolve() == Path(str(bundled)).resolve()


def test_resource_override_is_resolved_when_load_data_is_called(monkeypatch, tmp_path):
    index = pd.DatetimeIndex(["2026-01-02"])
    prices = pd.DataFrame({"TEST": [100.0]}, index=index)
    description = pd.DataFrame(
        {"group_data": ["Equities"], "names": ["Test future"]},
        index=["TEST"],
    )
    calls = []

    def fake_load_df_dict_from_csv(*, dataset_keys, file_name, local_path):
        calls.append(local_path)
        return {
            "prices": prices,
            "volume_costs": prices.copy(),
            "benchmark_prices": prices.copy(),
            "descriptive_df": description,
        }

    monkeypatch.setenv("TF_RESOURCE_PATH", str(tmp_path))
    monkeypatch.setattr(universe.qis, "load_df_dict_from_csv", fake_load_df_dict_from_csv)

    loaded = universe.load_data()

    assert calls == [str(tmp_path) + os.sep]
    assert loaded[0].equals(prices)
    assert loaded[3].equals(description)


def test_generate_data_requires_explicit_external_destination(monkeypatch):
    monkeypatch.delenv("TF_RESOURCE_PATH", raising=False)

    with pytest.raises(RuntimeError, match="TF_RESOURCE_PATH"):
        universe.generate_data()
