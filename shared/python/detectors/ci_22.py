"""CI-22 Resource Lifecycle Leak detector."""
from __future__ import annotations

import ast
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from ._helpers import _relative_path, _line_excerpt, _build_parent_map, _cached_parse
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from detectors._helpers import _relative_path, _line_excerpt, _build_parent_map, _cached_parse  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI22_RESOURCE_CLEANUP_GAP"})

_RESOURCE_OPENER_NAMES: frozenset[str] = frozenset({
    "open",
    "Popen",
    "NamedTemporaryFile",
    "TemporaryFile",
    "SpooledTemporaryFile",
})


def _enclosing_function(node: ast.AST, parent_map: dict[ast.AST, ast.AST]) -> ast.AST | None:
    cur = parent_map.get(node)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur
        cur = parent_map.get(cur)
    return None


def _name_is_managed(func: ast.AST, varname: str) -> bool:
    """True when a handle bound to `varname` is returned, closed, stored on the
    instance, used in a `with`, or handed to another call (a wrapper that takes
    ownership) anywhere in the function."""
    for n in ast.walk(func):
        if isinstance(n, ast.Return):
            v = n.value
            if isinstance(v, ast.Name) and v.id == varname:
                return True
            if isinstance(v, (ast.Tuple, ast.List)) and any(isinstance(e, ast.Name) and e.id == varname for e in v.elts):
                return True
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == varname and n.func.attr in {"close", "__exit__"}:
                return True
            if any(isinstance(a, ast.Name) and a.id == varname for a in n.args):
                return True
            if any(isinstance(kw.value, ast.Name) and kw.value.id == varname for kw in n.keywords):
                return True
        if isinstance(n, (ast.With, ast.AsyncWith)):
            for item in n.items:
                if isinstance(item.context_expr, ast.Name) and item.context_expr.id == varname:
                    return True
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Name) and n.value.id == varname:
            if any(isinstance(t, ast.Attribute) for t in n.targets):
                return True
    return False


def _is_managed_open(call_node: ast.Call, parent_map: dict[ast.AST, ast.AST]) -> bool:
    """Approximate dataflow: is the opened handle's lifecycle managed?"""
    parent = parent_map.get(call_node)
    if isinstance(parent, ast.Return):
        return True  # returned to the caller, which owns cleanup
    if isinstance(parent, ast.Call):
        return True  # passed into a wrapper that takes ownership
    if isinstance(parent, ast.withitem):
        return True
    if isinstance(parent, ast.Assign):
        for target in parent.targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                return True  # stored on the instance, closed elsewhere
            if isinstance(target, ast.Name):
                func = _enclosing_function(call_node, parent_map)
                if func is not None and _name_is_managed(func, target.id):
                    return True
    return False


def scan(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = _cached_parse(text)
    except SyntaxError:
        return []

    parent_map = _build_parent_map(tree)
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
        if _is_managed_open(node, parent_map):
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
                # medium: now dataflow-aware — handles that are returned, stored
                # on self, closed, used in `with`, or handed to a wrapper are
                # excluded, so a reported handle is genuinely unmanaged.
                confidence=CONFIDENCE_MEDIUM,
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
