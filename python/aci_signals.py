#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ACI core structure signal catalog and project-replaced boundary constants.

Type: helper
When: a project runtime copy composes signal/profile behavior
Writes: none

This common authority file keeps only domain-independent rule core and
project-replaced boundary points. Domain-specific investigation vocabulary
belongs in a selected domain pack, not in this file.
"""
from __future__ import annotations

import re

STRUCTURE_SIGNALS = (
    "RESPONSIBILITY_SPROUT",
    "SIDE_PROGRAM_LEAK",
    "SHELF_BOUNDARY_BREAK",
    "OPERATOR_VIEW_GAP",
    "PATCHWORK_GRAFT",
)

EXTERNAL_SIGNAL_ALIASES = {
    "RESPONSIBILITYSPROUT": "RESPONSIBILITY_SPROUT",
    "SIDEPROGRAMLEAK": "SIDE_PROGRAM_LEAK",
    "SHELFBOUNDARYBREAK": "SHELF_BOUNDARY_BREAK",
    "OPERATORVIEWGAP": "OPERATOR_VIEW_GAP",
    "PATCHWORKGRAFT": "PATCHWORK_GRAFT",
}


def compile_keyword_pattern(*terms: str) -> re.Pattern[str]:
    escaped_terms = tuple(
        re.escape(term.strip())
        for term in terms
        if term.strip() and "{" not in term and "}" not in term
    )
    if not escaped_terms:
        return re.compile(r"(?!)")
    return re.compile(r"\b(" + "|".join(escaped_terms) + r")\b", re.IGNORECASE)

STATE_PLANE_TERMS: tuple[str, ...] = ()

STATE_SQL_PATTERNS: tuple[re.Pattern[str], ...] = ()

LOW_INFO_SCATTERED_LITERALS: frozenset[str] = frozenset(
    {
        "--env-file",
        "--refetch",
        "--verdicts",
        "__main__",
        "archive.db",
        "bookmark_intake.json",
        "created_at",
        "db/archive.db",
        "db/control.db",
        "db/knowledge.db",
        "domcontentloaded",
        "keep,hold",
        "next_step",
        "overview",
        "store_true",
        "translations",
        "updated_at",
        "User-Agent",
    }
)

LOW_INFO_SCATTERED_LITERAL_SUFFIXES = ("-zh-overview.md",)

SIDE_PROGRAM_TERMS: tuple[str, ...] = ()
AUTHORITY_TERMS: tuple[str, ...] = ()
SAFE_AUTHORITY_CONTEXT_TERMS: tuple[str, ...] = ()
SHELF_BREAK_TERMS: tuple[str, ...] = ()

SIDE_PROGRAM_PATTERN = compile_keyword_pattern(*SIDE_PROGRAM_TERMS)
DANGEROUS_SIDE_PROGRAM_PATTERN = compile_keyword_pattern(*AUTHORITY_TERMS)
SAFE_SIDE_PROGRAM_PATTERN = re.compile(
    r"(side program|reference-only|support-only|bounded trial)",
    re.IGNORECASE,
)
SHELF_BREAK_PATTERN = compile_keyword_pattern(*SHELF_BREAK_TERMS)
CURRENT_AUTHORITY_PATTERN = compile_keyword_pattern(*AUTHORITY_TERMS)
SAFE_SHELF_CONTEXT_PATTERN = compile_keyword_pattern(*SAFE_AUTHORITY_CONTEXT_TERMS)
