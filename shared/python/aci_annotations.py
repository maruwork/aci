#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub Actions workflow-command annotation emitter for ACI scan reports."""
from __future__ import annotations

try:
    from .aci_findings import SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW
    from .aci_report_helpers import (
        gate_scope_classes as _gate_scope_classes,
        scope_class as _scope_class,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW
    from aci_report_helpers import (  # type: ignore[no-redef]
        gate_scope_classes as _gate_scope_classes,
        scope_class as _scope_class,
    )


_SEVERITY_TO_LEVEL: dict[str, str] = {
    SEVERITY_CRITICAL: "error",
    SEVERITY_HIGH: "error",
    SEVERITY_MEDIUM: "warning",
    SEVERITY_LOW: "notice",
}


def _encode_param(value: str) -> str:
    """Percent-encode characters that break GitHub Actions workflow command parsing."""
    return (
        value
        .replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )


def _encode_message(value: str) -> str:
    """Percent-encode characters that break the workflow command message field."""
    return (
        value
        .replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )


def build_github_annotations(report: dict[str, object]) -> list[str]:
    """Return GitHub Actions workflow command strings for every finding in report.

    Each line is one annotation in the format::
        ::level file={path},line={n},title={ci_id signal}::{reason}

    Suppressions and waivers are included — the CI owner decides display policy.
    """
    raw_findings = report.get("findings") or []
    findings: list[dict[str, object]] = raw_findings if isinstance(raw_findings, list) else []
    gate_scope_classes = _gate_scope_classes(report)
    lines: list[str] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        scope_class = _scope_class(finding)
        advisory_only = scope_class not in gate_scope_classes
        level = "notice" if advisory_only else _SEVERITY_TO_LEVEL.get(str(finding.get("severity") or ""), "notice")
        file_ = _encode_param(str(finding.get("target_file") or ""))
        line_raw = finding.get("line")
        line_no = line_raw if isinstance(line_raw, int) else 1
        ci_id = str(finding.get("ci_id") or "")
        signal = str(finding.get("signal") or "")
        title = _encode_param(f"{ci_id} {signal}".strip())
        reason = str(finding.get("reason") or "")
        if advisory_only:
            reason = f"advisory-only ({scope_class}): {reason}"
        message = _encode_message(reason)
        lines.append(f"::{level} file={file_},line={line_no},title={title}::{message}")
    return lines
