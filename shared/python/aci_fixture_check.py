#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded fixture checks for the common ACI shelf."""
from __future__ import annotations

import json
from pathlib import Path

try:
    from .aci_package_assets import read_text_asset
    from .aci_automation import validate_sample_reports
    from .aci_public_smoke import build_public_smoke_result
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_package_assets import read_text_asset
    from aci_automation import validate_sample_reports
    from aci_public_smoke import build_public_smoke_result


def run_fixture_check(repo_root: Path) -> dict[str, object]:
    fallback_root = Path(__file__).resolve().parent / "package_assets"
    expected = json.loads(
        read_text_asset("fixtures/expected_smoke_contract.json", fallback_root)
    )
    actual = build_public_smoke_result(repo_root)
    sample_checks = validate_sample_reports()

    checks = []

    checks.append(
        {
            "check": "tool_id",
            "ok": actual.get("tool") == expected.get("tool"),
            "expected": expected.get("tool"),
            "actual": actual.get("tool"),
        }
    )

    for key, expected_value in expected["mode_checks"].items():
        actual_value = actual["mode_checks"].get(key)
        checks.append(
            {
                "check": f"mode_checks.{key}",
                "ok": actual_value == expected_value,
                "expected": expected_value,
                "actual": actual_value,
            }
        )

    for key, expected_value in expected["finding_sample"].items():
        actual_value = actual["finding_sample"].get(key)
        checks.append(
            {
                "check": f"finding_sample.{key}",
                "ok": actual_value == expected_value,
                "expected": expected_value,
                "actual": actual_value,
            }
        )

    checks.append(
        {
            "check": "sample_report_contracts",
            "ok": sample_checks["ok"],
            "expected": True,
            "actual": sample_checks["ok"],
        }
    )

    ok = all(item["ok"] for item in checks)
    return {
        "tool": "ACI",
        "command": "fixture-check",
        "ok": ok,
        "checks": checks,
        "sample_report_checks": sample_checks["checks"],
    }
