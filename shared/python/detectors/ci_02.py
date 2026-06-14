"""CI-02 Code Structure detectors (spaghetti code + long functions)."""
from __future__ import annotations

import ast
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from ._helpers import _relative_path
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from detectors._helpers import _relative_path  # type: ignore[no-redef]

SIGNALS_SPAGHETTI: frozenset[str] = frozenset({"CI02_SPAGHETTI_CODE"})
SIGNALS_LONG: frozenset[str] = frozenset({"CI02_LONG_FUNCTION"})

# Spaghetti = deeply nested AND branch-complex. Deep nesting alone (a linear
# chain of ifs) or high branching alone (a flat dispatch) is not the smell;
# requiring both targets genuinely tangled control flow. Long-function size is
# measured in logical lines (code only) so documentation does not inflate it.
_NESTING_THRESHOLD = 5
_COMPLEXITY_THRESHOLD = 8  # McCabe cyclomatic complexity
_LONG_FUNCTION_THRESHOLD = 50


def _cyclomatic_complexity(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """McCabe cyclomatic complexity of the function body (decision points + 1).
    Nested function/class bodies are not descended into."""
    complexity = 1

    def _visit(node: ast.AST) -> None:
        nonlocal complexity
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue  # separate scope; not part of this function's complexity
            if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += len(child.ifs)
            elif type(child).__name__ == "match_case":
                complexity += 1
            _visit(child)

    for stmt in func_node.body:
        _visit(stmt)
    return complexity


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


def _logical_line_count(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef, source_lines: list[str]
) -> int:
    """Count code lines in the function body, excluding the docstring, blank
    lines, and comment-only lines. Returns 0 when the body is only a docstring."""
    body = func_node.body
    if not body:
        return 0
    first = body[0]
    is_docstring = (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    )
    statements = body[1:] if is_docstring else body
    if not statements:
        return 0
    start = statements[0].lineno
    end = func_node.end_lineno or start
    count = 0
    for i in range(start, end + 1):
        if i - 1 >= len(source_lines):
            break
        stripped = source_lines[i - 1].strip()
        if stripped and not stripped.startswith("#"):
            count += 1
    return count


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
        complexity = _cyclomatic_complexity(node)
        if complexity < _COMPLEXITY_THRESHOLD:
            continue  # deeply nested but not branch-complex — a linear chain, not spaghetti
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-02",
                signal="CI02_SPAGHETTI_CODE",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=node.lineno,
                excerpt=f"def {node.name}(...) [nesting {depth}, complexity {complexity}]",
                reason=(
                    f"Function '{node.name}' is tangled: nesting depth {depth} and cyclomatic "
                    f"complexity {complexity}. Deep nesting plus heavy branching obscures state movement."
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
    source_lines = text.splitlines()
    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not hasattr(node, "end_lineno") or node.end_lineno is None:
            continue
        body_lines = _logical_line_count(node, source_lines)
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
                    f"Function body contains {body_lines} code lines (excluding docstring/blank/comment), "
                    f"exceeding the {_LONG_FUNCTION_THRESHOLD}-line threshold."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Extract cohesive sub-operations into named helper functions.",
                # medium, not high: a long function is a design-review prompt, not
                # a confirmed defect (precision audit 2026-06-13).
                confidence=CONFIDENCE_MEDIUM,
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
