#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded automation helpers for the common ACI shelf."""
from __future__ import annotations

import json
from pathlib import Path

try:
    from .aci_findings import (
        SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW,
        VERIFICATION_DETECTED, VERIFICATION_EXECUTED,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (
        SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW,
        VERIFICATION_DETECTED, VERIFICATION_EXECUTED,
    )

ALLOWED_SEVERITIES = {SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL}
ALLOWED_BASELINE_STATES = {"new", "existing-baseline"}
ALLOWED_WAIVER_STATES = {"none", "active-waiver"}
ALLOWED_VERIFICATION_STATES = {VERIFICATION_DETECTED, VERIFICATION_EXECUTED}


REQUIRED_SAMPLE_TOP_LEVEL_FIELDS = (
    "report_format_version",
    "report_id",
    "tool_id",
    "tool_version",
    "mode",
    "domain",
    "scan_scope",
    "generated_at",
    "verification_status",
    "summary",
    "findings",
    "blockers",
    "residuals",
    "resolved_baseline_entries",
    "next_actions",
)

REQUIRED_SAMPLE_FINDING_FIELDS = (
    "finding_id",
    "ci_id",
    "signal",
    "severity",
    "confidence",
    "actor_label",
    "triage_state",
    "priority",
    "fixability",
    "baseline_status",
    "waiver_status",
    "target_file",
    "line",
    "excerpt",
    "reason",
    "evidence_ref",
    "recommended_action",
    "owner_lane",
    "verification_status",
)

SUMMARY_COUNT_FIELDS = (
    "waived_count",
    "suppressed_count",
    "new_count",
    "existing_baseline_count",
    "blocker_count",
    "residual_count",
    "resolved_baseline_count",
)


def _sample_paths() -> tuple[Path, ...]:
    root = Path(__file__).resolve().parent.parent.parent
    return (root / "shared" / "report" / "examples" / "aci-core-sample-report.json",)


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and value >= 0


def _validate_summary(summary: object, findings: list[dict[str, object]], residuals: list[object]) -> list[str]:
    if not isinstance(summary, dict):
        return ["summary must be an object"]

    errors: list[str] = []
    if summary.get("total_findings") != len(findings):
        errors.append("summary.total_findings must equal findings length")

    for field in SUMMARY_COUNT_FIELDS:
        if not _is_non_negative_int(summary.get(field)):
            errors.append(f"summary.{field} must be a non-negative integer")

    severity_counts: dict[str, int] = {}
    baseline_counts: dict[str, int] = {}
    for finding in findings:
        severity = finding.get("severity")
        baseline = finding.get("baseline_status")
        if isinstance(severity, str):
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        if isinstance(baseline, str):
            baseline_counts[baseline] = baseline_counts.get(baseline, 0) + 1

    if summary.get("by_severity") != severity_counts:
        errors.append("summary.by_severity must match finding rows")
    if summary.get("by_baseline_status") != baseline_counts:
        errors.append("summary.by_baseline_status must match finding rows")
    if summary.get("new_count") != baseline_counts.get("new", 0):
        errors.append("summary.new_count must match new findings")
    if summary.get("existing_baseline_count") != baseline_counts.get("existing-baseline", 0):
        errors.append("summary.existing_baseline_count must match baseline findings")
    if summary.get("waived_count") != sum(
        1 for finding in findings if finding.get("waiver_status") != "none"
    ):
        errors.append("summary.waived_count must match waived findings")
    if summary.get("residual_count") != len(residuals):
        errors.append("summary.residual_count must match residual rows")
    return errors


def _validate_gate(gate: object, blockers: list[object]) -> list[str]:
    if not isinstance(gate, dict):
        return ["gate must be an object"]
    errors: list[str] = []
    if gate.get("decision") not in {"pass", "fail"}:
        errors.append("gate.decision must be pass or fail")
    reasons = gate.get("reasons", [])
    if not isinstance(reasons, list):
        errors.append("gate.reasons must be an array")
        reasons = []
    reason_details = gate.get("reason_details", [])
    if not isinstance(reason_details, list):
        errors.append("gate.reason_details must be an array")
        reason_details = []
    if gate.get("blocking_count") != len(blockers):
        errors.append("gate.blocking_count must match blocker rows")
    seen_reasons = {item.get("reason") for item in reason_details if isinstance(item, dict)}
    for reason in reasons:
        if reason not in seen_reasons:
            errors.append(f"gate.reason_details must include {reason}")
    return errors


def _validate_finding(sample_name: str, index: int, finding: object) -> list[str]:
    prefix = f"{sample_name}.findings[{index}]"
    if not isinstance(finding, dict):
        return [f"{prefix} must be an object"]

    errors: list[str] = []
    for field in REQUIRED_SAMPLE_FINDING_FIELDS:
        if field not in finding:
            errors.append(f"{prefix}.{field} is required")

    if finding.get("severity") not in ALLOWED_SEVERITIES:
        errors.append(f"{prefix}.severity must be one of {sorted(ALLOWED_SEVERITIES)}")
    if finding.get("baseline_status") not in ALLOWED_BASELINE_STATES:
        errors.append(f"{prefix}.baseline_status must be one of {sorted(ALLOWED_BASELINE_STATES)}")
    if finding.get("waiver_status") not in ALLOWED_WAIVER_STATES:
        errors.append(f"{prefix}.waiver_status must be one of {sorted(ALLOWED_WAIVER_STATES)}")
    if finding.get("verification_status") not in ALLOWED_VERIFICATION_STATES:
        errors.append(
            f"{prefix}.verification_status must be one of {sorted(ALLOWED_VERIFICATION_STATES)}"
        )
    line = finding.get("line")
    if line is not None and not _is_non_negative_int(line):
        errors.append(f"{prefix}.line must be null or a non-negative integer")
    return errors


def validate_report_payload(
    sample_name: str,
    data: object,
    *,
    require_findings: bool = False,
) -> dict[str, object]:
    if not isinstance(data, dict):
        return {
            "sample": sample_name,
            "ok": False,
            "missing_top_level_fields": [],
            "field_errors": [],
            "type_errors": [f"{sample_name} must be an object"],
        }
    top_missing = [field for field in REQUIRED_SAMPLE_TOP_LEVEL_FIELDS if field not in data]
    findings = data.get("findings", [])
    residuals = data.get("residuals", [])
    blockers = data.get("blockers", [])
    field_errors: list[str] = []
    type_errors: list[str] = []
    if not isinstance(findings, list):
        type_errors.append(f"{sample_name}.findings must be an array")
        findings = []
    if not isinstance(residuals, list):
        type_errors.append(f"{sample_name}.residuals must be an array")
        residuals = []
    if not isinstance(blockers, list):
        type_errors.append(f"{sample_name}.blockers must be an array")
        blockers = []
    if require_findings and not findings:
        field_errors.append(f"{sample_name}.findings must contain at least one finding")
    for index, finding in enumerate(findings):
        field_errors.extend(_validate_finding(sample_name, index, finding))
    type_errors.extend(_validate_summary(data.get("summary"), findings, residuals))
    type_errors.extend(_validate_gate(data.get("gate"), blockers))
    if data.get("report_format_version") != "1.0.0":
        type_errors.append(f"{sample_name}.report_format_version must be 1.0.0")
    sample_ok = not top_missing and not field_errors and not type_errors
    return {
        "sample": sample_name,
        "ok": sample_ok,
        "missing_top_level_fields": top_missing,
        "field_errors": field_errors,
        "type_errors": type_errors,
    }


def validate_sample_reports() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    ok = True
    for sample_path in _sample_paths():
        data = json.loads(sample_path.read_text(encoding="utf-8"))
        check = validate_report_payload(sample_path.name, data, require_findings=True)
        ok = ok and bool(check["ok"])
        checks.append(check)
    return {"ok": ok, "checks": checks}
