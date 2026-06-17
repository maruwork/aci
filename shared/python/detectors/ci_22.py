"""CI-22 Resource Lifecycle Leak detector."""
from __future__ import annotations

import ast
from dataclasses import dataclass
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


@dataclass(frozen=True)
class _ResourceFindingContext:
    path: Path
    text: str
    target_root: Path
    next_id: int


def _enclosing_function(node: ast.AST, parent_map: dict[ast.AST, ast.AST]) -> ast.AST | None:
    cur = parent_map.get(node)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur
        cur = parent_map.get(cur)
    return None


def _name_is_managed(func: ast.AST, varname: str) -> bool:
    """True when a handle bound to `varname` is returned, closed, stored on the
    instance, used in a `with`, or handed to another call that takes ownership."""
    for node in ast.walk(func):
        if isinstance(node, ast.Return):
            value = node.value
            if isinstance(value, ast.Name) and value.id == varname:
                return True
            if isinstance(value, (ast.Tuple, ast.List)):
                if any(isinstance(item, ast.Name) and item.id == varname for item in value.elts):
                    return True
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == varname
                and node.func.attr in {"close", "__exit__"}
            ):
                return True
            if any(isinstance(arg, ast.Name) and arg.id == varname for arg in node.args):
                return True
            if any(isinstance(kw.value, ast.Name) and kw.value.id == varname for kw in node.keywords):
                return True
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if isinstance(item.context_expr, ast.Name) and item.context_expr.id == varname:
                    return True
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name) and node.value.id == varname:
            if any(isinstance(target, ast.Attribute) for target in node.targets):
                return True
    return False


def _is_managed_open(call_node: ast.Call, parent_map: dict[ast.AST, ast.AST]) -> bool:
    """Approximate dataflow: is the opened handle's lifecycle managed?"""
    parent = parent_map.get(call_node)
    if isinstance(parent, (ast.Return, ast.Call, ast.Lambda, ast.withitem)):
        return True
    if not isinstance(parent, ast.Assign):
        return False
    for target in parent.targets:
        if isinstance(target, ast.Attribute):
            return True
        if isinstance(target, ast.Name):
            func = _enclosing_function(call_node, parent_map)
            if func is not None and _name_is_managed(func, target.id):
                return True
    return False


def _with_wrapped_nodes(tree: ast.AST) -> set[int]:
    wrapped: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.With, ast.AsyncWith)):
            continue
        for item in node.items:
            wrapped.add(id(item.context_expr))
            if isinstance(item.context_expr, ast.Call):
                for arg in item.context_expr.args:
                    wrapped.add(id(arg))
    return wrapped


def _opened_resource_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _is_fire_and_forget_task(node: ast.AST) -> bool:
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return False
    call = node.value
    if isinstance(call.func, ast.Attribute):
        if call.func.attr != "create_task":
            return False
        if isinstance(call.func.value, ast.Name) and call.func.value.id == "asyncio":
            return True
        return True
    return False


def _build_resource_finding(
    context: _ResourceFindingContext,
    finding_index: int,
    line: int,
    fname: str,
) -> AciFinding:
    return build_finding(
        finding_id=f"F-SCAN-{context.next_id + finding_index:04d}",
        ci_id="CI-22",
        signal="CI22_RESOURCE_CLEANUP_GAP",
        severity="medium",
        target_file=_relative_path(context.path, context.target_root),
        line=line,
        excerpt=_line_excerpt(context.text, line),
        reason=(
            f"'{fname}' opens a resource without a context manager; "
            "the lifecycle may not be closed on exception paths."
        ),
        evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
        recommended_action=(
            "Wrap resource-opening calls in a 'with' statement to ensure "
            "deterministic cleanup."
        ),
        confidence=CONFIDENCE_MEDIUM,
        priority="P2",
        owner_lane=LANE_NATIVE_STATIC,
        verification_status=VERIFICATION_EXECUTED,
    )


def _build_task_finding(context: _ResourceFindingContext, finding_index: int, line: int) -> AciFinding:
    return build_finding(
        finding_id=f"F-SCAN-{context.next_id + finding_index:04d}",
        ci_id="CI-22",
        signal="CI22_FIRE_AND_FORGET_TASK",
        severity="medium",
        target_file=_relative_path(context.path, context.target_root),
        line=line,
        excerpt=_line_excerpt(context.text, line),
        reason="asyncio.create_task is launched without retaining or awaiting the task, so failures can escape the owning boundary.",
        evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
        recommended_action="Retain the task handle and await, cancel, or explicitly supervise it at the owning boundary.",
        confidence=CONFIDENCE_MEDIUM,
        priority="P2",
        owner_lane=LANE_NATIVE_STATIC,
        verification_status=VERIFICATION_EXECUTED,
    )


def scan(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = _cached_parse(text)
    except SyntaxError:
        return []

    parent_map = _build_parent_map(tree)
    with_wrapped = _with_wrapped_nodes(tree)
    context = _ResourceFindingContext(path=path, text=text, target_root=target_root, next_id=next_id)
    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if _is_fire_and_forget_task(node):
            findings.append(_build_task_finding(context, len(findings), getattr(node, "lineno", 1)))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if id(node) in with_wrapped:
            continue
        fname = _opened_resource_name(node)
        if fname is None or fname not in _RESOURCE_OPENER_NAMES:
            continue
        if _is_managed_open(node, parent_map):
            continue
        findings.append(_build_resource_finding(context, len(findings), node.lineno, fname))
    return findings
