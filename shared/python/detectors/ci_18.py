"""CI-18 Parameter Cluster detector."""
from __future__ import annotations

import ast
import re
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from ._helpers import _relative_path, _build_parent_map
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from detectors._helpers import _relative_path, _build_parent_map  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI18_PARAMETER_CLUSTER"})

_BOUNDARY_INTERFACE_NAME_PATTERN = re.compile(
    r"^(?:_)?(check|record|emit|notify|validate|reset|release|acquire|load|resolve|approve|insert)_"
)
_NON_BLOCKING_HINT_PATTERN = re.compile(r"(non-blocking|非ブロッキング|best-effort)", re.IGNORECASE)
_LOGGING_HELPER_NAME_PATTERN = re.compile(r"^(log|record|emit)_[a-z0-9_]+$")


def _get_node_docstring(node: ast.AST) -> str | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
        return ast.get_docstring(node)
    return None


def _get_ancestor_docstring(
    node: ast.AST,
    parent_map: dict[ast.AST, ast.AST],
    target_type: type,
) -> str | None:
    current = parent_map.get(node)
    while current is not None:
        if isinstance(current, target_type):
            return _get_node_docstring(current)
        current = parent_map.get(current)
    return None


def _is_boundary_interface_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    if not _BOUNDARY_INTERFACE_NAME_PATTERN.match(node.name):
        return False
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    if not body or len(body) > 30:
        return False
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name) and func.id in {
                "_emit", "_notify", "_release_task_lock", "_acquire_task_lock",
                "_record_transition", "_record_violation", "check_and_record", "queue_notification",
            }:
                return True
            if isinstance(func, ast.Attribute) and func.attr in {"execute", "commit", "record", "notify", "write"}:
                return True
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "sys" and func.attr == "exit":
                return True
            if isinstance(func, ast.Name) and func.id in {"print", "_emit"}:
                return True
        elif isinstance(child, ast.Raise):
            return True
        elif isinstance(child, ast.Return) and child.value is not None:
            return True
    return False


def _is_pytest_parametrized_test_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    path: Path,
) -> bool:
    posix = path.as_posix()
    if "/tests/" not in posix and "\\tests\\" not in str(path):
        return False
    if not node.name.startswith("test_"):
        return False
    for dec in getattr(node, "decorator_list", []):
        if not isinstance(dec, ast.Call):
            continue
        func = dec.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "parametrize"
            and isinstance(func.value, ast.Attribute)
            and func.value.attr == "mark"
            and isinstance(func.value.value, ast.Name)
            and func.value.value.id == "pytest"
        ):
            return True
    return False


def _is_non_blocking_logging_helper_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    parent_map: dict[ast.AST, ast.AST],
) -> bool:
    if not _LOGGING_HELPER_NAME_PATTERN.match(node.name):
        return False
    docs = [
        _get_node_docstring(node),
        _get_ancestor_docstring(node, parent_map, ast.ClassDef),
        _get_ancestor_docstring(node, parent_map, ast.Module),
    ]
    if not any(d and _NON_BLOCKING_HINT_PATTERN.search(d) for d in docs):
        return False
    for child in ast.walk(ast.Module(body=node.body, type_ignores=[])):
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr in {
            "warning", "info", "exception", "error", "debug", "add", "commit",
        }:
            return True
    return False


def scan(paths: list[Path], root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    for path in [p for p in paths if p.suffix.lower() == ".py"]:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        parent_map = _build_parent_map(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            arg_names = [a.arg for a in node.args.args if a.arg not in {"self", "cls"}]
            # Calibrated (P1-4): 5 positional args is widely accepted; only 6+
            # is reported. Constructors with 5 params are common and not a smell.
            if len(arg_names) < 6:
                continue
            if _is_boundary_interface_function(node):
                continue
            if _is_pytest_parametrized_test_function(node, path):
                continue
            if _is_non_blocking_logging_helper_function(node, parent_map):
                continue
            findings.append(
                build_finding(
                    finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                    ci_id="CI-18",
                    signal="CI18_PARAMETER_CLUSTER",
                    severity="medium",
                    target_file=_relative_path(path, root),
                    line=node.lineno,
                    excerpt=f"def {node.name}({', '.join(arg_names[:6])}{'...' if len(arg_names) > 6 else ''})",
                    reason=f"Function takes {len(arg_names)} positional arguments; consider a named parameter object.",
                    evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                    recommended_action="Group related parameters into a named data structure or configuration object.",
                    confidence=CONFIDENCE_MEDIUM,
                    priority="P2",
                    owner_lane=LANE_NATIVE_STATIC,
                    verification_status=VERIFICATION_EXECUTED,
                )
            )
    return findings
