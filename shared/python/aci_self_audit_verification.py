#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dedicated self-audit verification surface for ACI."""
from __future__ import annotations

from pathlib import Path
from typing import cast

try:
    from .aci_domain_contract import CORE_ONLY_DOMAIN_ID
    from .aci_ignore import load_ignore_patterns
    from .aci_profile_catalog import profile_catalog
    from .aci_profiles import PROFILE_SELF_AUDIT, default_scope_mode
    from .aci_scan import (
        SCOPE_CLASS_MAINTAINER_PROBES,
        SCOPE_CLASS_ROADMAP_EVIDENCE,
        SCOPE_CLASS_RUNTIME_SOURCE,
        SCOPE_MODE_SELF_AUDIT,
        _classify_relative_path,
        scan_target,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_domain_contract import CORE_ONLY_DOMAIN_ID
    from aci_ignore import load_ignore_patterns
    from aci_profile_catalog import profile_catalog
    from aci_profiles import PROFILE_SELF_AUDIT, default_scope_mode
    from aci_scan import (
        SCOPE_CLASS_MAINTAINER_PROBES,
        SCOPE_CLASS_ROADMAP_EVIDENCE,
        SCOPE_CLASS_RUNTIME_SOURCE,
        SCOPE_MODE_SELF_AUDIT,
        _classify_relative_path,
        scan_target,
    )


REQUIRED_IGNORE_PATTERNS: tuple[str, ...] = ("archive", "common", "workspace")
EXPECTED_CLASSIFICATIONS: tuple[tuple[str, str], ...] = (
    ("shared/python/aci_cli.py", SCOPE_CLASS_RUNTIME_SOURCE),
    ("shared/tools/aci_recall_probe.py", SCOPE_CLASS_MAINTAINER_PROBES),
    ("docs/roadmap/ACI_AUDIT_TOOL_COMPLETION_INVENTORY_2026-06-18.md", SCOPE_CLASS_ROADMAP_EVIDENCE),
)


def _existing_self_audit_include_paths(repo_root: Path) -> tuple[str, ...]:
    candidates = ("shared/python", "domains", "tests", "shared/tests", "shared/tools", "docs/roadmap")
    return tuple(candidate for candidate in candidates if (repo_root / candidate).exists())


def run_self_audit_check(repo_root: Path) -> dict[str, object]:
    expected_scope_mode = default_scope_mode(PROFILE_SELF_AUDIT) or SCOPE_MODE_SELF_AUDIT
    report = scan_target(
        repo_root,
        PROFILE_SELF_AUDIT,
        CORE_ONLY_DOMAIN_ID,
        include_external_analyzers=False,
        scope_mode=expected_scope_mode,
    )
    profile_ids = {entry["profile_id"] for entry in profile_catalog()}
    actual_ignore_patterns = set(load_ignore_patterns(repo_root))
    findings = cast("list[dict[str, object]]", report["findings"])
    scope_rules = cast("dict[str, object]", report["scope_rules"])
    summary = cast("dict[str, object]", report["summary"])
    review_brief = cast("dict[str, object]", report["review_brief"])
    visible_targets = {
        cast("str", item["target_file"])
        for item in findings
        if isinstance(item, dict) and isinstance(item.get("target_file"), str)
    }
    expected_include_paths = _existing_self_audit_include_paths(repo_root)

    checks: list[dict[str, object]] = [
        {
            "check": "self_audit.profile_registered",
            "ok": PROFILE_SELF_AUDIT in profile_ids,
            "expected": True,
            "actual": PROFILE_SELF_AUDIT in profile_ids,
        },
        {
            "check": "self_audit.default_scope_mode",
            "ok": scope_rules["scope_mode"] == expected_scope_mode,
            "expected": expected_scope_mode,
            "actual": scope_rules["scope_mode"],
        },
        {
            "check": "self_audit.include_paths",
            "ok": tuple(cast("list[str]", scope_rules["include_paths"])) == expected_include_paths,
            "expected": list(expected_include_paths),
            "actual": scope_rules["include_paths"],
        },
        {
            "check": "self_audit.gate_scope_classes",
            "ok": scope_rules["gate_scope_classes"] == [SCOPE_CLASS_RUNTIME_SOURCE],
            "expected": [SCOPE_CLASS_RUNTIME_SOURCE],
            "actual": scope_rules["gate_scope_classes"],
        },
        {
            "check": "self_audit.required_ignore_patterns",
            "ok": all(pattern in actual_ignore_patterns for pattern in REQUIRED_IGNORE_PATTERNS),
            "expected": list(REQUIRED_IGNORE_PATTERNS),
            "actual": sorted(actual_ignore_patterns),
        },
        {
            "check": "self_audit.no_touch_visible",
            "ok": not any(
                target == pattern or target.startswith(f"{pattern}/")
                for pattern in REQUIRED_IGNORE_PATTERNS
                for target in visible_targets
            ),
            "expected": True,
            "actual": any(
                target == pattern or target.startswith(f"{pattern}/")
                for pattern in REQUIRED_IGNORE_PATTERNS
                for target in visible_targets
            ),
        },
    ]

    for relative_path, expected_scope_class in EXPECTED_CLASSIFICATIONS:
        if not (repo_root / relative_path).exists():
            continue
        checks.append(
            {
                "check": f"classification.{relative_path}",
                "ok": _classify_relative_path(relative_path) == expected_scope_class,
                "expected": expected_scope_class,
                "actual": _classify_relative_path(relative_path),
            }
        )

    ok = all(item["ok"] for item in checks)
    return {
        "tool": "ACI",
        "command": "self-audit-check",
        "ok": ok,
        "profile_id": PROFILE_SELF_AUDIT,
        "checks": checks,
        "scope_rules": scope_rules,
        "summary": summary,
        "review_brief": review_brief,
    }
