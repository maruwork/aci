#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normalized finding helpers for ACI structure signals."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass

try:
    from .aci_signals import (
        SIGNAL_RESPONSIBILITY_SPROUT, SIGNAL_SIDE_PROGRAM_LEAK,
        SIGNAL_OPERATOR_VIEW_GAP, SIGNAL_STATE_DUPLICATION,
    )
    from .aci_wording import SUGGESTED_ACTIONS
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_signals import (
        SIGNAL_RESPONSIBILITY_SPROUT, SIGNAL_SIDE_PROGRAM_LEAK,
        SIGNAL_OPERATOR_VIEW_GAP, SIGNAL_STATE_DUPLICATION,
    )
    from aci_wording import SUGGESTED_ACTIONS


LANE_NATIVE_STATIC = "native-static"
LANE_EXTERNAL_ANALYZER = "external-analyzer"
LANE_HUMAN_JUDGMENT = "human-judgment"

VERIFICATION_DETECTED = "detected"
VERIFICATION_EXECUTED = "executed"

SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"

FINDING_CLASS_CONFIRMED_DEFECT = "confirmed defect"
FINDING_CLASS_DESIGN_REVIEW = "design/review question"

# CI-IDs where the finding represents a design/scope question rather than a clear defect.
# Callers should treat these as discussion starters, not mandatory fixes.
_DESIGN_REVIEW_CI_IDS: frozenset[str] = frozenset({"CI-06", "CI-08", "CI-11", "CI-12"})


def _finding_class_for(ci_id: str) -> str:
    return FINDING_CLASS_DESIGN_REVIEW if ci_id in _DESIGN_REVIEW_CI_IDS else FINDING_CLASS_CONFIRMED_DEFECT


STRUCTURE_SIGNAL_TO_CI_ID: dict[str, str] = {
    SIGNAL_RESPONSIBILITY_SPROUT: "CI-04",
    SIGNAL_SIDE_PROGRAM_LEAK: "CI-19",
    SIGNAL_OPERATOR_VIEW_GAP: "CI-24",
    SIGNAL_STATE_DUPLICATION: "CI-20",
}


@dataclass(frozen=True)
class AciFinding:
    finding_id: str
    fingerprint: str
    ci_id: str
    signal: str
    severity: str
    confidence: str
    actor_label: str
    triage_state: str
    priority: str
    fixability: str
    baseline_status: str
    waiver_status: str
    lifecycle_state: str
    owner_lane: str
    target_file: str
    line: int | None
    excerpt: str
    reason: str
    evidence_ref: str
    recommended_action: str
    verification_status: str
    finding_class: str = "confirmed defect"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def structure_signal_ci_id(signal: str) -> str:
    try:
        return STRUCTURE_SIGNAL_TO_CI_ID[signal]
    except KeyError as exc:  # pragma: no cover - bounded caller contract
        raise ValueError(f"Unknown structure signal: {signal}") from exc


def build_finding_fingerprint(
    *,
    ci_id: str,
    signal: str,
    target_file: str,
    line: int | None,
    reason: str,
) -> str:
    stable_key = "|".join(
        [
            ci_id.strip(),
            signal.strip(),
            target_file.strip(),
            "" if line is None else str(line),
            reason.strip(),
        ]
    )
    return hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:16]


def build_legacy_location_key(
    *,
    ci_id: str,
    target_file: str,
    line: int | None,
) -> str:
    return f"{ci_id}|{target_file}|{'' if line is None else line}"


def build_structure_finding(
    *,
    finding_id: str,
    signal: str,
    severity: str,
    target_file: str,
    reason: str,
    evidence_ref: str,
    line: int | None = None,
    excerpt: str = "",
    actor_label: str = "ACI-detected",
    confidence: str = "medium",
    triage_state: str = "review-first",
    priority: str = "P2",
    fixability: str = "owner-decision",
    baseline_status: str = "new",
    waiver_status: str = "none",
    lifecycle_state: str = "open",
    owner_lane: str = LANE_HUMAN_JUDGMENT,
    verification_status: str = VERIFICATION_DETECTED,
    recommended_action: str | None = None,
) -> AciFinding:
    ci_id = structure_signal_ci_id(signal)
    return AciFinding(
        finding_id=finding_id,
        fingerprint=build_finding_fingerprint(
            ci_id=ci_id,
            signal=signal,
            target_file=target_file,
            line=line,
            reason=reason,
        ),
        ci_id=ci_id,
        signal=signal,
        severity=severity,
        confidence=confidence,
        actor_label=actor_label,
        triage_state=triage_state,
        priority=priority,
        fixability=fixability,
        baseline_status=baseline_status,
        waiver_status=waiver_status,
        lifecycle_state=lifecycle_state,
        owner_lane=owner_lane,
        target_file=target_file,
        line=line,
        excerpt=excerpt,
        reason=reason,
        evidence_ref=evidence_ref,
        recommended_action=recommended_action or SUGGESTED_ACTIONS[signal],
        verification_status=verification_status,
    )


def build_finding(
    *,
    finding_id: str,
    ci_id: str,
    signal: str,
    severity: str,
    target_file: str,
    reason: str,
    evidence_ref: str,
    line: int | None = None,
    excerpt: str = "",
    actor_label: str = "ACI-detected",
    confidence: str = "medium",
    triage_state: str = "review-first",
    priority: str = "P2",
    fixability: str = "owner-decision",
    baseline_status: str = "new",
    waiver_status: str = "none",
    lifecycle_state: str = "open",
    owner_lane: str = LANE_HUMAN_JUDGMENT,
    verification_status: str = VERIFICATION_DETECTED,
    fingerprint: str | None = None,
    recommended_action: str = "Review the evidence and route the finding to the smallest owning surface.",
) -> AciFinding:
    return AciFinding(
        finding_id=finding_id,
        fingerprint=fingerprint
        or build_finding_fingerprint(
            ci_id=ci_id,
            signal=signal,
            target_file=target_file,
            line=line,
            reason=reason,
        ),
        ci_id=ci_id,
        signal=signal,
        severity=severity,
        confidence=confidence,
        actor_label=actor_label,
        triage_state=triage_state,
        priority=priority,
        fixability=fixability,
        baseline_status=baseline_status,
        waiver_status=waiver_status,
        lifecycle_state=lifecycle_state,
        owner_lane=owner_lane,
        target_file=target_file,
        line=line,
        excerpt=excerpt,
        reason=reason,
        evidence_ref=evidence_ref,
        recommended_action=recommended_action,
        verification_status=verification_status,
        finding_class=_finding_class_for(ci_id),
    )
