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

SIGNAL_RESPONSIBILITY_SPROUT = "RESPONSIBILITY_SPROUT"
SIGNAL_SIDE_PROGRAM_LEAK = "SIDE_PROGRAM_LEAK"
SIGNAL_OPERATOR_VIEW_GAP = "OPERATOR_VIEW_GAP"
SIGNAL_STATE_DUPLICATION = "STATE_DUPLICATION"

STRUCTURE_SIGNALS = (
    SIGNAL_RESPONSIBILITY_SPROUT,
    SIGNAL_SIDE_PROGRAM_LEAK,
    SIGNAL_OPERATOR_VIEW_GAP,
    SIGNAL_STATE_DUPLICATION,
)

EXTERNAL_SIGNAL_ALIASES = {
    "RESPONSIBILITYSPROUT": SIGNAL_RESPONSIBILITY_SPROUT,
    "SIDEPROGRAMLEAK": SIGNAL_SIDE_PROGRAM_LEAK,
    "OPERATORVIEWGAP": SIGNAL_OPERATOR_VIEW_GAP,
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

LOW_INFO_SCATTERED_LITERALS: frozenset[str] = frozenset()

LOW_INFO_SCATTERED_LITERAL_SUFFIXES = ("-zh-overview.md",)

SIDE_PROGRAM_TERMS: tuple[str, ...] = ()
AUTHORITY_TERMS: tuple[str, ...] = ()

SIDE_PROGRAM_PATTERN = compile_keyword_pattern(*SIDE_PROGRAM_TERMS)
DANGEROUS_SIDE_PROGRAM_PATTERN = compile_keyword_pattern(*AUTHORITY_TERMS)
SAFE_SIDE_PROGRAM_PATTERN = re.compile(
    r"(side program|reference-only|support-only|bounded trial)",
    re.IGNORECASE,
)
