#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded external-analyzer catalog for the common ACI shelf."""
from __future__ import annotations

from dataclasses import asdict, dataclass

try:
    from .aci_profiles import (
        PROFILE_QUICK_GATE, PROFILE_FULL, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_profiles import (
        PROFILE_QUICK_GATE, PROFILE_FULL, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW,
    )


ANALYZER_SUPPORT_LEVELS: dict[str, str] = {
    "profile-default-catalog": (
        "Listed in the common shelf because one or more ACI profiles reference the analyzer "
        "as a default evidence source. Installation, invocation, and version pinning remain "
        "downstream responsibilities."
    ),
}


@dataclass(frozen=True)
class AciAnalyzerCatalogEntry:
    analyzer_id: str
    category: str
    purpose: str
    evidence_type: str
    support_level: str
    referenced_by_profiles: tuple[str, ...]
    typical_ci_ids: tuple[str, ...]
    ownership_boundary: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


ANALYZER_CATALOG: tuple[AciAnalyzerCatalogEntry, ...] = (
    AciAnalyzerCatalogEntry(
        analyzer_id="ruff",
        category="lint",
        purpose="fast lint and rule-based static evidence for code hygiene and contract drift",
        evidence_type="machine evidence",
        support_level="profile-default-catalog",
        referenced_by_profiles=(PROFILE_QUICK_GATE, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_FULL),
        typical_ci_ids=("CI-07", "CI-13", "CI-14", "CI-15", "CI-21", "CI-23", "CI-25"),
        ownership_boundary=(
            "The common shelf only catalogs that `ruff` is a recognized external evidence source. "
            "Actual execution flags, selected rules, and runtime wiring belong downstream."
        ),
    ),
    AciAnalyzerCatalogEntry(
        analyzer_id="pyflakes",
        category="lint",
        purpose="import, undefined-name, and dead-code style evidence for bounded Python review",
        evidence_type="machine evidence",
        support_level="profile-default-catalog",
        referenced_by_profiles=(PROFILE_QUICK_GATE, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_FULL),
        typical_ci_ids=("CI-07", "CI-13", "CI-21", "CI-23", "CI-25"),
        ownership_boundary=(
            "The common shelf only catalogs `pyflakes` as an allowed evidence lane. "
            "How a downstream project installs or invokes it is outside the common shelf."
        ),
    ),
    AciAnalyzerCatalogEntry(
        analyzer_id="mypy",
        category="type-check",
        purpose="static type and interface mismatch evidence",
        evidence_type="machine evidence",
        support_level="profile-default-catalog",
        referenced_by_profiles=(PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_FULL),
        typical_ci_ids=("CI-15", "CI-23", "CI-25"),
        ownership_boundary=(
            "The common shelf catalogs `mypy` because some bounded profiles expect type evidence. "
            "Type configuration, plugin setup, and path scope remain downstream."
        ),
    ),
    AciAnalyzerCatalogEntry(
        analyzer_id="pytest",
        category="test",
        purpose="test execution evidence for regression and fixture behavior",
        evidence_type="machine evidence",
        support_level="profile-default-catalog",
        referenced_by_profiles=(PROFILE_BUILD_REVIEW, PROFILE_FULL),
        typical_ci_ids=("CI-09", "CI-23", "CI-25"),
        ownership_boundary=(
            "The common shelf catalogs `pytest` as a recognized external evidence source. "
            "Test environment, markers, selection scope, and exit handling remain downstream."
        ),
    ),
    AciAnalyzerCatalogEntry(
        analyzer_id="eslint",
        category="lint",
        purpose="JS/TS rule-based static analysis for code quality, import hygiene, and type contract violations",
        evidence_type="machine evidence",
        support_level="profile-default-catalog",
        referenced_by_profiles=(),
        typical_ci_ids=("CI-02", "CI-07", "CI-13", "CI-14", "CI-21", "CI-23"),
        ownership_boundary=(
            "The common shelf catalogs `eslint` as a polyglot evidence source. "
            "ESLint config, plugin selection, and rule tuning remain downstream."
        ),
    ),
    AciAnalyzerCatalogEntry(
        analyzer_id="tsc",
        category="type-check",
        purpose="TypeScript compiler type checking for interface and contract drift",
        evidence_type="machine evidence",
        support_level="profile-default-catalog",
        referenced_by_profiles=(),
        typical_ci_ids=("CI-23",),
        ownership_boundary=(
            "The common shelf catalogs `tsc` for TypeScript type evidence. "
            "tsconfig.json, strict settings, and path scope remain downstream."
        ),
    ),
    AciAnalyzerCatalogEntry(
        analyzer_id="shellcheck",
        category="lint",
        purpose="shell script static analysis for unsafe patterns, error-handling gaps, and portability issues",
        evidence_type="machine evidence",
        support_level="profile-default-catalog",
        referenced_by_profiles=(),
        typical_ci_ids=("CI-02", "CI-21"),
        ownership_boundary=(
            "The common shelf catalogs `shellcheck` for shell script evidence. "
            "Target file scope and rule suppression remain downstream."
        ),
    ),
    AciAnalyzerCatalogEntry(
        analyzer_id="sqlfluff",
        category="lint",
        purpose="SQL style and structure linting for query quality",
        evidence_type="machine evidence",
        support_level="profile-default-catalog",
        referenced_by_profiles=(),
        typical_ci_ids=("CI-02",),
        ownership_boundary=(
            "The common shelf catalogs `sqlfluff` for SQL evidence. "
            "Dialect configuration and rule selection remain downstream."
        ),
    ),
)


def analyzer_support_levels() -> dict[str, str]:
    return dict(ANALYZER_SUPPORT_LEVELS)


def analyzer_catalog() -> list[dict[str, object]]:
    return [entry.as_dict() for entry in ANALYZER_CATALOG]
