"""CI-26 State Mutation Leak (Race Hazard) detector."""
from __future__ import annotations

import ast
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_HIGH,
    )
    from ._helpers import _relative_path, _line_excerpt
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_HIGH,
    )
    from detectors._helpers import _relative_path, _line_excerpt  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI26_RACE_HAZARD"})


def scan(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body_mod = ast.Module(body=node.body, type_ignores=[])
        for child in ast.walk(body_mod):
            if not isinstance(child, ast.Global):
                continue
            for name in child.names:
                findings.append(
                    build_finding(
                        finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                        ci_id="CI-26",
                        signal="CI26_RACE_HAZARD",
                        severity="medium",
                        target_file=_relative_path(path, target_root),
                        line=child.lineno,
                        excerpt=_line_excerpt(text, child.lineno),
                        reason=(
                            f"Function '{node.name}' modifies module-level state '{name}' via "
                            "'global'; concurrent calls share this mutable state without explicit "
                            "synchronization."
                        ),
                        evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                        recommended_action=(
                            "Eliminate the global by passing state as a parameter, using a class, "
                            "or protecting with a threading.Lock / asyncio.Lock."
                        ),
                        confidence=CONFIDENCE_HIGH,
                        priority="P2",
                        owner_lane=LANE_NATIVE_STATIC,
                        verification_status=VERIFICATION_EXECUTED,
                    )
                )
    return findings
