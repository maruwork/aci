#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-command public smoke check for the common ACI shelf."""
from __future__ import annotations

import json
from pathlib import Path

try:
    from .aci_domain_loader import load_domain_rules
    from .aci_findings import build_structure_finding
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_domain_loader import load_domain_rules
    from aci_findings import build_structure_finding


def build_public_smoke_result(repo_root: Path) -> dict[str, object]:
    core = load_domain_rules(None)
    try:
        pier = load_domain_rules("pier")
        pier_domain_id: str | None = pier.domain_id
    except (ValueError, ImportError):
        pier_domain_id = None
    finding = build_structure_finding(
        finding_id="F-SMOKE-001",
        signal="RESPONSIBILITY_SPROUT",
        severity="medium",
        target_file="shared/report/examples/aci-core-sample-report.md",
        line=1,
        reason="public smoke check",
        evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
    )
    mode_checks: dict[str, object] = {"core_only_domain": core.domain_id}
    if pier_domain_id is not None:
        mode_checks["pier_domain"] = pier_domain_id
    return {
        "tool": "ACI",
        "ok": True,
        "repository_layout": "standalone",
        "mode_checks": mode_checks,
        "finding_sample": finding.as_dict(),
        "layout_note": (
            "working mirror validation is monorepo-only and is intentionally skipped "
            "for standalone repository smoke checks"
        ),
    }


def detect_repo_root(script_path: Path) -> Path:
    aci_root = Path(__file__).resolve().parent.parent.parent
    if (aci_root / "shared" / "python" / "aci_domain_contract.py").exists():
        return aci_root
    resolved = script_path.resolve()
    for ancestor in resolved.parents:
        if (ancestor / "shared/python/aci_public_smoke.py").exists() and (ancestor / "README.md").exists():
            return ancestor
        if (
            ancestor.name != "python"
            and (ancestor / "aci_public_smoke.py").exists()
            and (ancestor / "aci_cli.py").exists()
        ):
            return ancestor
    for ancestor in resolved.parents:
        if (ancestor / "shared/python/aci_public_smoke.py").exists():
            return ancestor
    return resolved.parents[1]


def main() -> int:
    cwd = Path.cwd()
    if (cwd / "shared/python/aci_public_smoke.py").exists() and (cwd / "README.md").exists():
        repo_root = cwd
    else:
        repo_root = detect_repo_root(Path(__file__))
    print(json.dumps(build_public_smoke_result(repo_root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
