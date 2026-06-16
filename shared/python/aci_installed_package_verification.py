#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded installed-package verification helpers for ACI."""
from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import re
import sys
import tomllib
from pathlib import Path


def _detect_package_root(repo_root: Path) -> Path:
    standalone_package_root = repo_root / "shared" / "python"
    if (standalone_package_root / "__init__.py").exists():
        return standalone_package_root
    package_module = importlib.import_module("aci")
    if package_module.__file__ is None:
        raise RuntimeError("ACI package __file__ is None; cannot detect package root")
    return Path(package_module.__file__).resolve().parent


def _load_package_root(package_root: Path) -> None:
    init_file = package_root / "__init__.py"
    if "aci" in sys.modules:
        return
    spec = importlib.util.spec_from_file_location(
        "aci",
        init_file,
        submodule_search_locations=[str(package_root)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("ACI package root spec could not be created")
    module = importlib.util.module_from_spec(spec)
    sys.modules["aci"] = module
    spec.loader.exec_module(module)


def _editable_install_checks(repo_root: Path) -> list[dict[str, object]]:
    package_root = _detect_package_root(repo_root)
    _load_package_root(package_root)

    checks: list[dict[str, object]] = []

    cli_module = importlib.import_module("aci.aci_cli")
    checks.append(
        {
            "check": "editable_import.aci_cli",
            "ok": hasattr(cli_module, "main"),
            "expected": True,
            "actual": hasattr(cli_module, "main"),
        }
    )

    domain_loader = importlib.import_module("aci.aci_domain_loader")
    core_rules = domain_loader.load_domain_rules(None)
    checks.append(
        {
            "check": "editable_import.core_domain_loader",
            "ok": core_rules.domain_id == "core-only",
            "expected": "core-only",
            "actual": core_rules.domain_id,
        }
    )

    package_assets = importlib.import_module("aci.aci_package_assets")
    sample_text = package_assets.read_text_asset(
        "report/examples/aci-core-sample-report.json",
        package_root.parent,
    )
    checks.append(
        {
            "check": "editable_import.package_asset",
            "ok": "aci-core-sample-001" in sample_text,
            "expected": True,
            "actual": "aci-core-sample-001" in sample_text,
        }
    )

    return checks


def _built_artifact_contract_checks(repo_root: Path) -> list[dict[str, object]]:
    pyproject_candidates = (
        repo_root / "pyproject.toml",
    )
    pyproject_path = next((item for item in pyproject_candidates if item.exists()), None)
    if pyproject_path is not None:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        package_data = data["tool"]["setuptools"]["package-data"]["aci"]
        scripts = data["project"]["scripts"]
        return [
            {
                "check": "built_contract.cli_entrypoint",
                "ok": scripts.get("aci") == "aci.aci_cli:main",
                "expected": "aci.aci_cli:main",
                "actual": scripts.get("aci"),
            },
            {
                "check": "built_contract.fixture_asset_rule",
                "ok": "package_assets/fixtures/*.json" in package_data,
                "expected": True,
                "actual": "package_assets/fixtures/*.json" in package_data,
            },
            {
                "check": "built_contract.report_asset_rule",
                "ok": "package_assets/report/examples/*.json" in package_data
                and "package_assets/report/examples/*.md" in package_data,
                "expected": True,
                "actual": "package_assets/report/examples/*.json" in package_data
                and "package_assets/report/examples/*.md" in package_data,
            },
        ]

    dist = importlib.metadata.distribution("aci")
    entry_points = [item for item in dist.entry_points if item.group == "console_scripts" and item.name == "aci"]
    package_files = [str(item) for item in (dist.files or [])]
    has_fixture_asset = any(item.endswith("aci/package_assets/fixtures/expected_smoke_contract.json") for item in package_files)
    has_core_report_json = any(item.endswith("aci/package_assets/report/examples/aci-core-sample-report.json") for item in package_files)
    has_core_report_md = any(item.endswith("aci/package_assets/report/examples/aci-core-sample-report.md") for item in package_files)
    actual_entry = entry_points[0].value if entry_points else None
    return [
        {
            "check": "built_contract.cli_entrypoint",
            "ok": actual_entry == "aci.aci_cli:main",
            "expected": "aci.aci_cli:main",
            "actual": actual_entry,
        },
        {
            "check": "built_contract.fixture_asset_rule",
            "ok": has_fixture_asset,
            "expected": True,
            "actual": has_fixture_asset,
        },
        {
            "check": "built_contract.report_asset_rule",
            "ok": has_core_report_json and has_core_report_md,
            "expected": True,
            "actual": has_core_report_json and has_core_report_md,
        },
    ]


def _release_gate_checks(repo_root: Path) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []

    # Version string consistency: ACI_TOOL_VERSION in aci_scan.py vs pyproject.toml
    pyproject_path = repo_root / "pyproject.toml"
    scan_py_path = repo_root / "shared" / "python" / "aci_scan.py"
    pyproject_version: str | None = None
    scan_version: str | None = None
    if pyproject_path.exists():
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        pyproject_version = str(data.get("project", {}).get("version") or "")
    if scan_py_path.exists():
        m = re.search(r'ACI_TOOL_VERSION\s*=\s*"([^"]+)"', scan_py_path.read_text(encoding="utf-8"))
        if m:
            scan_version = m.group(1)
    checks.append({
        "check": "release_gate.version_consistency",
        "ok": bool(pyproject_version and pyproject_version == scan_version),
        "expected": pyproject_version,
        "actual": scan_version,
    })

    # Sample report schema validity
    try:
        from .aci_automation import validate_sample_reports
    except ImportError:  # pragma: no cover
        from aci_automation import validate_sample_reports  # type: ignore[no-redef]
    report_result = validate_sample_reports()
    checks.append({
        "check": "release_gate.sample_reports_valid",
        "ok": bool(report_result.get("ok")),
        "expected": True,
        "actual": bool(report_result.get("ok")),
    })

    return checks


def run_installed_package_check(repo_root: Path) -> dict[str, object]:
    editable_checks = _editable_install_checks(repo_root)
    built_contract_checks = _built_artifact_contract_checks(repo_root)
    release_gate_checks = _release_gate_checks(repo_root)
    checks = editable_checks + built_contract_checks + release_gate_checks
    editable_ok = all(item["ok"] for item in editable_checks)
    built_contract_ok = all(item["ok"] for item in built_contract_checks)
    release_gate_ok = all(item["ok"] for item in release_gate_checks)
    ok = all(item["ok"] for item in checks)
    return {
        "tool": "ACI",
        "command": "installed-package-check",
        "ok": ok,
        "proof_lanes": {
            "editable_install": {
                "proved": editable_ok,
                "checks": editable_checks,
            },
            "built_artifact_contract": {
                "proved": built_contract_ok,
                "checks": built_contract_checks,
            },
            "release_gate": {
                "proved": release_gate_ok,
                "checks": release_gate_checks,
            },
        },
        "checks": checks,
    }
