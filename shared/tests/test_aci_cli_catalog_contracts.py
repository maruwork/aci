from __future__ import annotations

import json
from types import SimpleNamespace

import aci.aci_cli as cli
from aci.aci_config import AciCliConfig


def test_show_analyzer_catalog_cli_contract(capsys) -> None:
    args = SimpleNamespace(command="show-analyzer-catalog", output_format="json")

    assert cli._handle_catalog_command(args, AciCliConfig()) == 0

    payload = json.loads(capsys.readouterr().out)
    catalog = {entry["analyzer_id"]: entry for entry in payload["entries"]}

    assert payload["tool"] == "ACI"
    assert payload["catalog_kind"] == "external-analyzer"
    assert set(payload["support_levels"]) == {"profile-default", "opt-in"}
    assert catalog["ruff"]["support_level"] == "profile-default"
    assert catalog["codeql"]["support_level"] == "opt-in"
    assert catalog["codeql"]["referenced_by_profiles"] == []


def test_show_analyzer_availability_cli_contract(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli,
        "analyzer_availability",
        lambda: [
            {
                "analyzer_id": "ruff",
                "category": "lint",
                "purpose": "fast lint evidence",
                "support_level": "profile-default",
                "referenced_by_profiles": ["quick-gate"],
                "typical_ci_ids": ["CI-07"],
                "ownership_boundary": "bounded",
                "executable_path": "C:/fake/ruff.exe",
                "availability_check": "path-and-version-probe",
                "availability_state": "ready",
                "version_text": "ruff 0.4.8",
                "version_ok": True,
                "minimum_version": "0.1.0",
                "tested_version": "0.4.8",
                "version_policy": "aci-maintained-pin",
                "install_spec": "ruff==0.4.8",
                "setup_hint": "install it",
                "remediation_hint": "",
                "default_policy": "profile-default",
                "execution_support_level": "execution-ready",
            }
        ],
    )
    monkeypatch.setattr(
        cli,
        "analyzer_execution_support_levels",
        lambda: {
            "execution-ready": "ready text",
            "availability-check-only": "availability text",
        },
    )

    args = SimpleNamespace(command="show-analyzer-availability", output_format="json")

    assert cli._handle_catalog_command(args, AciCliConfig()) == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload == {
        "tool": "ACI",
        "catalog_kind": "analyzer-availability",
        "support_levels": {
            "execution-ready": "ready text",
            "availability-check-only": "availability text",
        },
        "entries": [
            {
                "analyzer_id": "ruff",
                "category": "lint",
                "purpose": "fast lint evidence",
                "support_level": "profile-default",
                "referenced_by_profiles": ["quick-gate"],
                "typical_ci_ids": ["CI-07"],
                "ownership_boundary": "bounded",
                "executable_path": "C:/fake/ruff.exe",
                "availability_check": "path-and-version-probe",
                "availability_state": "ready",
                "version_text": "ruff 0.4.8",
                "version_ok": True,
                "minimum_version": "0.1.0",
                "tested_version": "0.4.8",
                "version_policy": "aci-maintained-pin",
                "install_spec": "ruff==0.4.8",
                "setup_hint": "install it",
                "remediation_hint": "",
                "default_policy": "profile-default",
                "execution_support_level": "execution-ready",
            }
        ],
    }


def test_show_profile_execution_plan_cli_contract(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli,
        "profile_execution_plan",
        lambda: [
            {
                "profile_id": "full",
                "enabled_lanes": ["native-static", "external-analyzer", "human-judgment"],
                "default_external_analyzers": ["ruff", "pyflakes"],
                "optional_opt_in_analyzers": ["codeql"],
                "execution_support_level": "execution-ready",
                "readiness_summary": {"ruff": "ready", "pyflakes": "ready"},
                "execution_plan": "bounded defaults only",
                "ownership_boundary": "bounded",
            }
        ],
    )
    monkeypatch.setattr(
        cli,
        "analyzer_execution_support_levels",
        lambda: {
            "execution-ready": "ready text",
            "availability-check-only": "availability text",
        },
    )

    args = SimpleNamespace(command="show-profile-execution-plan", output_format="json")

    assert cli._handle_catalog_command(args, AciCliConfig()) == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload == {
        "tool": "ACI",
        "catalog_kind": "profile-execution-plan",
        "support_levels": {
            "execution-ready": "ready text",
            "availability-check-only": "availability text",
        },
        "entries": [
            {
                "profile_id": "full",
                "enabled_lanes": ["native-static", "external-analyzer", "human-judgment"],
                "default_external_analyzers": ["ruff", "pyflakes"],
                "optional_opt_in_analyzers": ["codeql"],
                "execution_support_level": "execution-ready",
                "readiness_summary": {"ruff": "ready", "pyflakes": "ready"},
                "execution_plan": "bounded defaults only",
                "ownership_boundary": "bounded",
            }
        ],
    }
