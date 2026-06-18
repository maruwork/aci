#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded profile execution catalog for the common ACI shelf."""
from __future__ import annotations

from dataclasses import asdict, dataclass

try:
    from .aci_findings import LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER, LANE_HUMAN_JUDGMENT
    from .aci_profiles import (
        BUILD_SIDE_PROFILES,
        default_scope_mode,
        PROFILE_DEFAULT_SCOPE_REFS,
        PROFILE_REQUIRES_TARGETED_SCOPE,
        SUPPORTED_PROFILES,
        PROFILE_STARTUP, PROFILE_QUICK_GATE, PROFILE_STATE_CHANGE, PROFILE_WRAP_UP,
        PROFILE_FULL, PROFILE_SELF_AUDIT, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW,
        default_control_lane,
        default_external_analyzers,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER, LANE_HUMAN_JUDGMENT
    from aci_profiles import (
        BUILD_SIDE_PROFILES,
        default_scope_mode,
        PROFILE_DEFAULT_SCOPE_REFS,
        PROFILE_REQUIRES_TARGETED_SCOPE,
        SUPPORTED_PROFILES,
        PROFILE_STARTUP, PROFILE_QUICK_GATE, PROFILE_STATE_CHANGE, PROFILE_WRAP_UP,
        PROFILE_FULL, PROFILE_SELF_AUDIT, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW,
        default_control_lane,
        default_external_analyzers,
    )


PROFILE_SUPPORT_LEVELS: dict[str, str] = {
    "common-catalog": (
        "The common shelf can describe this profile and its bounded defaults. "
        "Downstream runtime scope, repository targeting, and workflow orchestration remain local responsibilities."
    ),
}

PROFILE_PURPOSES: dict[str, str] = {
    PROFILE_STARTUP: "initial structure-only review before deeper evidence lanes are needed",
    PROFILE_QUICK_GATE: "fast bounded gate that combines structure signals and lightweight external evidence",
    PROFILE_STATE_CHANGE: "focused review for state movement and boundary churn",
    PROFILE_WRAP_UP: "late-stage cleanup review for remaining structure seams and contract drift",
    PROFILE_FULL: "widest bounded common-shelf review surface across structure, analyzer, and human-judgment lanes",
    PROFILE_SELF_AUDIT: "stable self-audit surface for ACI itself, including runtime code, tests, maintainer probes, and roadmap evidence",
    PROFILE_BUILD_PREFLIGHT: "bounded pre-build review with stronger analyzer evidence before a larger execution step",
    PROFILE_BUILD_REVIEW: "bounded post-build-style review that combines build-side evidence and design boundary checks",
}

PROFILE_ENABLED_LANES: dict[str, tuple[str, ...]] = {
    PROFILE_STARTUP: (LANE_NATIVE_STATIC, LANE_HUMAN_JUDGMENT),
    PROFILE_QUICK_GATE: (LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER),
    PROFILE_STATE_CHANGE: (LANE_NATIVE_STATIC,),
    PROFILE_WRAP_UP: (LANE_NATIVE_STATIC, LANE_HUMAN_JUDGMENT),
    PROFILE_FULL: (LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER, LANE_HUMAN_JUDGMENT),
    PROFILE_SELF_AUDIT: (LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER, LANE_HUMAN_JUDGMENT),
    PROFILE_BUILD_PREFLIGHT: (LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER, LANE_HUMAN_JUDGMENT),
    PROFILE_BUILD_REVIEW: (LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER, LANE_HUMAN_JUDGMENT),
}


@dataclass(frozen=True)
class AciProfileCatalogEntry:
    profile_id: str
    purpose: str
    enabled_lanes: tuple[str, ...]
    default_external_analyzers: tuple[str, ...]
    control_lane: str
    scope_mode: str
    support_level: str
    ownership_boundary: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _scope_mode(profile_id: str) -> str:
    profile_default_scope_mode = default_scope_mode(profile_id)
    if profile_default_scope_mode is not None:
        return profile_default_scope_mode
    if profile_id in PROFILE_REQUIRES_TARGETED_SCOPE:
        return "bounded-target-required"
    if profile_id in PROFILE_DEFAULT_SCOPE_REFS:
        return "project-entry-default"
    return "profile-defined"


def _ownership_boundary(profile_id: str) -> str:
    if profile_id in BUILD_SIDE_PROFILES:
        return (
            "The common shelf catalogs this build-side profile and its bounded defaults only. "
            "Actual target selection, runner invocation, and repository-local gating remain downstream."
        )
    return (
        "The common shelf catalogs this profile and its generic defaults only. "
        "Downstream scope, target path selection, and workflow wiring remain local responsibilities."
    )


def profile_catalog() -> list[dict[str, object]]:
    entries = []
    for profile_id in SUPPORTED_PROFILES:
        entry = AciProfileCatalogEntry(
            profile_id=profile_id,
            purpose=PROFILE_PURPOSES[profile_id],
            enabled_lanes=PROFILE_ENABLED_LANES[profile_id],
            default_external_analyzers=default_external_analyzers(profile_id),
            control_lane=default_control_lane(profile_id),
            scope_mode=_scope_mode(profile_id),
            support_level="common-catalog",
            ownership_boundary=_ownership_boundary(profile_id),
        )
        entries.append(entry.as_dict())
    return entries


def profile_support_levels() -> dict[str, str]:
    return dict(PROFILE_SUPPORT_LEVELS)
