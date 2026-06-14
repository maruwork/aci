"""CI-05 Copy-Paste Code detector."""
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

SIGNALS: frozenset[str] = frozenset({"CI05_COPY_PASTE_CODE"})

# Minimum structural size (AST node count) for a body to be considered for
# clone detection — guards against trivial getters/boilerplate matching.
_MIN_SIGNATURE_NODES = 18


def _is_dunder(name: str) -> bool:
    # Dunder/protocol methods (__repr__, __eq__, __rich_repr__, ...) are
    # structurally similar across classes by design — idiomatic, not copy-paste.
    return name.startswith("__") and name.endswith("__")


def _structural_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, ...] | None:
    """A rename/literal-invariant signature of the function body: the sequence of
    AST node TYPES (identifiers and literal values abstracted away). Two functions
    that are copy-pasted and then renamed produce the same signature, so this
    catches near-duplicates a text/token match would miss."""
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]  # drop docstring
    if not body:
        return None
    types: list[str] = []
    for stmt in body:
        for sub in ast.walk(stmt):
            types.append(type(sub).__name__)
    if len(types) < _MIN_SIGNATURE_NODES:
        return None
    return tuple(types)


def scan(paths: list[Path], root: Path, next_id: int) -> list[AciFinding]:
    body_map: dict[tuple[str, ...], list[tuple[Path, int, str]]] = {}
    for path in [p for p in paths if p.suffix.lower() == ".py"]:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if _is_dunder(node.name):
                continue
            content = _structural_signature(node)
            if content is None:
                continue
            body_map.setdefault(content, []).append((path, node.lineno, node.name))

    findings: list[AciFinding] = []
    for content, locs in body_map.items():
        distinct = {_relative_path(p, root) for p, _, _ in locs}
        if len(distinct) < 2:
            continue
        first_path, first_line, first_name = locs[0]
        files_sample = ", ".join(sorted(distinct)[:3])
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-05",
                signal="CI05_COPY_PASTE_CODE",
                severity="medium",
                target_file=_relative_path(first_path, root),
                line=first_line,
                excerpt=f"def {first_name}(...)",
                reason=(
                    f"Function body is structurally duplicated (rename-invariant near-duplicate) "
                    f"across {len(distinct)} files without a shared abstraction: {files_sample}"
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Extract the shared logic into a single named function and call it from each site.",
                confidence=CONFIDENCE_MEDIUM,
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
