"""CI-23 Contract Drift detector."""
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

SIGNALS: frozenset[str] = frozenset({"CI23_CONTRACT_FIELD_DRIFT"})

# A cross-file call-arity detector was prototyped and reverted (T12): without
# full import resolution it produced only false positives on real code (names
# rebound by local assignment, e.g. rich `_cell_len = cell_len`, or imported from
# a different module than the same-named project def, e.g. typing_extensions
# `assert_never` vs a v1 shim). Correct call/arity checking needs a resolver +
# types — that is mypy's job (external-analyzer lane), and mature code has ~0 real
# arity bugs to find. Not viable at acceptable precision as a native heuristic.


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
        if node.args.kwarg is None:
            continue
        kwargs_name = node.args.kwarg.arg
        body_mod = ast.Module(body=node.body, type_ignores=[])
        hidden_fields: dict[str, int] = {}
        for child in ast.walk(body_mod):
            if (
                isinstance(child, ast.Subscript)
                and isinstance(child.value, ast.Name)
                and child.value.id == kwargs_name
                and isinstance(child.slice, ast.Constant)
                and isinstance(child.slice.value, str)
            ):
                field = child.slice.value
                if field not in hidden_fields:
                    hidden_fields[field] = child.lineno
            elif (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and isinstance(child.func.value, ast.Name)
                and child.func.value.id == kwargs_name
                and child.func.attr == "get"
                and child.args
                and isinstance(child.args[0], ast.Constant)
                and isinstance(child.args[0].value, str)
            ):
                field = child.args[0].value
                if field not in hidden_fields:
                    hidden_fields[field] = child.lineno
        if len(hidden_fields) < 2:
            continue
        field_list = ", ".join(f'"{f}"' for f in sorted(hidden_fields.keys())[:5])
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-23",
                signal="CI23_CONTRACT_FIELD_DRIFT",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=node.lineno,
                excerpt=_line_excerpt(text, node.lineno),
                reason=(
                    f"Function '{node.name}' hides {len(hidden_fields)} implicit field(s) "
                    f"({field_list}) inside **{kwargs_name}; the call contract is invisible to callers."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action=(
                    "Replace **kwargs with explicit named parameters or a typed "
                    "dataclass/TypedDict to make the field contract visible and checkable."
                ),
                confidence=CONFIDENCE_LOW,
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
