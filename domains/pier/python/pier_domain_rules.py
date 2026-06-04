#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pier-specific ACI domain vocabulary.

This file exists so Pier investigation terms can be selected as a domain pack
instead of remaining embedded in domain-independent ACI core.
"""
from __future__ import annotations

import re

try:
    from ....python.aci_domain_contract import AciDomainRules
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_domain_contract import AciDomainRules

DOMAIN_ID = "pier"

STATE_PLANE_TERMS = (
    "effective_task_state",
    "pending_human_gate_queue",
    "governance_alerts",
)

STATE_SQL_PATTERNS = (
    re.compile(r"SELECT\s+status\s+FROM\s+event_ledger", re.IGNORECASE),
    re.compile(r"FROM\s+event_ledger.*latest", re.IGNORECASE),
)

SHELF_BREAK_TERMS = (
    "workspace/",
    "archive/",
    "scratch/",
)

RISK_SURFACES = (
    "{project_entry_readme}",
    "{project_workflow_doc}",
    "{project_docs_index}",
    "{project_current_task_register}",
    "{project_execution_order_file}",
)

AUTHORITY_TERMS = (
    "current task SSOT",
    "current canonical",
    "authority",
    "active branch",
    "executable branch",
    "mainline authority",
    "becomes the current mainline",
    "treated as authority/mainline",
    "current",
    "active",
    "canonical",
    "ssot",
    "mainline",
    "execution",
)

SAFE_AUTHORITY_CONTEXT_TERMS = (
    "example",
    "archive note",
    "scratch note",
    "historical",
    "non-authority",
)

SIDE_PROGRAM_TERMS = (
    "{project_side_program_primary}",
    "{project_side_program_secondary}",
    "{project_side_program_tertiary}",
)

EXCLUDED_FILES = (
    "{project_aci_core}",
    "{project_index_generator}",
    "{project_tools_classifier}",
)

EXCLUDED_PREFIXES = (
    "{project_test_shelf}/",
)

PIER_DOMAIN_RULES = AciDomainRules(
    domain_id=DOMAIN_ID,
    state_plane_terms=STATE_PLANE_TERMS,
    state_sql_patterns=STATE_SQL_PATTERNS,
    shelf_break_terms=SHELF_BREAK_TERMS,
    risk_surfaces=RISK_SURFACES,
    authority_terms=AUTHORITY_TERMS,
    safe_authority_context_terms=SAFE_AUTHORITY_CONTEXT_TERMS,
    side_program_terms=SIDE_PROGRAM_TERMS,
    excluded_files=EXCLUDED_FILES,
    excluded_prefixes=EXCLUDED_PREFIXES,
)
