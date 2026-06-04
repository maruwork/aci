#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normalized finding helpers for ACI structure signals."""
from __future__ import annotations

from dataclasses import asdict, dataclass

try:
    from .aci_wording import SUGGESTED_ACTIONS
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_wording import SUGGESTED_ACTIONS


STRUCTURE_SIGNAL_TO_CI_ID: dict[str, str] = {
    "RESPONSIBILITY_SPROUT": "CI-04",
    "SIDE_PROGRAM_LEAK": "CI-19",
    "SHELF_BOUNDARY_BREAK": "CI-23",
    "OPERATOR_VIEW_GAP": "CI-24",
    "PATCHWORK_GRAFT": "CI-27",
}


@dataclass(frozen=True)
class AciFinding:
    finding_id: str
    ci_id: str
    signal: str
    severity: str
    actor_label: str
    owner_lane: str
    target_file: str
    line: int | None
    reason: str
    evidence_ref: str
    recommended_action: str
    verification_status: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def structure_signal_ci_id(signal: str) -> str:
    try:
        return STRUCTURE_SIGNAL_TO_CI_ID[signal]
    except KeyError as exc:  # pragma: no cover - bounded caller contract
        raise ValueError(f"Unknown structure signal: {signal}") from exc


def build_structure_finding(
    *,
    finding_id: str,
    signal: str,
    severity: str,
    target_file: str,
    reason: str,
    evidence_ref: str,
    line: int | None = None,
    actor_label: str = "ACI-detected",
    owner_lane: str = "human-judgment",
    verification_status: str = "detected",
    recommended_action: str | None = None,
) -> AciFinding:
    ci_id = structure_signal_ci_id(signal)
    return AciFinding(
        finding_id=finding_id,
        ci_id=ci_id,
        signal=signal,
        severity=severity,
        actor_label=actor_label,
        owner_lane=owner_lane,
        target_file=target_file,
        line=line,
        reason=reason,
        evidence_ref=evidence_ref,
        recommended_action=recommended_action or SUGGESTED_ACTIONS[signal],
        verification_status=verification_status,
    )
