"""CI-05 Copy-Paste Code detector."""
from __future__ import annotations

import ast
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_LOW,
    )
    from ._helpers import _relative_path, _cached_parse
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_LOW,
    )
    from detectors._helpers import _relative_path, _cached_parse  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI05_COPY_PASTE_CODE"})

# Minimum structural size (AST node count) for a body to be considered for
# clone detection — guards against trivial getters/boilerplate matching.
_MIN_SIGNATURE_NODES = 18


def _is_dunder(name: str) -> bool:
    # Dunder/protocol methods (__repr__, __eq__, __rich_repr__, ...) are
    # structurally similar across classes by design — idiomatic, not copy-paste.
    return name.startswith("__") and name.endswith("__")


def _node_shape(node: ast.AST) -> tuple:
    """Nesting-preserving shape of a node: (type, child-shapes...). Identifiers
    and literal values are abstracted to their node type, so renamed/re-literalled
    copies share a shape; the recursive form keeps tree structure, so A(B(C)) and
    A(B, C) do NOT collide (a flat node-type list would)."""
    return (type(node).__name__, tuple(_node_shape(c) for c in ast.iter_child_nodes(node)))


def _structural_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple | None:
    """Rename/literal-invariant, structure-preserving signature of the function
    body. Copy-paste-then-rename produces the same signature (caught), while
    structurally-different functions do not collide."""
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]  # drop docstring
    if not body:
        return None
    node_count = sum(1 for stmt in body for _ in ast.walk(stmt))
    if node_count < _MIN_SIGNATURE_NODES:
        return None
    return tuple(_node_shape(stmt) for stmt in body)


def _is_support_duplicate_path(relative_path: str) -> bool:
    posix = relative_path.replace("\\", "/").strip("/")
    parts = set(posix.split("/"))
    return bool(
        parts & {"test", "tests", "docs", "example", "examples", "fixture", "fixtures", "sample", "samples"}
        or posix.startswith("shared/tests/")
        or posix.startswith("shared/tools/")
        or posix.startswith("shared/report/examples/")
    )


def scan(paths: list[Path], root: Path, next_id: int) -> list[AciFinding]:
    body_map: dict[tuple, list[tuple[Path, int, str]]] = {}
    for path in [p for p in paths if p.suffix.lower() == ".py"]:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            tree = _cached_parse(text)
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

    # Aggregate clone signatures by the set of files they span. Two parallel
    # implementations that share N duplicated function bodies (e.g. uvicorn's
    # h11 vs httptools HTTP protocols, or a v1/v2 compat namespace) otherwise
    # produce N separate findings for what is really one fact: "these files are
    # structural near-duplicates." One finding per file-set, listing the shared
    # functions, is the actionable unit.
    groups: dict[frozenset[str], list[tuple[Path, int, str]]] = {}
    for content, locs in body_map.items():
        distinct = {_relative_path(p, root) for p, _, _ in locs}
        if len(distinct) < 2:
            continue
        # one representative occurrence (first) per duplicated signature
        groups.setdefault(frozenset(distinct), []).append(locs[0])

    findings: list[AciFinding] = []
    for fileset, funcs in groups.items():
        funcs_sorted = sorted(funcs, key=lambda t: (_relative_path(t[0], root), t[1]))
        first_path, first_line, _first_name = funcs_sorted[0]
        files_sample = ", ".join(sorted(fileset)[:3])
        names = list(dict.fromkeys(nm for _, _, nm in funcs_sorted))  # dedupe, keep order
        name_sample = ", ".join(names[:6]) + ("..." if len(names) > 6 else "")
        support_only = all(_is_support_duplicate_path(relative_path) for relative_path in fileset)
        if len(funcs_sorted) == 1:
            reason = (
                f"Function body is structurally duplicated (rename-invariant near-duplicate) "
                f"across {len(fileset)} files without a shared abstraction: {files_sample}"
            )
        else:
            reason = (
                f"{len(funcs_sorted)} function bodies are structurally duplicated "
                f"(rename-invariant near-duplicates) across {len(fileset)} files without a "
                f"shared abstraction ({files_sample}): {name_sample}"
            )
        if support_only:
            reason = (
                f"Support-only duplicate helper logic spans {len(fileset)} non-runtime files "
                f"({files_sample}): {name_sample}. This is usually advisory unless the helper "
                "forks are drifting independently."
            )
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-05",
                signal="CI05_COPY_PASTE_CODE",
                severity="low" if support_only else "medium",
                target_file=_relative_path(first_path, root),
                line=first_line,
                excerpt=f"def {_first_name}(...)",
                reason=reason,
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action=(
                    "If the duplication is intentional test/support scaffolding, keep it isolated or suppress it explicitly; "
                    "otherwise extract the shared logic into a single named helper."
                    if support_only
                    else "Extract the shared logic into a single named function and call it from each site."
                ),
                # Calibrated to measured field precision (~40% on real code: FPs
                # on trivial boilerplate / re-exports). See examples/aci-field-precision/.
                confidence=CONFIDENCE_LOW,
                priority="P3" if support_only else "P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
