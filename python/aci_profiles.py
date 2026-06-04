#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ACI profile wiring and project-replaced runtime defaults."""
from __future__ import annotations

try:
    from .aci_signals import STRUCTURE_SIGNALS as PROJECT_STRUCTURE_SIGNALS
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_signals import STRUCTURE_SIGNALS as PROJECT_STRUCTURE_SIGNALS

SUPPORTED_PROFILES = (
    "startup",
    "quick-gate",
    "state-change",
    "wrap-up",
    "full",
    "build-preflight",
    "build-review",
)

BUILD_SIDE_PROFILES = {"build-preflight", "build-review"}
PROFILE_REQUIRES_TARGETED_SCOPE = {"build-preflight", "build-review"}

PROFILE_DEFAULT_SCOPE_REFS: dict[str, tuple[str, ...]] = {
    "startup": (
        "{project_runtime_shelf}",
        "{project_current_state_shelf}",
        "{project_entry_shelf}",
    ),
    "quick-gate": (
        "{project_runtime_shelf}",
        "{project_current_state_shelf}",
        "{project_entry_shelf}",
    ),
    "wrap-up": (
        "{project_runtime_shelf}",
        "{project_current_state_shelf}",
        "{project_entry_shelf}",
    ),
}

STRUCTURE_SIGNAL_SET: tuple[str, ...] = (
    "STATE_DUPLICATION",
    *PROJECT_STRUCTURE_SIGNALS,
)

TOP_LEVEL_SIGNALS: frozenset[str] = frozenset(STRUCTURE_SIGNAL_SET)


def build_profile_signals(
    *,
    structure_signals: tuple[str, ...],
    external_evidence_signals: tuple[str, ...],
    human_judgment_signals: tuple[str, ...],
    native_hygiene_signals: tuple[str, ...],
) -> dict[str, tuple[str, ...]]:
    return {
        "startup": structure_signals,
        "quick-gate": (
            *structure_signals,
            *external_evidence_signals,
            *native_hygiene_signals,
        ),
        "state-change": (
            "STATE_DUPLICATION",
            "SIDE_PROGRAM_LEAK",
            "SHELF_BOUNDARY_BREAK",
            "OPERATOR_VIEW_GAP",
            "PATCHWORK_GRAFT",
            "CI21_BROAD_EXCEPTION_SWALLOW",
            "CI22_RESOURCE_CLEANUP_GAP",
            "CI23_CONTRACT_FIELD_DRIFT",
            "CI25_ENVIRONMENT_DRIFT",
            "CI26_RACE_HAZARD",
        ),
        "wrap-up": (
            "RESPONSIBILITY_SPROUT",
            "SIDE_PROGRAM_LEAK",
            "SHELF_BOUNDARY_BREAK",
            "OPERATOR_VIEW_GAP",
            "PATCHWORK_GRAFT",
            "CI03_TODO_HACK",
            "CI23_CONTRACT_FIELD_DRIFT",
        ),
        "full": (
            *structure_signals,
            *external_evidence_signals,
            *human_judgment_signals,
            *native_hygiene_signals,
        ),
        "build-preflight": (
            "RESPONSIBILITY_SPROUT",
            "STATE_DUPLICATION",
            "SIDE_PROGRAM_LEAK",
            *external_evidence_signals,
            *human_judgment_signals,
            *native_hygiene_signals,
        ),
        "build-review": (
            "STATE_DUPLICATION",
            "RESPONSIBILITY_SPROUT",
            "SIDE_PROGRAM_LEAK",
            "OPERATOR_VIEW_GAP",
            "PATCHWORK_GRAFT",
            *external_evidence_signals,
            *human_judgment_signals,
            *native_hygiene_signals,
        ),
    }


def default_external_analyzers(profile: str) -> tuple[str, ...]:
    return {
        "quick-gate": ("ruff", "pyflakes"),
        "build-preflight": ("ruff", "pyflakes", "mypy"),
        "build-review": ("ruff", "pyflakes", "mypy", "pytest"),
        "full": ("ruff", "pyflakes", "mypy", "pytest"),
    }.get(profile, ())


def default_control_lane(profile: str) -> str:
    if profile in {"startup", "state-change", "wrap-up"}:
        return "workflow-controlled"
    if profile == "quick-gate":
        return "background-controlled"
    return "UI-controlled"
