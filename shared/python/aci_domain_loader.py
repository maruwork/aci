#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal domain-pack loader for ACI.

This helper keeps domain selection explicit without coupling ACI core to one
domain. It returns bounded domain-rule objects only and prefers package-safe
imports when available.
"""
from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
import sys

try:
    from .aci_domain_contract import AciDomainRules, CORE_ONLY_DOMAIN_ID, EMPTY_DOMAIN_RULES
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_domain_contract import AciDomainRules, CORE_ONLY_DOMAIN_ID, EMPTY_DOMAIN_RULES


def _normalize_domain_rules(value: object) -> AciDomainRules | None:
    if value is None or not hasattr(value, "domain_id"):
        return None
    return AciDomainRules(
        domain_id=value.domain_id,
        state_plane_terms=tuple(getattr(value, "state_plane_terms", ())),
        state_sql_patterns=tuple(getattr(value, "state_sql_patterns", ())),
        risk_surfaces=tuple(getattr(value, "risk_surfaces", ())),
        authority_terms=tuple(getattr(value, "authority_terms", ())),
        safe_authority_context_terms=tuple(getattr(value, "safe_authority_context_terms", ())),
        side_program_terms=tuple(getattr(value, "side_program_terms", ())),
        excluded_files=tuple(getattr(value, "excluded_files", ())),
        excluded_prefixes=tuple(getattr(value, "excluded_prefixes", ())),
    )


def _load_rules_from_package(module_name: str, symbol: str) -> AciDomainRules | None:
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return None
    return _normalize_domain_rules(getattr(module, symbol, None))


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
    return _normalize_domain_rules(getattr(module, symbol, None))


def _discover_domain_file(domain_id: str) -> Path | None:
    aci_root = Path(__file__).resolve().parent.parent.parent
    candidate = aci_root / "domains" / domain_id / "python" / f"{domain_id}_domain_rules.py"
    return candidate if candidate.exists() else None


def load_domain_rules(domain_id: str | None, domain_file: Path | None = None) -> AciDomainRules:
    if not domain_id or domain_id == CORE_ONLY_DOMAIN_ID:
        return EMPTY_DOMAIN_RULES
    symbol = f"{domain_id.upper()}_DOMAIN_RULES"
    if domain_file is not None:
        rules = _load_rules_from_file(f"aci_{domain_id}_domain_rules", domain_file, symbol)
        if rules is None:
            raise ValueError(f"Domain pack file did not provide expected symbol: {domain_file}")
        return rules
    rules = _load_rules_from_package(f"aci.domains.{domain_id}.{domain_id}_domain_rules", symbol)
    if rules is not None:
        return rules
    discovered = _discover_domain_file(domain_id)
    if discovered is not None:
        rules = _load_rules_from_file(f"aci_{domain_id}_domain_rules", discovered, symbol)
        if rules is not None:
            return rules
    raise ValueError(f"Unknown ACI domain pack: {domain_id}")
