#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ACI profile wiring and project-replaced runtime defaults."""
from __future__ import annotations

try:
    from .aci_signals import (
        STRUCTURE_SIGNALS as PROJECT_STRUCTURE_SIGNALS,
        SIGNAL_RESPONSIBILITY_SPROUT, SIGNAL_SIDE_PROGRAM_LEAK,
        SIGNAL_OPERATOR_VIEW_GAP, SIGNAL_STATE_DUPLICATION,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_signals import (
        STRUCTURE_SIGNALS as PROJECT_STRUCTURE_SIGNALS,
        SIGNAL_RESPONSIBILITY_SPROUT, SIGNAL_SIDE_PROGRAM_LEAK,
        SIGNAL_OPERATOR_VIEW_GAP, SIGNAL_STATE_DUPLICATION,
    )

PROFILE_STARTUP = "startup"
PROFILE_QUICK_GATE = "quick-gate"
PROFILE_STATE_CHANGE = "state-change"
PROFILE_WRAP_UP = "wrap-up"
PROFILE_FULL = "full"
PROFILE_SELF_AUDIT = "self-audit"
PROFILE_BUILD_PREFLIGHT = "build-preflight"
PROFILE_BUILD_REVIEW = "build-review"

SUPPORTED_PROFILES = (
    PROFILE_STARTUP,
    PROFILE_QUICK_GATE,
    PROFILE_STATE_CHANGE,
    PROFILE_WRAP_UP,
    PROFILE_FULL,
    PROFILE_SELF_AUDIT,
    PROFILE_BUILD_PREFLIGHT,
    PROFILE_BUILD_REVIEW,
)

BUILD_SIDE_PROFILES = {PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW}
PROFILE_REQUIRES_TARGETED_SCOPE = {PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_STATE_CHANGE}

PROFILE_DEFAULT_SCOPE_REFS: dict[str, tuple[str, ...]] = {
    PROFILE_STARTUP: (
        "{project_runtime_shelf}",
        "{project_current_state_shelf}",
        "{project_entry_shelf}",
    ),
    PROFILE_QUICK_GATE: (
        "{project_runtime_shelf}",
        "{project_current_state_shelf}",
        "{project_entry_shelf}",
    ),
    PROFILE_WRAP_UP: (
        "{project_runtime_shelf}",
        "{project_current_state_shelf}",
        "{project_entry_shelf}",
    ),
}

PROFILE_DEFAULT_SCOPE_MODES: dict[str, str] = {
    PROFILE_SELF_AUDIT: "self-audit",
}

STRUCTURE_SIGNAL_SET: tuple[str, ...] = PROJECT_STRUCTURE_SIGNALS

TOP_LEVEL_SIGNALS: frozenset[str] = frozenset(STRUCTURE_SIGNAL_SET)


def build_profile_signals(
    *,
    structure_signals: tuple[str, ...],
    external_evidence_signals: tuple[str, ...],
    human_judgment_signals: tuple[str, ...],
    native_hygiene_signals: tuple[str, ...],
    opt_in_native_signals: tuple[str, ...] = (),
) -> dict[str, tuple[str, ...]]:
    # opt_in_native_signals are wholly-low-confidence native detectors that the
    # default scan does NOT apply; only the exhaustive profiles (full, self-audit)
    # opt into them. See aci_scan._OPT_IN_NATIVE_SIGNALS for the criterion.
    return {
        PROFILE_STARTUP: (
            *structure_signals,
            "CI04_GOD_CLASS",
            "CI12_POLTERGEIST",
            "CI02_SPAGHETTI_CODE",
        ),
        PROFILE_QUICK_GATE: (
            *structure_signals,
            *external_evidence_signals,
            *native_hygiene_signals,
        ),
        PROFILE_STATE_CHANGE: (
            SIGNAL_STATE_DUPLICATION,
            SIGNAL_SIDE_PROGRAM_LEAK,
            SIGNAL_OPERATOR_VIEW_GAP,
            "CI21_BROAD_EXCEPTION_SWALLOW",
            "CI22_RESOURCE_CLEANUP_GAP",
            "CI23_CONTRACT_FIELD_DRIFT",
            "CI25_ENVIRONMENT_DRIFT",
            "CI26_RACE_HAZARD",
        ),
        PROFILE_WRAP_UP: (
            SIGNAL_RESPONSIBILITY_SPROUT,
            SIGNAL_SIDE_PROGRAM_LEAK,
            SIGNAL_OPERATOR_VIEW_GAP,
            "CI03_TODO_HACK",
            "CI23_CONTRACT_FIELD_DRIFT",
        ),
        PROFILE_FULL: (
            *structure_signals,
            *external_evidence_signals,
            *human_judgment_signals,
            *native_hygiene_signals,
            *opt_in_native_signals,
        ),
        PROFILE_SELF_AUDIT: (
            *structure_signals,
            *external_evidence_signals,
            *human_judgment_signals,
            *native_hygiene_signals,
            *opt_in_native_signals,
        ),
        PROFILE_BUILD_PREFLIGHT: (
            SIGNAL_RESPONSIBILITY_SPROUT,
            SIGNAL_STATE_DUPLICATION,
            SIGNAL_SIDE_PROGRAM_LEAK,
            *external_evidence_signals,
            *human_judgment_signals,
            *native_hygiene_signals,
        ),
        PROFILE_BUILD_REVIEW: (
            SIGNAL_STATE_DUPLICATION,
            SIGNAL_RESPONSIBILITY_SPROUT,
            SIGNAL_SIDE_PROGRAM_LEAK,
            SIGNAL_OPERATOR_VIEW_GAP,
            *external_evidence_signals,
            *human_judgment_signals,
            *native_hygiene_signals,
        ),
    }


def default_external_analyzers(profile: str) -> tuple[str, ...]:
    return {
        PROFILE_QUICK_GATE: ("ruff", "pyflakes"),
        PROFILE_SELF_AUDIT: ("ruff", "pyflakes", "mypy", "pytest", "semgrep", "eslint", "tsc", "shellcheck", "sqlfluff"),
        PROFILE_BUILD_PREFLIGHT: ("ruff", "pyflakes", "mypy", "semgrep", "eslint", "tsc", "shellcheck", "sqlfluff"),
        PROFILE_BUILD_REVIEW: ("ruff", "pyflakes", "mypy", "pytest", "semgrep", "eslint", "tsc", "shellcheck", "sqlfluff"),
        PROFILE_FULL: ("ruff", "pyflakes", "mypy", "pytest", "semgrep", "eslint", "tsc", "shellcheck", "sqlfluff"),
    }.get(profile, ())


def default_scope_mode(profile: str) -> str | None:
    return PROFILE_DEFAULT_SCOPE_MODES.get(profile)


def default_control_lane(profile: str) -> str:
    if profile in {PROFILE_STARTUP, PROFILE_STATE_CHANGE, PROFILE_WRAP_UP, PROFILE_SELF_AUDIT}:
        return "workflow-controlled"
    if profile == PROFILE_QUICK_GATE:
        return "background-controlled"
    return "UI-controlled"
