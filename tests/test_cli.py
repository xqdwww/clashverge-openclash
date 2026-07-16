from __future__ import annotations

from pathlib import Path

import yaml

from clashverge_openclash.cli import main


FIXTURES = Path(__file__).parent / "fixtures"


def test_convert_smoke_and_target_validation(tmp_path):
    output = tmp_path / "target.yaml"
    assert main(["convert", "-i", str(FIXTURES / "synthetic-source.yaml"), "-o", str(output)]) == 0
    assert main(["validate", str(output), "--type", "target"]) == 0
    document = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert document["rules"][-1] == "MATCH,OPENCLASH"
    assert document["proxies"][0]["udp"] is True
    assert output.stat().st_mode & 0o777 == 0o600


def test_dry_run_writes_nothing_even_if_output_exists(tmp_path):
    output = tmp_path / "target.yaml"
    output.write_text("keep", encoding="utf-8")
    assert (
        main(
            [
                "convert",
                "-i",
                str(FIXTURES / "synthetic-source.yaml"),
                "-o",
                str(output),
                "--dry-run",
            ]
        )
        == 0
    )
    assert output.read_text(encoding="utf-8") == "keep"


def test_overwrite_requires_force(tmp_path):
    output = tmp_path / "target.yaml"
    output.write_text("keep", encoding="utf-8")
    base = ["convert", "-i", str(FIXTURES / "synthetic-source.yaml"), "-o", str(output)]
    assert main(base) == 1
    assert output.read_text(encoding="utf-8") == "keep"
    assert main([*base, "--force"]) == 0


def test_invalid_yaml_returns_one(tmp_path):
    output = tmp_path / "target.yaml"
    assert main(["convert", "-i", str(FIXTURES / "invalid.yaml"), "-o", str(output)]) == 1
    assert not output.exists()


def test_same_input_and_output_returns_one():
    source = FIXTURES / "synthetic-source.yaml"
    assert main(["convert", "-i", str(source), "-o", str(source), "--force"]) == 1


def test_stats_do_not_echo_proxy_credentials(tmp_path, capsys):
    output = tmp_path / "target.yaml"
    assert main(["convert", "-i", str(FIXTURES / "synthetic-source.yaml"), "-o", str(output)]) == 0
    captured = capsys.readouterr()
    assert "synthetic-only" not in captured.out
    assert "192.0.2.10" not in captured.out


def test_validate_invalid_target_returns_one():
    assert main(["validate", str(FIXTURES / "synthetic-source.yaml"), "--type", "target"]) == 1
