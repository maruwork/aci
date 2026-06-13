"""CI-22 Resource Lifecycle Leak detector."""
from __future__ import annotations

import ast
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_LOW,
    )
    from ._helpers import _relative_path, _line_excerpt
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_LOW,
    )
    from detectors._helpers import _relative_path, _line_excerpt  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI22_RESOURCE_CLEANUP_GAP"})

_RESOURCE_OPENER_NAMES: frozenset[str] = frozenset({
    "open",
    "Popen",
    "NamedTemporaryFile",
    "TemporaryFile",
    "SpooledTemporaryFile",
})


def scan(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    with_wrapped: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                with_wrapped.add(id(item.context_expr))
                if isinstance(item.context_expr, ast.Call):
                    for arg in item.context_expr.args:
                        with_wrapped.add(id(arg))

    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if id(node) in with_wrapped:
            continue
        if isinstance(node.func, ast.Name):
            fname = node.func.id
        elif isinstance(node.func, ast.Attribute):
            fname = node.func.attr
        else:
            continue
        if fname not in _RESOURCE_OPENER_NAMES:
            continue
        line = node.lineno
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-22",
                signal="CI22_RESOURCE_CLEANUP_GAP",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason=(
                    f"'{fname}' opens a resource without a context manager; "
                    "the lifecycle may not be closed on exception paths."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action=(
                    "Wrap resource-opening calls in a 'with' statement to ensure "
                    "deterministic cleanup."
                ),
                # low confidence: precision audit (2026-06-13) found most matches
                # are managed via wrappers/context managers or exit paths — the
                # "no with-statement" heuristic cannot see that without dataflow.
                confidence=CONFIDENCE_LOW,
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
