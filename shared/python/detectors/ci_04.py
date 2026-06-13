"""CI-04 God Class detector."""
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

SIGNALS: frozenset[str] = frozenset({"CI04_GOD_CLASS"})

# Calibrated (P1-4): library classes commonly hold 16-19 cohesive methods or
# 11-14 attributes without being god classes. Only 20+ methods or 15+ attributes
# are reported as a god-class signal.
_METHOD_COUNT_THRESHOLD = 19
_ATTRIBUTE_COUNT_THRESHOLD = 14


def _count_non_dunder_methods(class_node: ast.ClassDef) -> int:
    return sum(
        1 for node in class_node.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not (node.name.startswith("__") and node.name.endswith("__"))
    )


def _count_instance_attributes(class_node: ast.ClassDef) -> int:
    attrs: set[str] = set()
    for node in ast.walk(class_node):
        if not isinstance(node, ast.FunctionDef) or node.name != "__init__":
            continue
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        attrs.add(target.attr)
            elif isinstance(stmt, ast.AnnAssign):
                if (
                    isinstance(stmt.target, ast.Attribute)
                    and isinstance(stmt.target.value, ast.Name)
                    and stmt.target.value.id == "self"
                ):
                    attrs.add(stmt.target.attr)
    return len(attrs)


def scan(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        method_count = _count_non_dunder_methods(node)
        attr_count = _count_instance_attributes(node)
        if method_count <= _METHOD_COUNT_THRESHOLD and attr_count <= _ATTRIBUTE_COUNT_THRESHOLD:
            continue
        reason_parts = []
        if method_count > _METHOD_COUNT_THRESHOLD:
            reason_parts.append(
                f"{method_count} non-dunder methods (threshold: {_METHOD_COUNT_THRESHOLD})"
            )
        if attr_count > _ATTRIBUTE_COUNT_THRESHOLD:
            reason_parts.append(
                f"{attr_count} instance attributes (threshold: {_ATTRIBUTE_COUNT_THRESHOLD})"
            )
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-04",
                signal="CI04_GOD_CLASS",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=node.lineno,
                excerpt=f"class {node.name}",
                reason=f"Class {node.name!r} shows God Class indicators: {'; '.join(reason_parts)}.",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action=(
                    "Split responsibilities into focused classes or extract cohesive groups "
                    "of methods and attributes into separate units."
                ),
                confidence=CONFIDENCE_MEDIUM,
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
