#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report projection helpers for scope/owner-lane triage views."""
from __future__ import annotations

from collections import Counter
from typing import cast

try:
    from .aci_findings import (
        LANE_EXTERNAL_ANALYZER,
        LANE_HUMAN_JUDGMENT,
        LANE_NATIVE_STATIC,
        SEVERITY_CRITICAL,
        SEVERITY_HIGH,
        SEVERITY_LOW,
        SEVERITY_MEDIUM,
    )
    from .aci_scan import (
        SCOPE_CLASS_DOCS_EVIDENCE,
        SCOPE_CLASS_FIXTURES,
        SCOPE_CLASS_GENERATED,
        SCOPE_CLASS_MAINTAINER_PROBES,
        SCOPE_CLASS_ROADMAP_EVIDENCE,
        SCOPE_CLASS_RUNTIME_SOURCE,
        SCOPE_CLASS_SUPPORT,
        SCOPE_CLASS_TESTS,
        _classify_relative_path,
    )
    from .aci_report_helpers import report_map as _report_map, gate_scope_classes as _gate_scope_classes
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        LANE_EXTERNAL_ANALYZER,
        LANE_HUMAN_JUDGMENT,
        LANE_NATIVE_STATIC,
        SEVERITY_CRITICAL,
        SEVERITY_HIGH,
        SEVERITY_LOW,
        SEVERITY_MEDIUM,
    )
    from aci_scan import (  # type: ignore[no-redef]
        SCOPE_CLASS_DOCS_EVIDENCE,
        SCOPE_CLASS_FIXTURES,
        SCOPE_CLASS_GENERATED,
        SCOPE_CLASS_MAINTAINER_PROBES,
        SCOPE_CLASS_ROADMAP_EVIDENCE,
        SCOPE_CLASS_RUNTIME_SOURCE,
        SCOPE_CLASS_SUPPORT,
        SCOPE_CLASS_TESTS,
        _classify_relative_path,
    )
    from aci_report_helpers import report_map as _report_map, gate_scope_classes as _gate_scope_classes  # type: ignore[no-redef]


SUPPORTED_REPORT_SCOPE_CLASSES: tuple[str, ...] = (
    SCOPE_CLASS_RUNTIME_SOURCE,
    SCOPE_CLASS_TESTS,
    SCOPE_CLASS_FIXTURES,
    SCOPE_CLASS_DOCS_EVIDENCE,
    SCOPE_CLASS_ROADMAP_EVIDENCE,
    SCOPE_CLASS_MAINTAINER_PROBES,
    SCOPE_CLASS_SUPPORT,
    SCOPE_CLASS_GENERATED,
)
SUPPORTED_REPORT_OWNER_LANES: tuple[str, ...] = (
    LANE_NATIVE_STATIC,
    LANE_EXTERNAL_ANALYZER,
    LANE_HUMAN_JUDGMENT,
)

_SEVERITY_RANK = {
    SEVERITY_LOW: 1,
    SEVERITY_MEDIUM: 2,
    SEVERITY_HIGH: 3,
    SEVERITY_CRITICAL: 4,
}
_NON_FAILING_ANALYZER_RUNTIME_STATES = {
    "executed",
    "no-tests-collected",
    "no-applicable-source",
    "not-installed",
    "version-or-runtime-problem",
    "downstream-setup-required",
}


def _report_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [cast(dict[str, object], item) for item in value if isinstance(item, dict)]


