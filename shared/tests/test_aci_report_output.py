"""Tests for fixed-destination report output (--output / report_output config)."""
from __future__ import annotations

import json
from pathlib import Path

from aci.aci_cli import _write_report_file
from aci.aci_config import AciCliConfig, config_schema, load_cli_config


def test_report_output_defaults_to_stdout() -> None:
    assert AciCliConfig().report_output == ""
    assert "report_output" in config_schema()["fields"]  # type: ignore[index]


def test_config_loads_report_output(tmp_path: Path) -> None:
    cfg_file = tmp_path / "aci.toml"
    cfg_file.write_text('[aci]\nreport_output = ".aci/report.json"\n', encoding="utf-8")
    cfg = load_cli_config(cfg_file)
    assert cfg.report_output == ".aci/report.json"


def test_config_rejects_non_string_report_output(tmp_path: Path) -> None:
    cfg_file = tmp_path / "aci.toml"
    cfg_file.write_text("[aci]\nreport_output = 123\n", encoding="utf-8")
    try:
        load_cli_config(cfg_file)
    except ValueError:
        return
    raise AssertionError("expected ValueError for non-string report_output")


def test_write_report_file_creates_parent_and_valid_json(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "dir" / "report.json"
    data = {"summary": {"total_findings": 3}, "gate": {"decision": "fail"}, "findings": []}
    _write_report_file(data, out, "json")
    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8"))["summary"]["total_findings"] == 3
