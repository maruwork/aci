"""CI-02 Code Structure detectors (spaghetti code + long functions)."""
from __future__ import annotations

import ast
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM, CONFIDENCE_HIGH,
    )
    from ._helpers import _relative_path
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM, CONFIDENCE_HIGH,
    )
    from detectors._helpers import _relative_path  # type: ignore[no-redef]

SIGNALS_SPAGHETTI: frozenset[str] = frozenset({"CI02_SPAGHETTI_CODE"})
SIGNALS_LONG: frozenset[str] = frozenset({"CI02_LONG_FUNCTION"})

_NESTING_THRESHOLD = 4
_LONG_FUNCTION_THRESHOLD = 50


def _max_control_flow_depth(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    CONTROL_TYPES = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.AsyncWith)

    def _depth(node: ast.AST, d: int) -> int:
        if isinstance(node, CONTROL_TYPES):
            d += 1
        best = d
        if isinstance(node, ast.If):
            for stmt in node.body:
                best = max(best, _depth(stmt, d))
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                best = max(best, _depth(node.orelse[0], d - 1))
            else:
                for stmt in node.orelse:
                    best = max(best, _depth(stmt, d))
        else:
            for child in ast.iter_child_nodes(node):
                best = max(best, _depth(child, d))
        return best

    body_mod = ast.Module(body=func_node.body, type_ignores=[])
    return _depth(body_mod, 0)


def scan_spaghetti(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
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
        depth = _max_control_flow_depth(node)
        if depth < _NESTING_THRESHOLD:
            continue
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-02",
                signal="CI02_SPAGHETTI_CODE",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=node.lineno,
                excerpt=f"def {node.name}(...) [nesting depth {depth}]",
                reason=(
                    f"Function '{node.name}' has control-flow nesting depth {depth}; "
                    "tangled branching obscures state movement and makes the function hard to follow."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Extract inner blocks into named helper functions to flatten the control flow.",
                confidence=CONFIDENCE_MEDIUM,
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def scan_long_functions(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
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
        if not hasattr(node, "end_lineno") or node.end_lineno is None:
            continue
        body_lines = node.end_lineno - node.lineno
        if body_lines < _LONG_FUNCTION_THRESHOLD:
            continue
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-02",
                signal="CI02_LONG_FUNCTION",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=node.lineno,
                excerpt=f"def {node.name}(...)",
                reason=(
                    f"Function body spans {body_lines} lines, "
                    f"exceeding the {_LONG_FUNCTION_THRESHOLD}-line threshold."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Extract cohesive sub-operations into named helper functions.",
                confidence=CONFIDENCE_HIGH,
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
