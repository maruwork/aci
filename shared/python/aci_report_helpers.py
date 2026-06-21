#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared report-reading helpers for the emit/view surfaces.

These three helpers were copy-pasted, byte-identical, across the SARIF,
annotations, GitHub-summary, and report-view emitters. ACI's own CI-05
(copy-paste) detector flagged the duplication on a self-scan; this module is the
shared abstraction it asked for. Each emitter imports these (aliased to its
former private names) instead of redefining them.
"""
from __future__ import annotations

from typing import cast

try:
    from .aci_scan import SCOPE_CLASS_RUNTIME_SOURCE, _classify_relative_path
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_scan import SCOPE_CLASS_RUNTIME_SOURCE, _classify_relative_path  # type: ignore[no-redef]


def report_map(value: object) -> dict[str, object]:
    """Coerce an arbitrary report value to a dict, or {} if it is not one."""
    return cast(dict[str, object], value) if isinstance(value, dict) else {}


def gate_scope_classes(report: dict[str, object]) -> tuple[str, ...]:
    """The report's gate scope classes, defaulting to runtime-source."""
    scope_rules = report_map(report.get("scope_rules"))
    raw = scope_rules.get("gate_scope_classes")
    if not isinstance(raw, list) or not raw:
        return (SCOPE_CLASS_RUNTIME_SOURCE,)
    values = tuple(str(item) for item in raw if isinstance(item, str) and item)
    return values or (SCOPE_CLASS_RUNTIME_SOURCE,)


def scope_class(finding: dict[str, object]) -> str:
    """A finding's explicit scope_class, else one derived from its target file."""
    explicit = finding.get("scope_class")
    if isinstance(explicit, str) and explicit:
        return explicit
    return _classify_relative_path(str(finding.get("target_file") or ""))
