#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SARIF emission helpers for ACI."""
from __future__ import annotations

from typing import cast

try:
    from .aci_findings import SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW
    from .aci_report_helpers import gate_scope_classes as _gate_scope_classes, scope_class as _scope_class
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW
    from aci_report_helpers import gate_scope_classes as _gate_scope_classes, scope_class as _scope_class  # type: ignore[no-redef]


SEVERITY_TO_LEVEL = {
    SEVERITY_LOW: "note",
    SEVERITY_MEDIUM: "warning",
    SEVERITY_HIGH: "error",
    SEVERITY_CRITICAL: "error",
}


def build_sarif_report(report: dict[str, object]) -> dict[str, object]:
    raw_findings = report.get("findings") or []
    findings: list[dict[str, object]] = raw_findings if isinstance(raw_findings, list) else []
    gate_scope_classes = _gate_scope_classes(report)
    rules: dict[str, dict[str, object]] = {}
    results: list[dict[str, object]] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        scope_class = _scope_class(finding)
        advisory_only = scope_class not in gate_scope_classes
        rule_id = str(finding.get("signal") or finding.get("ci_id") or "ACI-FINDING")
        rules.setdefault(
            rule_id,
            {
                "id": rule_id,
                "name": str(finding.get("ci_id") or rule_id),
                "shortDescription": {"text": str(finding.get("reason") or rule_id)},
                "properties": {
                    "precision": str(finding.get("confidence") or "medium"),
                    "problem.severity": str(finding.get("severity") or "medium"),
                },
            },
        )
        location: dict[str, object] = {
            "physicalLocation": {
                "artifactLocation": {"uri": str(finding.get("target_file") or "")},
            }
        }
        if finding.get("line") is not None:
            phys_loc = location["physicalLocation"]
            if isinstance(phys_loc, dict):
                phys_loc["region"] = {"startLine": int(cast(int, finding["line"]))}
        message_text = str(finding.get("reason") or "ACI finding")
        if advisory_only:
            message_text = f"Advisory-only ({scope_class}): {message_text}"
        results.append(
            {
                "ruleId": rule_id,
                "level": "note" if advisory_only else SEVERITY_TO_LEVEL.get(str(finding.get("severity")), "warning"),
                "message": {"text": message_text},
                "locations": [location],
                "properties": {
                    "aci.scope_class": scope_class,
                    "aci.scope_policy": "advisory-only" if advisory_only else "gated",
                },
                "fingerprints": {
                    "primaryLocationLineHash": str(finding.get("fingerprint") or "")
                },
            }
        )
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "ACI",
                        "informationUri": "https://github.com/maruwork/aci",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }


def validate_sarif_report(payload: object) -> dict[str, object]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return {"ok": False, "errors": ["SARIF payload must be an object"]}
    if payload.get("version") != "2.1.0":
        errors.append("version must be 2.1.0")
    runs = payload.get("runs")
    if not isinstance(runs, list) or not runs:
        errors.append("runs must be a non-empty array")
        runs = []
    for run_index, run in enumerate(runs):
        if not isinstance(run, dict):
            errors.append(f"runs[{run_index}] must be an object")
            continue
        driver = (((run.get("tool") or {}) if isinstance(run.get("tool"), dict) else {}).get("driver"))
        if not isinstance(driver, dict):
            errors.append(f"runs[{run_index}].tool.driver must be an object")
            continue
        if not driver.get("name"):
            errors.append(f"runs[{run_index}].tool.driver.name is required")
        rules = driver.get("rules", [])
        if not isinstance(rules, list):
            errors.append(f"runs[{run_index}].tool.driver.rules must be an array")
        results = run.get("results", [])
        if not isinstance(results, list):
            errors.append(f"runs[{run_index}].results must be an array")
            continue
        for result_index, result in enumerate(results):
            if not isinstance(result, dict):
                errors.append(f"runs[{run_index}].results[{result_index}] must be an object")
                continue
            if not result.get("ruleId"):
                errors.append(f"runs[{run_index}].results[{result_index}].ruleId is required")
            locations = result.get("locations", [])
            if not isinstance(locations, list) or not locations:
                errors.append(f"runs[{run_index}].results[{result_index}].locations must be a non-empty array")
                continue
            first_location = locations[0]
            if not isinstance(first_location, dict):
                errors.append(f"runs[{run_index}].results[{result_index}].locations[0] must be an object")
                continue
            physical = first_location.get("physicalLocation", {})
            if not isinstance(physical, dict):
                errors.append(
                    f"runs[{run_index}].results[{result_index}].locations[0].physicalLocation must be an object"
                )
                continue
            artifact = physical.get("artifactLocation", {})
            if not isinstance(artifact, dict) or not artifact.get("uri"):
                errors.append(
                    f"runs[{run_index}].results[{result_index}].locations[0].physicalLocation.artifactLocation.uri is required"
                )
    return {"ok": not errors, "errors": errors}
