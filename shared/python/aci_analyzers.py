#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded external-analyzer catalog for the common ACI shelf."""
from __future__ import annotations

from dataclasses import asdict, dataclass

try:
    from .aci_profiles import (
        PROFILE_QUICK_GATE, PROFILE_FULL, PROFILE_SELF_AUDIT, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_profiles import (
        PROFILE_QUICK_GATE, PROFILE_FULL, PROFILE_SELF_AUDIT, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW,
    )


ANALYZER_SUPPORT_LEVELS: dict[str, str] = {
    "profile-default": (
        "This analyzer is part of the bounded default external-analyzer set for one or more ACI profiles. "
        "The common shelf owns the catalog claim and profile-default policy only; installation and local tuning "
        "still depend on the environment."
    ),
    "opt-in": (
        "This analyzer is cataloged by the common shelf, but it stays opt-in and is never auto-selected by the "
        "bounded profile defaults. Downstream projects must decide whether and how to enable it."
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
        analyzer_id="semgrep",
        category="static-analysis",
        purpose="polyglot semantic rule matching and taint-style security evidence across common source languages",
        evidence_type="machine evidence",
        support_level="profile-default",
        referenced_by_profiles=(PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_FULL, PROFILE_SELF_AUDIT),
        typical_ci_ids=("CI-14", "CI-21", "CI-22", "CI-23", "CI-26"),
        ownership_boundary=(
            "The common shelf ships a bounded baseline Semgrep rule pack and normalizes its JSON output. "
            "Repository-local rule packs and stricter policies remain downstream."
        ),
    ),
    AciAnalyzerCatalogEntry(
        analyzer_id="codeql",
        category="static-analysis",
        purpose="deep semantic and dataflow evidence when a repository-local CodeQL database and query pack exist",
        evidence_type="machine evidence",
        support_level="opt-in",
        referenced_by_profiles=(),
        typical_ci_ids=("CI-14", "CI-21", "CI-22", "CI-23", "CI-26"),
        ownership_boundary=(
            "The common shelf catalogs CodeQL and can report readiness, but CodeQL database creation, query pack "
            "selection, and repo-specific tuning remain downstream."
        ),
    ),
    AciAnalyzerCatalogEntry(
        analyzer_id="gitleaks",
        category="secret-scan",
        purpose="repository secret and credential leakage detection",
        evidence_type="machine evidence",
        support_level="opt-in",
        referenced_by_profiles=(),
        typical_ci_ids=("CI-14",),
        ownership_boundary=(
            "The common shelf catalogs gitleaks as an optional secret-scanning evidence lane. "
            "Rule tuning, allowlists, and enforcement policy remain downstream."
        ),
    ),
    AciAnalyzerCatalogEntry(
        analyzer_id="osv-scanner",
        category="dependency-audit",
        purpose="dependency vulnerability evidence from lockfiles and manifests",
        evidence_type="machine evidence",
        support_level="opt-in",
        referenced_by_profiles=(),
        typical_ci_ids=("CI-14", "CI-23"),
        ownership_boundary=(
            "The common shelf catalogs OSV-Scanner as an optional dependency audit lane. "
            "Manifest scope, advisory policy, and remediation workflow remain downstream."
        ),
    ),
    AciAnalyzerCatalogEntry(
        analyzer_id="trivy",
        category="dependency-and-image-audit",
        purpose="dependency, container image, and IaC vulnerability evidence",
        evidence_type="machine evidence",
        support_level="opt-in",
        referenced_by_profiles=(),
        typical_ci_ids=("CI-14",),
        ownership_boundary=(
            "The common shelf catalogs Trivy as an optional security evidence lane. "
            "Target selection, policy thresholds, and CI gating remain downstream."
        ),
    ),
    AciAnalyzerCatalogEntry(
        analyzer_id="ruff",
        category="lint",
        purpose="fast lint and rule-based static evidence for code hygiene and contract drift",
        evidence_type="machine evidence",
        support_level="profile-default",
        referenced_by_profiles=(PROFILE_QUICK_GATE, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_FULL, PROFILE_SELF_AUDIT),
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
        support_level="profile-default",
        referenced_by_profiles=(PROFILE_QUICK_GATE, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_FULL, PROFILE_SELF_AUDIT),
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
        support_level="profile-default",
        referenced_by_profiles=(PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_FULL, PROFILE_SELF_AUDIT),
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
        support_level="profile-default",
        referenced_by_profiles=(PROFILE_BUILD_REVIEW, PROFILE_FULL, PROFILE_SELF_AUDIT),
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
        support_level="profile-default",
        referenced_by_profiles=(PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_FULL, PROFILE_SELF_AUDIT),
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
        support_level="profile-default",
        referenced_by_profiles=(PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_FULL, PROFILE_SELF_AUDIT),
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
        support_level="profile-default",
        referenced_by_profiles=(PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_FULL, PROFILE_SELF_AUDIT),
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
        support_level="profile-default",
        referenced_by_profiles=(PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_FULL, PROFILE_SELF_AUDIT),
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
