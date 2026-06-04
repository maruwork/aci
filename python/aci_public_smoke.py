#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-command public smoke check for the common ACI shelf."""
from __future__ import annotations

import json
from pathlib import Path

try:
    from .aci_domain_loader import load_domain_rules
    from .aci_findings import build_structure_finding
    from .aci_working_mirror_sync import check_required_mirror_pairs
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_domain_loader import load_domain_rules
    from aci_findings import build_structure_finding
    from aci_working_mirror_sync import check_required_mirror_pairs


def build_public_smoke_result(repo_root: Path) -> dict[str, object]:
    core = load_domain_rules(None)
    pier = load_domain_rules("pier")
    finding = build_structure_finding(
        finding_id="F-SMOKE-001",
        signal="PATCHWORK_GRAFT",
        severity="medium",
        target_file="report/examples/aci-core-sample-report.md",
        line=1,
        reason="public smoke check",
        evidence_ref="core/aci-code-inspection-execution-spec.md",
    )
    mirror = check_required_mirror_pairs(repo_root)
    return {
        "tool": "ACI",
        "mode_checks": {
            "core_only_domain": core.domain_id,
            "pier_domain": pier.domain_id,
        },
        "finding_sample": finding.as_dict(),
        "mirror_sync": mirror.as_dict(),
    }


def detect_repo_root(script_path: Path) -> Path:
    resolved = script_path.resolve()
    for ancestor in resolved.parents:
        if (ancestor / "python/aci_public_smoke.py").exists() and (ancestor / "README.md").exists():
            if ancestor.name == "aci" and ancestor.parent.name == "common":
                return ancestor.parent.parent
            return ancestor
    for ancestor in resolved.parents:
        if (ancestor / "common/aci/python/aci_public_smoke.py").exists():
            return ancestor
    return resolved.parents[1]


def main() -> int:
    cwd = Path.cwd()
    if (cwd / "python/aci_public_smoke.py").exists() and (cwd / "README.md").exists():
        repo_root = cwd
    else:
        repo_root = detect_repo_root(Path(__file__))
    print(json.dumps(build_public_smoke_result(repo_root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
