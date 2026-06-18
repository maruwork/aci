from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import aci.aci_cli as cli
import aci.aci_scale_verification as scale


def test_default_scratch_root_prefers_workspace(tmp_path: Path) -> None:
    (tmp_path / "workspace").mkdir()

    scratch_root = scale._default_scratch_root(tmp_path)

    assert scratch_root == tmp_path / "workspace" / "scale-check"


def test_build_scale_check_result_reports_budgets_and_platforms(monkeypatch, tmp_path: Path) -> None:
    scratch_root = tmp_path / "workspace" / "scale-check"
    monkeypatch.setattr(
        scale,
        "SCALE_SCENARIOS",
        (scale.ScaleScenario("tiny-python-repo", file_count=3, budget_seconds=10.0),),
    )
    monkeypatch.setattr(
        scale,
        "analyzer_availability",
        lambda: [
            {
                "analyzer_id": "ruff",
                "availability_state": "ready",
                "version_text": "ruff 0.4.8",
            }
        ],
    )

    result = scale.build_scale_check_result(tmp_path, scratch_root)

    assert result["ok"] is True
    assert result["command"] == "scale-check"
    assert result["scratch_root"] == scratch_root.as_posix()
    assert result["scan_runtime_budgets_seconds"] == {"tiny-python-repo": 10.0}
    assert result["platform_support_matrix"]["continuous_ci"] == [
        "ubuntu-latest",
        "windows-latest",
        "macos-latest",
    ]
    assert result["scenarios"][0]["file_count"] == 3
    assert result["scenarios"][0]["within_budget"] is True
    assert result["analyzer_availability_snapshot"][0]["budget_seconds"] == 10.0


def test_scale_check_cli_surface_emits_compact_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli,
        "build_scale_check_result",
        lambda repo_root, scratch_root: {
            "tool": "ACI",
            "command": "scale-check",
            "ok": True,
            "scratch_root": None if scratch_root is None else str(scratch_root),
            "scenarios": [],
            "scan_runtime_budgets_seconds": {},
            "analyzer_runtime_budgets_seconds": {},
            "analyzer_availability_snapshot": [],
            "platform_support_matrix": {
                "continuous_ci": ["ubuntu-latest", "windows-latest", "macos-latest"],
                "python_versions": ["3.11", "3.12"],
            },
        },
    )

    result = cli._handle_verification_command(
        SimpleNamespace(command="scale-check", scratch_root=Path("workspace/scale-check")),
        cli.AciCliConfig(),
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "scale-check"
    assert payload["ok"] is True
    assert payload["platform_support_matrix"]["continuous_ci"][1] == "windows-latest"


def test_ci_workflow_continuously_verifies_windows_and_macos() -> None:
    workflow = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "windows-latest" in workflow
    assert "macos-latest" in workflow
    assert "scale-check" in workflow
