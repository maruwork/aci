#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Common domain-pack contract for ACI.

Domain packs provide investigation vocabulary and bounded rule inputs that are
selected alongside ACI core. They must not contain project-local absolute
paths, runtime schedules, or persistence backend implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class AciDomainRules:
    domain_id: str
    state_plane_terms: tuple[str, ...] = ()
    state_sql_patterns: tuple[re.Pattern[str], ...] = ()
    shelf_break_terms: tuple[str, ...] = ()
    risk_surfaces: tuple[str, ...] = ()
    authority_terms: tuple[str, ...] = ()
    safe_authority_context_terms: tuple[str, ...] = ()
    side_program_terms: tuple[str, ...] = ()
    excluded_files: tuple[str, ...] = ()
    excluded_prefixes: tuple[str, ...] = ()


EMPTY_DOMAIN_RULES = AciDomainRules(domain_id="core-only")
