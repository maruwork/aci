"""CI-20 Scattered Constant detector."""
from __future__ import annotations

import ast
import re
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from ..aci_signals import LOW_INFO_SCATTERED_LITERALS, LOW_INFO_SCATTERED_LITERAL_SUFFIXES
    from ._helpers import _relative_path, _build_parent_map
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from aci_signals import LOW_INFO_SCATTERED_LITERALS, LOW_INFO_SCATTERED_LITERAL_SUFFIXES  # type: ignore[no-redef]
    from detectors._helpers import _relative_path, _build_parent_map  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI20_SCATTERED_CONSTANT"})

_CONTRACT_FIELD_LITERAL_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,}$")
_WINDOWS_PROJECT_PATH_LITERAL_PATTERN = re.compile(r"^[A-Za-z]:\\Users\\[^\\]+\\project\\")
_CODE_FENCE_SPLITTER_LITERAL = r"(```[\s\S]*?```)"
_PYTHON_DUNDER_LITERAL_PATTERN = re.compile(r"^__[a-zA-Z_]+__$")
_ARGPARSE_ACTION_LITERALS: frozenset[str] = frozenset({
    "store_true", "store_false", "store_const", "append_const",
})


def _is_low_information_scattered_literal(text: str) -> bool:
    if text in LOW_INFO_SCATTERED_LITERALS:
        return True
    if text == _CODE_FENCE_SPLITTER_LITERAL:
        return True
    if text.endswith(LOW_INFO_SCATTERED_LITERAL_SUFFIXES):
        return True
    if _WINDOWS_PROJECT_PATH_LITERAL_PATTERN.match(text):
        return True
    if _PYTHON_DUNDER_LITERAL_PATTERN.match(text):
        return True
    if text in _ARGPARSE_ACTION_LITERALS:
        return True
    return False


def _is_contract_field_literal_context(
    node: ast.Constant,
    parent_map: dict[ast.AST, ast.AST],
) -> bool:
    parent = parent_map.get(node)
    grandparent = parent_map.get(parent) if parent is not None else None
    if isinstance(parent, ast.Dict):
        if node in parent.keys:
            return True
        if node in parent.values:
            vals = [v.value for v in parent.values if isinstance(v, ast.Constant) and isinstance(v.value, str)]
            if vals and all(_CONTRACT_FIELD_LITERAL_PATTERN.match(v) for v in vals):
                return True
    if isinstance(parent, ast.Call):
        func = parent.func
        if isinstance(func, ast.Attribute) and func.attr in {"get", "pop", "setdefault"}:
            return bool(parent.args) and parent.args[0] is node
        if isinstance(func, ast.Attribute) and func.attr == "label":
            return bool(parent.args) and parent.args[0] is node
    if isinstance(parent, ast.Subscript):
        return parent.slice is node
    if isinstance(parent, (ast.List, ast.Tuple, ast.Set)) and isinstance(grandparent, ast.Assign):
        targets = [t.id for t in grandparent.targets if isinstance(t, ast.Name)]
        if any(tok in name.lower() for name in targets for tok in ("field", "column", "col", "key")):
            return True
    if isinstance(parent, ast.keyword) and parent.arg in {"fieldnames", "columns", "keys"}:
        return True
    return False


def _is_contract_field_literal_family(
    literal: str,
    refs: list[tuple[Path, int, bool]],
) -> bool:
    if not _CONTRACT_FIELD_LITERAL_PATTERN.match(literal) or len(refs) < 3:
        return False
    return sum(1 for _, _, ctx in refs if ctx) / len(refs) >= 0.75


def _is_date_format_literal_family(
    literal: str,
    refs: list[tuple[Path, int, bool]],
) -> bool:
    return len(refs) >= 3 and "%" in literal and all(t in literal for t in ("%Y", "%m", "%d"))


def _is_api_route_literal_family(
    literal: str,
    refs: list[tuple[Path, int, bool]],
) -> bool:
    return len(refs) >= 3 and literal.startswith("/api/")


def _is_test_memory_sqlite_literal_family(
    literal: str,
    refs: list[tuple[Path, int, bool]],
) -> bool:
    return (
        literal == "sqlite:///:memory:"
        and len(refs) >= 3
        and all("/tests/" in p.as_posix() for p, _, _ in refs)
    )


def _is_severity_literal_family(
    literal: str,
    refs: list[tuple[Path, int, bool]],
) -> bool:
    return len(refs) >= 3 and literal in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "WARN", "ERROR"}


def _is_export_manifest_literal(node: ast.Constant, parent_map: dict[ast.AST, ast.AST]) -> bool:
    """True when the string is an element of a list/tuple assigned to ``__all__``.

    Symbol names re-exported through ``__all__`` repeat across a package's
    modules by design; they are export declarations, not scattered constants.
    """
    container = parent_map.get(node)
    if not isinstance(container, (ast.List, ast.Tuple)):
        return False
    parent = parent_map.get(container)
    if isinstance(parent, ast.Assign):
        return any(isinstance(t, ast.Name) and t.id == "__all__" for t in parent.targets)
    if isinstance(parent, (ast.AnnAssign, ast.AugAssign)):
        return isinstance(parent.target, ast.Name) and parent.target.id == "__all__"
    return False


_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _collect_symbol_names(tree: ast.AST) -> set[str]:
    """Names defined or imported in a module: class/function names and import
    aliases. A string literal equal to one of these is a symbol reference
    (re-export, lazy import, getattr/registry key), not a config constant."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
    return names


def scan(paths: list[Path], root: Path, next_id: int) -> list[AciFinding]:
    py_paths = [p for p in paths if p.suffix.lower() == ".py"]
    trees: list[tuple[Path, ast.Module]] = []
    symbol_names: set[str] = set()
    for path in py_paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        trees.append((path, tree))
        symbol_names |= _collect_symbol_names(tree)

    occurrences: dict[str, list[tuple[Path, int, bool]]] = {}
    for path, tree in trees:
        parent_map = _build_parent_map(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            text = node.value.strip()
            if len(text) < 8 or " " in text:
                continue
            if _is_low_information_scattered_literal(text):
                continue
            if _is_export_manifest_literal(node, parent_map):
                continue
            if _IDENTIFIER_PATTERN.match(text) and text in symbol_names:
                # The string names a class/function/import defined in the scanned
                # tree — a symbol reference (re-export / lazy import / registry
                # key), not a scattered configuration constant.
                continue
            occurrences.setdefault(text, []).append(
                (path, getattr(node, "lineno", 0), _is_contract_field_literal_context(node, parent_map))
            )
    findings: list[AciFinding] = []
    for literal, refs in occurrences.items():
        if _is_contract_field_literal_family(literal, refs):
            continue
        if _is_date_format_literal_family(literal, refs):
            continue
        if _is_api_route_literal_family(literal, refs):
            continue
        if _is_test_memory_sqlite_literal_family(literal, refs):
            continue
        if _is_severity_literal_family(literal, refs):
            continue
        distinct = {_relative_path(p, root) for p, _, _ in refs}
        if len(distinct) < 3:
            continue
        first_path, first_line, _ = refs[0]
        files_sample = ", ".join(sorted(distinct)[:3])
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-20",
                signal="CI20_SCATTERED_CONSTANT",
                severity="medium",
                target_file=_relative_path(first_path, root),
                line=first_line or None,
                excerpt=repr(literal),
                reason=f"String constant appears in {len(distinct)} files without a single defining owner: {files_sample}",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Extract the shared constant into a named symbol at its canonical owner and import from there.",
                confidence=CONFIDENCE_MEDIUM,
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
