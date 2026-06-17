"""CI-07 Lava Flow — cross-file dead private-symbol detector.

Single-file linters (ruff/pyflakes) only flag names unused within one file. This
finds module-level private definitions (`_name`) that are referenced NOWHERE in
the whole scanned project — likely dead code. Conservative on purpose (libraries
have public APIs and dynamic access): only leading-underscore, module-level,
undecorated functions/classes; a name is spared if it appears in any `__all__`,
any string literal (possible getattr target), or is referenced anywhere.
"""
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

SIGNALS: frozenset[str] = frozenset({"CI07_UNUSED_PRIVATE_SYMBOL"})


def _is_private(name: str) -> bool:
    return name.startswith("_") and not (name.startswith("__") and name.endswith("__"))


def _collect_named_loads(node: ast.AST, used: set[str]) -> bool:
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
        used.add(node.id)
        return True
    if isinstance(node, ast.Attribute):
        used.add(node.attr)
        return True
    return False


def _collect_import_uses(node: ast.AST, used: set[str]) -> bool:
    if isinstance(node, ast.ImportFrom):
        for alias in node.names:
            used.add(alias.name)
            if alias.asname:
                used.add(alias.asname)
        return True
    if isinstance(node, ast.Import):
        for alias in node.names:
            used.add((alias.asname or alias.name).split(".")[0])
        return True
    return False


def _collect_string_protection(node: ast.AST, protected: set[str]) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        protected.add(node.value)
        return True
    return False


def _collect_all_exports(node: ast.AST, protected: set[str]) -> bool:
    if not isinstance(node, ast.Assign):
        return False
    for target in node.targets:
        if isinstance(target, ast.Name) and target.id == "__all__":
            for elt in ast.walk(node.value):
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    protected.add(elt.value)
            return True
    return False


def _collect_protected_exports(node: ast.AST, protected: set[str]) -> bool:
    return _collect_string_protection(node, protected) or _collect_all_exports(node, protected)


def _collect_uses(tree: ast.AST) -> tuple[set[str], set[str]]:
    """(referenced names, "protected" names that must never be flagged)."""
    used: set[str] = set()
    protected: set[str] = set()
    for node in ast.walk(tree):
        if _collect_named_loads(node, used):
            continue
        if _collect_import_uses(node, used):
            continue
        _collect_protected_exports(node, protected)
    return used, protected


def scan(paths: list[Path], root: Path, next_id: int) -> list[AciFinding]:
    trees: list[tuple[Path, ast.Module]] = []
    used: set[str] = set()
    protected: set[str] = set()
    for path in [p for p in paths if p.suffix.lower() == ".py"]:
        try:
            tree = _cached_parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        trees.append((path, tree))
        file_used, file_protected = _collect_uses(tree)
        used |= file_used
        protected |= file_protected

    findings: list[AciFinding] = []
    for path, tree in trees:
        for node in tree.body:  # module-level only
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            name = node.name
            if not _is_private(name):
                continue
            if node.decorator_list:
                continue  # decorated -> registration/dispatch; spare it
            if name in used or name in protected:
                continue
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            findings.append(
                build_finding(
                    finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                    ci_id="CI-07",
                    signal="CI07_UNUSED_PRIVATE_SYMBOL",
                    severity="low",
                    target_file=_relative_path(path, root),
                    line=node.lineno,
                    excerpt=f"{kind} {name}",
                    reason=(
                        f"Private {kind} '{name}' is defined but referenced nowhere in the "
                        "scanned project — likely dead code (a single-file linter cannot see this)."
                    ),
                    evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                    recommended_action="Remove the unused private symbol, or make it public if it is intended API.",
                    confidence=CONFIDENCE_MEDIUM,
                    priority="P3",
                    owner_lane=LANE_NATIVE_STATIC,
                    verification_status=VERIFICATION_EXECUTED,
                )
            )
    return findings