def _report_list_of_strs(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _report_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text:
            try:
                return int(text)
            except ValueError:
                return default
    return default


def _normalized_values(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if not values:
        return ()
    return tuple(sorted({str(value).strip() for value in values if str(value).strip()}))


def validate_report_view_filters(
    scope_classes: tuple[str, ...] | list[str] | None,
    owner_lanes: tuple[str, ...] | list[str] | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    normalized_scope = _normalized_values(scope_classes)
    normalized_lanes = _normalized_values(owner_lanes)
    unknown_scope = sorted(set(normalized_scope) - set(SUPPORTED_REPORT_SCOPE_CLASSES))
    if unknown_scope:
        raise ValueError(
            f"Unsupported report scope_class filter(s): {', '.join(unknown_scope)}"
        )
    unknown_lanes = sorted(set(normalized_lanes) - set(SUPPORTED_REPORT_OWNER_LANES))
    if unknown_lanes:
        raise ValueError(
            f"Unsupported report owner_lane filter(s): {', '.join(unknown_lanes)}"
        )
    return normalized_scope, normalized_lanes


def _row_scope_class(row: dict[str, object]) -> str:
    explicit = row.get("scope_class")
    if isinstance(explicit, str) and explicit:
        return explicit
    return _classify_relative_path(str(row.get("target_file") or ""))


def _row_line(row: dict[str, object]) -> int | None:
    line = row.get("line")
    return line if isinstance(line, int) else None


def _top_counts(values: list[str], *, limit: int = 5) -> list[dict[str, object]]:
    counter = Counter(value for value in values if value)
    return [{"name": name, "count": count} for name, count in counter.most_common(limit)]


def _filter_findings(
    findings: list[dict[str, object]],
    scope_classes: tuple[str, ...],
    owner_lanes: tuple[str, ...],
) -> list[dict[str, object]]:
    visible: list[dict[str, object]] = []
    for row in findings:
        scope_class = _row_scope_class(row)
        owner_lane = str(row.get("owner_lane") or "")
        if scope_classes and scope_class not in scope_classes:
            continue
        if owner_lanes and owner_lane not in owner_lanes:
            continue
        if "scope_class" not in row:
            row = dict(row)
            row["scope_class"] = scope_class
        visible.append(row)
    return visible


def _build_summary(
    findings: list[dict[str, object]],
    *,
    gate_scope_classes: tuple[str, ...],
    suppressed_count: int,
    resolved_baseline_count: int,
) -> dict[str, object]:
    severity_counts = Counter(str(item.get("severity") or "") for item in findings)
    confidence_counts = Counter(str(item.get("confidence") or "") for item in findings)
    actor_counts = Counter(str(item.get("actor_label") or "") for item in findings)
    triage_counts = Counter(str(item.get("triage_state") or "") for item in findings)
    priority_counts = Counter(str(item.get("priority") or "") for item in findings)
    baseline_counts = Counter(str(item.get("baseline_status") or "") for item in findings)
    lifecycle_counts = Counter(str(item.get("lifecycle_state") or "") for item in findings)
    owner_lane_counts = Counter(str(item.get("owner_lane") or "") for item in findings)
    scope_class_counts = Counter(_row_scope_class(item) for item in findings)
    gated_count = sum(1 for item in findings if _row_scope_class(item) in gate_scope_classes)
    advisory_counts = Counter(
        _row_scope_class(item)
        for item in findings
        if _row_scope_class(item) not in gate_scope_classes
    )
    blocking = [
        item
        for item in findings
        if str(item.get("severity") or "") in {SEVERITY_CRITICAL, SEVERITY_HIGH}
        and str(item.get("waiver_status") or "none") == "none"
        and _row_scope_class(item) in gate_scope_classes
    ]
    return {
        "total_findings": len(findings),
        "by_severity": dict(severity_counts),
        "by_confidence": dict(confidence_counts),
        "by_actor_label": dict(actor_counts),
        "by_triage_state": dict(triage_counts),
        "by_priority": dict(priority_counts),
        "by_baseline_status": dict(baseline_counts),
        "by_lifecycle_state": dict(lifecycle_counts),
        "by_owner_lane": dict(owner_lane_counts),
        "by_scope_class": dict(scope_class_counts),
        "by_scope_policy": {
            "gated": gated_count,
            "advisory": len(findings) - gated_count,
        },
        "advisory_by_scope_class": dict(advisory_counts),
        "waived_count": sum(1 for item in findings if str(item.get("waiver_status") or "none") != "none"),
        "suppressed_count": suppressed_count,
        "new_count": sum(1 for item in findings if str(item.get("baseline_status") or "") == "new"),
        "existing_baseline_count": sum(
            1 for item in findings if str(item.get("baseline_status") or "") == "existing-baseline"
        ),
        "blocker_count": len(blocking),
        "residual_count": sum(1 for item in findings if str(item.get("triage_state") or "") == "accepted-residual"),
        "resolved_baseline_count": resolved_baseline_count,
    }


def _build_blockers(
    findings: list[dict[str, object]],
    *,
    threshold_levels: set[str],
    gate_scope_classes: tuple[str, ...],
) -> list[dict[str, object]]:
    blockers: list[dict[str, object]] = []
    for finding in findings:
        if _row_scope_class(finding) not in gate_scope_classes:
            continue
        if str(finding.get("severity") or "") not in threshold_levels:
            continue
        if str(finding.get("waiver_status") or "none") != "none":
            continue
        blockers.append(
            {
                "blocker_id": f"B-{finding.get('finding_id', '')}",
                "finding_id": finding.get("finding_id", ""),
                "signal": finding.get("signal", ""),
                "severity": finding.get("severity", ""),
                "target_file": finding.get("target_file", ""),
                "line": _row_line(finding),
                "reason": finding.get("reason", ""),
                "required_decision": "resolve-or-waive",
                "resume_condition": "all blockers resolved or explicitly waived",
            }
        )
    return blockers


def _build_residuals(findings: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for finding in findings:
        if str(finding.get("triage_state") or "") != "accepted-residual":
            continue
        rows.append(
            {
                "residual_id": f"R-{finding.get('finding_id', '')}",
                "classification": "accepted-risk",
                "reason": finding.get("reason", ""),
                "target_file": finding.get("target_file", ""),
                "line": _row_line(finding),
                "next_wave": "recheck when the owning boundary changes",
            }
        )
    return rows


def _build_gate(
    findings: list[dict[str, object]],
    report: dict[str, object],
    *,
    gate_scope_classes: tuple[str, ...],
    blockers: list[dict[str, object]],
) -> dict[str, object]:
    source_gate = _report_map(report.get("gate"))
    severity_threshold = str(source_gate.get("severity_threshold") or SEVERITY_HIGH)
    threshold_rank = _SEVERITY_RANK.get(severity_threshold, _SEVERITY_RANK[SEVERITY_HIGH])
    blocking_severities = [
        severity for severity, rank in _SEVERITY_RANK.items() if rank >= threshold_rank
    ]
    fail_on_new_findings = bool(source_gate.get("fail_on_new_findings", False))
    fail_on_unreviewed_review_required = bool(
        source_gate.get("fail_on_unreviewed_review_required", False)
    )
    fail_on_analyzer_errors = bool(source_gate.get("fail_on_analyzer_errors", False))
    gated_findings = [
        item for item in findings if _row_scope_class(item) in gate_scope_classes
    ]
    new_findings = [
        item for item in gated_findings
        if str(item.get("baseline_status") or "") == "new"
        and str(item.get("waiver_status") or "none") == "none"
    ]
    unreviewed = [
        item for item in gated_findings
        if str(item.get("owner_lane") or "") == LANE_HUMAN_JUDGMENT
        and str(item.get("baseline_status") or "") == "new"
        and str(item.get("waiver_status") or "none") == "none"
    ]
    analyzer_runs = _report_rows(report.get("external_analyzer_runs"))
    analyzer_failures = [
        item for item in analyzer_runs
        if str(item.get("runtime_state") or "") not in _NON_FAILING_ANALYZER_RUNTIME_STATES
    ]
    reasons: list[str] = []
    if blockers:
        reasons.append("severity-threshold")
    if fail_on_new_findings and new_findings:
        reasons.append("new-findings-present")
    if fail_on_unreviewed_review_required and unreviewed:
        reasons.append("unreviewed-review-required")
    if fail_on_analyzer_errors and analyzer_failures:
        reasons.append("analyzer-runtime-error")
    reason_details: list[dict[str, object]] = []
    if blockers:
        reason_details.append(
            {
                "reason": "severity-threshold",
                "count": len(blockers),
                "finding_ids": [str(item.get("finding_id") or "") for item in blockers],
            }
        )
    if fail_on_new_findings and new_findings:
        reason_details.append(
            {
                "reason": "new-findings-present",
                "count": len(new_findings),
                "finding_ids": [str(item.get("finding_id") or "") for item in new_findings],
            }
        )
    if fail_on_unreviewed_review_required and unreviewed:
        reason_details.append(
            {
                "reason": "unreviewed-review-required",
                "count": len(unreviewed),
                "finding_ids": [str(item.get("finding_id") or "") for item in unreviewed],
            }
        )
    if fail_on_analyzer_errors and analyzer_failures:
        reason_details.append(
            {
                "reason": "analyzer-runtime-error",
                "count": len(analyzer_failures),
                "analyzers": [str(item.get("analyzer_id") or "") for item in analyzer_failures],
            }
        )
    return {
        "decision": "fail" if reasons else "pass",
        "blocking_severities": blocking_severities,
        "blocking_count": len(blockers),
        "unreviewed_review_required_count": len(unreviewed),
        "analyzer_failure_count": len(analyzer_failures),
        "reasons": reasons,
        "reason_details": reason_details,
        "severity_threshold": severity_threshold,
        "fail_on_new_findings": fail_on_new_findings,
        "fail_on_unreviewed_review_required": fail_on_unreviewed_review_required,
        "fail_on_analyzer_errors": fail_on_analyzer_errors,
    }


def _build_review_brief(
    findings: list[dict[str, object]],
    report: dict[str, object],
    *,
    gate_scope_classes: tuple[str, ...],
    blockers: list[dict[str, object]],
    gate: dict[str, object],
) -> dict[str, object]:
    source_brief = _report_map(report.get("review_brief"))
    advisory_scope_classes = [
        _row_scope_class(item)
        for item in findings
        if _row_scope_class(item) not in gate_scope_classes
    ]
    blocker_headline = (
        (
            "1 blocking finding needs owner action."
            if len(blockers) == 1
            else f"{len(blockers)} blocking findings need owner action."
        )
        if blockers
        else "No blocking findings remain in the gated scope."
    )
    advisory_count = len(advisory_scope_classes)
    if advisory_count:
        advisory_headline = (
            f"{advisory_count} advisory-only finding{'s' if advisory_count != 1 else ''} "
            f"{'sit' if advisory_count != 1 else 'sits'} outside the gate in "
            f"{', '.join(sorted(set(advisory_scope_classes)))}."
        )
    else:
        advisory_headline = "No advisory-only findings remain outside the gate in this view."
    return {
        "gate_decision": gate.get("decision", "fail"),
        "scope_mode": source_brief.get("scope_mode", _report_map(report.get("scope_rules")).get("scope_mode", "unknown")),
        "diff_from": source_brief.get("diff_from", _report_map(report.get("scope_rules")).get("diff_from")),
        "blocker_headline": blocker_headline,
        "advisory_headline": advisory_headline,
        "top_files": _top_counts([str(item.get("target_file") or "") for item in findings]),
        "top_signals": _top_counts([str(item.get("signal") or "") for item in findings]),
        "top_scope_classes": _top_counts([_row_scope_class(item) for item in findings]),
        "advisory_scope_classes": _top_counts(advisory_scope_classes),
        "analyzer_failures": _report_rows(source_brief.get("analyzer_failures")),
        "analyzer_availability_notes": _report_rows(source_brief.get("analyzer_availability_notes")),
        "recommended_focus": _report_list_of_strs(source_brief.get("recommended_focus")),
    }


def _build_next_actions(
    blockers: list[dict[str, object]],
    findings: list[dict[str, object]],
    *,
    gate_scope_classes: tuple[str, ...],
    is_filtered: bool,
) -> list[str]:
    advisory_count = sum(1 for item in findings if _row_scope_class(item) not in gate_scope_classes)
    actions: list[str] = []
    if blockers:
        actions.append("Review blocking findings first.")
    if advisory_count:
        actions.append(
            "Route tests, fixtures, docs, roadmap, and support findings through the non-runtime triage flow."
        )
    if not blockers and not advisory_count:
        actions.append("No blockers or advisory-only findings remain in this view.")
    if is_filtered:
        actions.append("Re-run without report-view filters before treating this view as the full scan picture.")
    return actions


def apply_report_view(
    report: dict[str, object],
    *,
    scope_classes: tuple[str, ...] | list[str] | None = None,
    owner_lanes: tuple[str, ...] | list[str] | None = None,
) -> dict[str, object]:
    """Project a full ACI report into a scope/owner-lane triage view."""
    normalized_scope, normalized_lanes = validate_report_view_filters(scope_classes, owner_lanes)
    source_findings = _report_rows(report.get("findings"))
    visible_findings = _filter_findings(source_findings, normalized_scope, normalized_lanes)
    gate_scope_classes = _gate_scope_classes(report)
    source_summary = _report_map(report.get("summary"))
    blockers = _build_blockers(
        visible_findings,
        threshold_levels=set(
            cast("list[str]", _report_map(report.get("gate")).get("blocking_severities", [SEVERITY_HIGH, SEVERITY_CRITICAL]))
        ),
        gate_scope_classes=gate_scope_classes,
    )
    residuals = _build_residuals(visible_findings)
    summary = _build_summary(
        visible_findings,
        gate_scope_classes=gate_scope_classes,
        suppressed_count=_report_int(source_summary.get("suppressed_count", 0), 0),
        resolved_baseline_count=_report_int(source_summary.get("resolved_baseline_count", 0), 0),
    )
    gate = _build_gate(
        visible_findings,
        report,
        gate_scope_classes=gate_scope_classes,
        blockers=blockers,
    )
    summary["blocker_count"] = len(blockers)
    summary["residual_count"] = len(residuals)
    is_filtered = bool(normalized_scope or normalized_lanes)
    projected = dict(report)
    projected["summary"] = summary
    projected["findings"] = visible_findings
    projected["blockers"] = blockers
    projected["residuals"] = residuals
    projected["gate"] = gate
    projected["review_brief"] = _build_review_brief(
        visible_findings,
        report,
        gate_scope_classes=gate_scope_classes,
        blockers=blockers,
        gate=gate,
    )
    projected["next_actions"] = _build_next_actions(
        blockers,
        visible_findings,
        gate_scope_classes=gate_scope_classes,
        is_filtered=is_filtered,
    )
    projected["report_view"] = {
        "projection_kind": "finding-view",
        "is_filtered": is_filtered,
        "filters_applied": {
            "scope_classes": list(normalized_scope),
            "owner_lanes": list(normalized_lanes),
        },
        "source_total_findings": len(source_findings),
        "visible_total_findings": len(visible_findings),
        "hidden_total_findings": max(len(source_findings) - len(visible_findings), 0),
        "source_blocker_count": _report_int(source_summary.get("blocker_count", 0), 0),
        "source_gate_decision": _report_map(report.get("gate")).get("decision", "fail"),
        "source_scope_mode": _report_map(report.get("scope_rules")).get("scope_mode", "unknown"),
        "filter_note": (
            "scan exit status is still decided from the source scan before report-view filters are applied"
            if is_filtered and str(report.get("command") or "") == "scan"
            else "unfiltered source report view"
        ),
    }
    return projected
