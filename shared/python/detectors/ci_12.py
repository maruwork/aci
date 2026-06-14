"""CI-12 Poltergeist Class detector."""
from __future__ import annotations

import ast
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from ._helpers import _relative_path, _cached_parse
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from detectors._helpers import _relative_path, _cached_parse  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI12_POLTERGEIST"})


def _get_init_single_delegate(init_node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """If __init__ stores exactly one external arg as self.X, return attribute name; else None."""
    if len(init_node.args.args) != 2:
        return None
    real_body = [
        s for s in init_node.body
        if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
    ]
    if len(real_body) != 1 or not isinstance(real_body[0], ast.Assign):
        return None
    stmt = real_body[0]
    if len(stmt.targets) != 1:
        return None
    target = stmt.targets[0]
    if not (
        isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == "self"
    ):
        return None
    return target.attr


def _is_method_pure_delegation(
    method: ast.FunctionDef | ast.AsyncFunctionDef,
    delegate_attr: str,
) -> bool:
    real_body = [
        s for s in method.body
        if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
    ]
    if not real_body or len(real_body) > 2:
        return False
    for stmt in real_body:
        call = None
        if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
            call = stmt.value
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
        if call is None:
            return False
        if not (
            isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Attribute)
            and isinstance(call.func.value.value, ast.Name)
            and call.func.value.value.id == "self"
            and call.func.value.attr == delegate_attr
        ):
            return False
    return True


def scan(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = _cached_parse(text)
    except SyntaxError:
        return []
    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if node.bases:
            continue
        init = next(
            (m for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == "__init__"),
            None,
        )
        if init is None:
            continue
        delegate_attr = _get_init_single_delegate(init)
        if delegate_attr is None:
            continue
        public_methods = [
            m for m in node.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not m.name.startswith("__")
        ]
        if not public_methods or len(public_methods) > 3:
            continue
        if not all(_is_method_pure_delegation(m, delegate_attr) for m in public_methods):
            continue
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-12",
                signal="CI12_POLTERGEIST",
                severity="low",
                target_file=_relative_path(path, target_root),
                line=node.lineno,
                excerpt=f"class {node.name}",
                reason=(
                    f"Class '{node.name}' wraps a single dependency and delegates all "
                    f"{len(public_methods)} public method(s) without adding logic."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Remove the wrapper class and call the underlying object directly.",
                confidence=CONFIDENCE_MEDIUM,
                priority="P3",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
