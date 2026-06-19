"""Scan report and gate assembly.

One concern: turn a processed finding list into the report's summary, review
brief, gate decision, blockers, and residuals. Finding post-processing (dedup,
scope-noise filtering, baseline/waiver application) is a separate concern in
_scan_postprocess.py; configuration it reads lives in aci_scan.
"""
from __future__ import annotations

from collections import Counter
from typing import cast

try:
    from .aci_findings import AciFinding, LANE_HUMAN_JUDGMENT, SEVERITY_CRITICAL, SEVERITY_HIGH
    from .aci_scan import (
        SCOPE_CLASS_RUNTIME_SOURCE, SEVERITY_RANK, ScanSession, _classify_relative_path,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import AciFinding, LANE_HUMAN_JUDGMENT, SEVERITY_CRITICAL, SEVERITY_HIGH  # type: ignore[no-redef]
    from aci_scan import (  # type: ignore[no-redef]
        SCOPE_CLASS_RUNTIME_SOURCE, SEVERITY_RANK, ScanSession, _classify_relative_path,
    )


def _build_summary(findings: list[AciFinding]) -> dict[str, object]:
    severity_counts = Counter(item.severity for item in findings)
    confidence_counts = Counter(item.confidence for item in findings)
    actor_counts = Counter(item.actor_label for item in findings)
    triage_counts = Counter(item.triage_state for item in findings)
    priority_counts = Counter(item.priority for item in findings)
    baseline_counts = Counter(item.baseline_status for item in findings)
    lifecycle_counts = Counter(item.lifecycle_state for item in findings)
    owner_lane_counts = Counter(item.owner_lane for item in findings)
    scope_class_counts = Counter(_classify_relative_path(item.target_file) for item in findings)
    gated_count = sum(
        1 for item in findings if _classify_relative_path(item.target_file) == SCOPE_CLASS_RUNTIME_SOURCE
    )
    advisory_scope_class_counts = Counter(
        _classify_relative_path(item.target_file)
        for item in findings
        if _classify_relative_path(item.target_file) != SCOPE_CLASS_RUNTIME_SOURCE
    )
    blocking = [
        item
        for item in findings
        if item.severity in {SEVERITY_CRITICAL, SEVERITY_HIGH} and item.waiver_status == "none"
        and _classify_relative_path(item.target_file) == SCOPE_CLASS_RUNTIME_SOURCE
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
        "advisory_by_scope_class": dict(advisory_scope_class_counts),
        "waived_count": sum(1 for item in findings if item.waiver_status != "none"),
        "suppressed_count": 0,
        "new_count": sum(1 for item in findings if item.baseline_status == "new"),
        "existing_baseline_count": sum(
            1 for item in findings if item.baseline_status == "existing-baseline"
        ),
        "blocker_count": len(blocking),
        "residual_count": sum(1 for item in findings if item.triage_state == "accepted-residual"),
    }


def _top_counts(values: list[str], *, limit: int = 5) -> list[dict[str, object]]:
    counter = Counter(values)
    return [
        {"name": name, "count": count}
        for name, count in counter.most_common(limit)
    ]


def _build_review_brief(
    findings: list[AciFinding],
    blockers: list[dict[str, object]],
    analyzer_runs: list[dict[str, object]],
    session: ScanSession,
    gate: dict[str, object],
) -> dict[str, object]:
    top_files = _top_counts([finding.target_file for finding in findings])
    top_signals = _top_counts([finding.signal for finding in findings])
    top_scope_classes = _top_counts([_classify_relative_path(finding.target_file) for finding in findings])
    advisory_scope_classes = _top_counts(
        [
            _classify_relative_path(finding.target_file)
            for finding in findings
            if _classify_relative_path(finding.target_file) not in session.gate_scope_classes
        ]
    )
    availability_note_states = {
        "not-installed",
        "version-or-runtime-problem",
        "downstream-setup-required",
    }
    analyzer_failures = [
        {
            "analyzer_id": str(run.get("analyzer_id") or ""),
            "runtime_state": str(run.get("runtime_state") or ""),
        }
        for run in analyzer_runs
        if str(run.get("runtime_state") or "") not in {"executed", "no-tests-collected", "no-applicable-source"}
        and str(run.get("runtime_state") or "") not in availability_note_states
    ]
    analyzer_availability_notes = [
        {
            "analyzer_id": str(run.get("analyzer_id") or ""),
            "runtime_state": str(run.get("runtime_state") or ""),
        }
        for run in analyzer_runs
        if str(run.get("runtime_state") or "") in availability_note_states
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
    advisory_count = sum(
        1 for finding in findings if _classify_relative_path(finding.target_file) not in session.gate_scope_classes
    )
    advisory_headline = (
        "No advisory-only findings remain outside the gate."
        if advisory_count == 0
        else (
            f"{advisory_count} advisory-only finding{'s' if advisory_count != 1 else ''} "
            f"{'sit' if advisory_count != 1 else 'sits'} outside the gate in "
            f"{', '.join(str(item.get('name') or '') for item in advisory_scope_classes)}."
        )
    )
    recommended_focus = ["Start with the hottest files and highest-severity signals."]
    if analyzer_failures:
        recommended_focus.append("Resolve analyzer runtime failures before trusting an all-clear.")
    elif analyzer_availability_notes:
        recommended_focus.append("Decide whether unavailable analyzers are required for this environment or CI lane.")
    if advisory_count:
        recommended_focus.append(
            "Triage tests, fixtures, docs, roadmap, and support findings separately from runtime blockers."
        )
    return {
        "gate_decision": gate.get("decision", "fail"),
        "scope_mode": session.scope_mode,
        "diff_from": session.diff_from,
        "blocker_headline": blocker_headline,
        "advisory_headline": advisory_headline,
        "top_files": top_files,
        "top_signals": top_signals,
        "top_scope_classes": top_scope_classes,
        "advisory_scope_classes": advisory_scope_classes,
        "analyzer_failures": analyzer_failures,
        "analyzer_availability_notes": analyzer_availability_notes,
        "recommended_focus": recommended_focus,
    }


def _build_gate_result(
    findings: list[AciFinding],
    *,
    severity_threshold: str,
    fail_on_new_findings: bool,
    fail_on_unreviewed_review_required: bool,
    fail_on_analyzer_errors: bool,
    analyzer_runs: list[dict[str, object]],
) -> dict[str, object]:
    threshold_rank = SEVERITY_RANK[severity_threshold]
    blocking = [
        item
        for item in findings
        if SEVERITY_RANK[item.severity] >= threshold_rank and item.waiver_status == "none"
    ]
    reasons: list[str] = []
    if blocking:
        reasons.append("severity-threshold")
    if fail_on_new_findings and any(
        item.baseline_status == "new" and item.waiver_status == "none" for item in findings
    ):
        reasons.append("new-findings-present")
    unreviewed = [
        item
        for item in findings
        if (
            item.owner_lane == LANE_HUMAN_JUDGMENT
            and item.waiver_status == "none"
            and item.baseline_status == "new"
        )
    ]
    if fail_on_unreviewed_review_required and unreviewed:
        reasons.append("unreviewed-review-required")
    analyzer_failures = [item for item in analyzer_runs if not item["ok"]]
    if fail_on_analyzer_errors and analyzer_failures:
        reasons.append("analyzer-runtime-error")
    reason_details: list[dict[str, object]] = []
    if "severity-threshold" in reasons:
        reason_details.append(
            {
                "reason": "severity-threshold",
                "count": len(blocking),
                "finding_ids": [item.finding_id for item in blocking],
            }
        )
    if "new-findings-present" in reasons:
        new_findings = [
            item for item in findings
            if item.baseline_status == "new" and item.waiver_status == "none"
        ]
        reason_details.append(
            {
                "reason": "new-findings-present",
                "count": len(new_findings),
                "finding_ids": [item.finding_id for item in new_findings],
            }
        )
    if "unreviewed-review-required" in reasons:
        reason_details.append(
            {
                "reason": "unreviewed-review-required",
                "count": len(unreviewed),
                "finding_ids": [item.finding_id for item in unreviewed],
            }
        )
    if "analyzer-runtime-error" in reasons:
        reason_details.append(
            {
                "reason": "analyzer-runtime-error",
                "count": len(analyzer_failures),
                "analyzers": [item["analyzer_id"] for item in analyzer_failures],
            }
        )
    return {
        "decision": "fail" if reasons else "pass",
        "blocking_severities": [
            severity for severity, rank in SEVERITY_RANK.items() if rank >= threshold_rank
        ],
        "blocking_count": len(blocking),
        "unreviewed_review_required_count": len(unreviewed),
        "analyzer_failure_count": len(analyzer_failures),
        "reasons": reasons,
        "reason_details": reason_details,
        "severity_threshold": severity_threshold,
        "fail_on_new_findings": fail_on_new_findings,
        "fail_on_unreviewed_review_required": fail_on_unreviewed_review_required,
        "fail_on_analyzer_errors": fail_on_analyzer_errors,
    }


def _build_blockers(findings: list[AciFinding], gate: dict[str, object]) -> list[dict[str, object]]:
    threshold_levels = set(cast("list[str]", gate["blocking_severities"]))
    blockers: list[dict[str, object]] = []
    for finding in findings:
        if finding.severity not in threshold_levels:
            continue
        if finding.waiver_status != "none":
            continue
        blockers.append(
            {
                "blocker_id": f"B-{finding.finding_id}",
                "finding_id": finding.finding_id,
                "signal": finding.signal,
                "severity": finding.severity,
                "target_file": finding.target_file,
                "line": finding.line,
                "reason": finding.reason,
                "required_decision": "resolve-or-waive",
                "resume_condition": "all blockers resolved or explicitly waived",
            }
        )
    return blockers


def _build_residuals(findings: list[AciFinding]) -> list[dict[str, object]]:
    residuals: list[dict[str, object]] = []
    for finding in findings:
        if finding.triage_state != "accepted-residual":
            continue
        residuals.append(
            {
                "residual_id": f"R-{finding.finding_id}",
                "classification": "accepted-risk",
                "reason": finding.reason,
                "target_file": finding.target_file,
                "line": finding.line,
                "next_wave": "recheck when the owning boundary changes",
            }
        )
    return residuals








