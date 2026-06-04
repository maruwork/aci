#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal domain-pack loader for ACI.

This helper keeps domain selection explicit without coupling ACI core to one
domain. It returns bounded domain-rule objects only.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

try:
    from .aci_domain_contract import AciDomainRules, EMPTY_DOMAIN_RULES
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_domain_contract import AciDomainRules, EMPTY_DOMAIN_RULES

_PIER_RULES_FILE = (
    Path(__file__).resolve().parent.parent
    / "domains"
    / "pier"
    / "python"
    / "pier_domain_rules.py"
)


def _load_rules_from_file(module_name: str, file_path: Path, symbol: str) -> AciDomainRules | None:
    if not file_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    python_shelf = str(Path(__file__).resolve().parent)
    added_path = False
    if python_shelf not in sys.path:
        sys.path.insert(0, python_shelf)
        added_path = True
    try:
        spec.loader.exec_module(module)
    finally:
        if added_path:
            try:
                sys.path.remove(python_shelf)
            except ValueError:  # pragma: no cover - path already removed elsewhere
                pass
    value = getattr(module, symbol, None)
    if value is None or not hasattr(value, "domain_id"):
        return None
    return AciDomainRules(
        domain_id=value.domain_id,
        state_plane_terms=tuple(getattr(value, "state_plane_terms", ())),
        state_sql_patterns=tuple(getattr(value, "state_sql_patterns", ())),
        shelf_break_terms=tuple(getattr(value, "shelf_break_terms", ())),
        risk_surfaces=tuple(getattr(value, "risk_surfaces", ())),
        authority_terms=tuple(getattr(value, "authority_terms", ())),
        safe_authority_context_terms=tuple(getattr(value, "safe_authority_context_terms", ())),
        side_program_terms=tuple(getattr(value, "side_program_terms", ())),
        excluded_files=tuple(getattr(value, "excluded_files", ())),
        excluded_prefixes=tuple(getattr(value, "excluded_prefixes", ())),
    )


PIER_DOMAIN_RULES = _load_rules_from_file(
    "aci_pier_domain_rules",
    _PIER_RULES_FILE,
    "PIER_DOMAIN_RULES",
)


def load_domain_rules(domain_id: str | None) -> AciDomainRules:
    if not domain_id or domain_id == "core-only":
        return EMPTY_DOMAIN_RULES
    if domain_id == "pier":
        if PIER_DOMAIN_RULES is None:
            raise RuntimeError("Pier domain pack is not importable in this runtime path")
        return PIER_DOMAIN_RULES
    raise ValueError(f"Unknown ACI domain pack: {domain_id}")
