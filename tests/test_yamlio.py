from __future__ import annotations

import os

import pytest

from clashverge_openclash import yamlio
from clashverge_openclash.yamlio import ConfigError, atomic_write_yaml, load_yaml, paths_overlap


def test_safe_loader_rejects_python_object_tag(tmp_path):
    marker = tmp_path / "marker"
    source = tmp_path / "unsafe.yaml"
    source.write_text(
        "payload: !!python/object/apply:pathlib.Path ['" + str(marker) + "']\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="Invalid YAML"):
        load_yaml(source)
    assert not marker.exists()


def test_duplicate_mapping_keys_are_rejected(tmp_path):
    source = tmp_path / "duplicate.yaml"
    source.write_text("proxies: []\nproxies: []\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="Duplicate YAML mapping key"):
        load_yaml(source)


def test_alias_limit_is_enforced(tmp_path):
    source = tmp_path / "aliases.yaml"
    aliases = ", ".join("*item" for _ in range(yamlio.MAX_ALIASES + 1))
    source.write_text(f"base: &item value\nitems: [{aliases}]\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="YAML aliases"):
        load_yaml(source)


def test_input_size_limit_is_enforced(tmp_path, monkeypatch):
    source = tmp_path / "large.yaml"
    source.write_text("proxies: []\n", encoding="utf-8")
    monkeypatch.setattr(yamlio, "MAX_INPUT_BYTES", 4)
    with pytest.raises(ConfigError, match="exceeds"):
        load_yaml(source)


def test_atomic_write_is_private_and_requires_force(tmp_path):
    output = tmp_path / "target.yaml"
    atomic_write_yaml(output, {"mode": "rule"}, force=False)

    assert output.stat().st_mode & 0o777 == 0o600
    with pytest.raises(ConfigError, match="--force"):
        atomic_write_yaml(output, {"mode": "global"}, force=False)
    atomic_write_yaml(output, {"mode": "global"}, force=True)
    assert "global" in output.read_text(encoding="utf-8")
    assert output.stat().st_mode & 0o777 == 0o600


def test_output_symlink_is_refused(tmp_path):
    protected = tmp_path / "protected.yaml"
    protected.write_text("keep", encoding="utf-8")
    output = tmp_path / "target.yaml"
    output.symlink_to(protected)

    with pytest.raises(ConfigError, match="symlink"):
        atomic_write_yaml(output, {"mode": "rule"}, force=True)
    assert protected.read_text(encoding="utf-8") == "keep"


def test_paths_overlap_detects_same_path_and_symlink(tmp_path):
    source = tmp_path / "source.yaml"
    source.write_text("proxies: []", encoding="utf-8")
    link = tmp_path / "link.yaml"
    link.symlink_to(source)

    assert paths_overlap(source, source)
    assert paths_overlap(source, link)


def test_atomic_replace_leaves_no_temporary_file(tmp_path):
    output = tmp_path / "target.yaml"
    atomic_write_yaml(output, {"mode": "rule"}, force=False)
    assert list(tmp_path.glob(".target.yaml.*.tmp")) == []
    assert os.stat(output).st_size > 0


def test_no_force_write_detects_a_racing_output(tmp_path, monkeypatch):
    output = tmp_path / "target.yaml"
    real_link = os.link

    def racing_link(source, destination):
        output.write_text("racer", encoding="utf-8")
        return real_link(source, destination)

    monkeypatch.setattr(os, "link", racing_link)
    with pytest.raises(ConfigError, match="appeared during write"):
        atomic_write_yaml(output, {"mode": "rule"}, force=False)
    assert output.read_text(encoding="utf-8") == "racer"
