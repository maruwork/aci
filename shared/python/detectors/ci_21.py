"""CI-21 Exception handling detectors (broad swallow + silent return)."""
from __future__ import annotations

import ast
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from ._helpers import _relative_path, _line_excerpt, _build_parent_map
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from detectors._helpers import _relative_path, _line_excerpt, _build_parent_map  # type: ignore[no-redef]

SIGNALS_BROAD: frozenset[str] = frozenset({"CI21_BROAD_EXCEPTION_SWALLOW"})
SIGNALS_SILENT: frozenset[str] = frozenset({"CI21_SILENT_EXCEPTION_RETURN"})


def _is_bounded_retry_handler(
    handler: ast.ExceptHandler,
    parent_map: dict[ast.AST, ast.AST],
) -> bool:
    """Return True when `except Exception: continue` is inside a loop (bounded retry)."""
    if len(handler.body) != 1 or not isinstance(handler.body[0], ast.Continue):
        return False
    current = parent_map.get(handler)
    while current is not None:
        if isinstance(current, (ast.For, ast.While, ast.AsyncFor)):
            return True
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            break
        current = parent_map.get(current)
    return False


def _is_silent_return_value(node: ast.expr | None) -> bool:
    if node is None:
        return True
    if isinstance(node, ast.Constant):
        return node.value in (None, False, 0, "", b"")
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return len(node.elts) == 0
    if isinstance(node, ast.Dict):
        return len(node.keys) == 0
    return False


def scan_broad(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() != ".py":
        return findings
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return findings
    parent_map = _build_parent_map(tree)
    for handler in ast.walk(tree):
        if not isinstance(handler, ast.ExceptHandler):
            continue
        if not isinstance(handler.type, ast.Name) or handler.type.id != "Exception":
            continue
        if handler.name is not None:
            continue
        if _is_bounded_retry_handler(handler, parent_map):
            continue
        line = handler.lineno
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-21",
                signal="CI21_BROAD_EXCEPTION_SWALLOW",
                severity="high",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason="A broad `except Exception:` handler can hide unexpected failures and blur the recovery contract.",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Narrow the exception type or add explicit failure routing that preserves the real error boundary.",
                confidence=CONFIDENCE_MEDIUM,
                priority="P1",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def scan_silent(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() != ".py":
        return findings
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return findings
    for handler in ast.walk(tree):
        if not isinstance(handler, ast.ExceptHandler):
            continue
        if handler.type is not None:
            if not (isinstance(handler.type, ast.Name) and handler.type.id == "Exception"):
                continue
        if len(handler.body) != 1:
            continue
        stmt = handler.body[0]
        if not isinstance(stmt, ast.Return) or not _is_silent_return_value(stmt.value):
            continue
        line = handler.lineno
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-21",
                signal="CI21_SILENT_EXCEPTION_RETURN",
                severity="high",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason="Exception handler returns a silent sentinel value instead of propagating or logging the failure.",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Raise the exception, re-raise with context, or return an explicit error type that callers are required to handle.",
                confidence=CONFIDENCE_MEDIUM,
                priority="P1",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
