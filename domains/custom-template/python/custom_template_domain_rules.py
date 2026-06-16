#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Template ACI domain rules file.

Copy this file to domains/<domain>/python/<domain>_domain_rules.py and replace
all REPLACE_ME placeholders with domain-specific values before use.

See docs/DOMAIN_PACK_EXTENSION_GUIDE.md for the full field reference.
"""
from __future__ import annotations

import re

try:
    from aci_domain_contract import AciDomainRules
except ImportError:
    from aci.aci_domain_contract import AciDomainRules

DOMAIN_ID = "REPLACE_ME"  # e.g. "my-domain"

STATE_PLANE_TERMS: tuple[str, ...] = (
    # Terms that appear in state-plane files; used by SIDE_PROGRAM_LEAK detection.
    # e.g. "task_status", "pending_queue"
)

STATE_SQL_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Compiled regex patterns matching SQL queries that read from the state plane.
    # e.g. re.compile(r"SELECT\s+status\s+FROM\s+tasks", re.IGNORECASE)
)

RISK_SURFACES: tuple[str, ...] = (
    # File paths (repo-relative) that are high-risk authority surfaces.
    # e.g. "docs/current-state.md", "ops/task-register.md"
)

AUTHORITY_TERMS: tuple[str, ...] = (
    # Terms that indicate a file claims canonical authority.
    # e.g. "current canonical", "ssot", "authority"
)

SAFE_AUTHORITY_CONTEXT_TERMS: tuple[str, ...] = (
    # Terms that make an authority-term occurrence safe (e.g. in a comment or heading).
    # e.g. "historical", "archived"
)

SIDE_PROGRAM_TERMS: tuple[str, ...] = (
    # Names of side-programs / external services that should not appear in core code.
    # e.g. "my-side-service", "legacy-tool"
)

EXCLUDED_FILES: tuple[str, ...] = (
    # Exact repo-relative file paths to exclude from domain detection.
    # e.g. "domains/my-domain/python/my_domain_domain_rules.py"
)

EXCLUDED_PREFIXES: tuple[str, ...] = (
    # Path prefixes to exclude from domain detection.
    # e.g. "docs/", "archive/"
)

REPLACE_ME_DOMAIN_RULES = AciDomainRules(
    domain_id=DOMAIN_ID,
    state_plane_terms=STATE_PLANE_TERMS,
    state_sql_patterns=STATE_SQL_PATTERNS,
    risk_surfaces=RISK_SURFACES,
    authority_terms=AUTHORITY_TERMS,
    safe_authority_context_terms=SAFE_AUTHORITY_CONTEXT_TERMS,
    side_program_terms=SIDE_PROGRAM_TERMS,
    excluded_files=EXCLUDED_FILES,
    excluded_prefixes=EXCLUDED_PREFIXES,
)
