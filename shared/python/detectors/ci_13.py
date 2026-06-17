"""CI-13 Dependency Rot — cross-file circular-import detector.

Single-file linters cannot see import cycles; this builds the intra-project
import graph across all scanned files and reports strongly-connected components
(modules that import each other, directly or transitively). Imports inside
functions (deferred) and under `if TYPE_CHECKING:` are excluded — they do not
cause runtime import cycles.
"""
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

# Stdlib top-level names. An absolute `import typing` is the stdlib module even
# when a scanned package has a `typing.py` submodule (Python resolves the bare
# absolute name to stdlib); without this guard, such shadowing creates false
# cycles. Intra-package imports use relative (`.x`) or the full package prefix.
_STDLIB_NAMES = frozenset(sys.stdlib_module_names)

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_HIGH,
    )
    from ._helpers import _relative_path, _cached_parse
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_HIGH,
    )
    from detectors._helpers import _relative_path, _cached_parse  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI13_CIRCULAR_IMPORT"})


@dataclass
class _TarjanState:
    index_of: dict[str, int]
    low: dict[str, int]
    on_stack: set[str]
    stack: list[str]
    result: list[list[str]]
    counter: int = 0


def _module_name(path: Path, root: Path) -> tuple[str, bool]:
    """(dotted module name relative to root, is_package_init)."""
    rel = path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    is_init = parts and parts[-1] == "__init__"
    if is_init:
        parts = parts[:-1]
    return ".".join(parts), bool(is_init)


def _module_imports(tree: ast.Module, current: str, is_init: bool) -> set[str]:
    """Absolute dotted names imported at module scope (excludes function-local
    and TYPE_CHECKING-guarded imports)."""
    # package the relative imports are resolved against
    package = current if is_init else (current.rsplit(".", 1)[0] if "." in current else "")

    def _resolve_relative(level: int, module: str | None) -> str:
        base_parts = package.split(".") if package else []
        # level 1 = current package; each extra level drops one component
        drop = level - 1
        base = base_parts[: len(base_parts) - drop] if drop <= len(base_parts) else []
        target = list(base)
        if module:
            target += module.split(".")
        return ".".join(target)

    def _is_stdlib_absolute(name: str) -> bool:
        return name.split(".")[0] in _STDLIB_NAMES

    imports: set[str] = set()
    for stmt in tree.body:  # module scope only
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                if not _is_stdlib_absolute(alias.name):
                    imports.add(alias.name)
        elif isinstance(stmt, ast.ImportFrom):
            if stmt.level:
                base = _resolve_relative(stmt.level, stmt.module)
            else:
                base = stmt.module or ""
                if base and _is_stdlib_absolute(base):
                    continue  # absolute stdlib import (shadowing-safe)
            if base:
                imports.add(base)
                for alias in stmt.names:
                    imports.add(f"{base}.{alias.name}")
    return imports


def _visit_scc(node: str, graph: dict[str, set[str]], state: _TarjanState) -> None:
    state.index_of[node] = state.counter
    state.low[node] = state.counter
    state.counter += 1
    state.stack.append(node)
    state.on_stack.add(node)

    for neighbor in sorted(graph.get(node, ())):
        if neighbor not in graph:
            continue
        if neighbor not in state.index_of:
            _visit_scc(neighbor, graph, state)
            state.low[node] = min(state.low[node], state.low[neighbor])
            continue
        if neighbor in state.on_stack:
            state.low[node] = min(state.low[node], state.index_of[neighbor])

    if state.low[node] != state.index_of[node]:
        return
    component: list[str] = []
    while True:
        current = state.stack.pop()
        state.on_stack.discard(current)
        component.append(current)
        if current == node:
            break
    if len(component) > 1:
        state.result.append(component)


def _strongly_connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    """Tarjan's SCC algorithm."""
    state = _TarjanState(index_of={}, low={}, on_stack=set(), stack=[], result=[])
    for start in graph:
        if start not in state.index_of:
            _visit_scc(start, graph, state)
    return state.result


def scan(paths: list[Path], root: Path, next_id: int) -> list[AciFinding]:
    modules: dict[str, Path] = {}
    trees: dict[str, tuple[ast.Module, bool]] = {}
    for path in [p for p in paths if p.suffix.lower() == ".py"]:
        try:
            tree = _cached_parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        name, is_init = _module_name(path, root)
        if not name:
            continue
        modules[name] = path
        trees[name] = (tree, is_init)

    graph: dict[str, set[str]] = {name: set() for name in modules}
    for name, (tree, is_init) in trees.items():
        for imported in _module_imports(tree, name, is_init):
            if imported in modules and imported != name:
                graph[name].add(imported)

    findings: list[AciFinding] = []
    for component in _strongly_connected_components(graph):
        cycle = sorted(component)
        anchor = modules[cycle[0]]
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-13",
                signal="CI13_CIRCULAR_IMPORT",
                severity="medium",
                target_file=_relative_path(anchor, root),
                line=1,
                excerpt=" <-> ".join(cycle[:4]) + ("..." if len(cycle) > 4 else ""),
                reason=(
                    f"Circular import among {len(cycle)} modules: "
                    f"{', '.join(cycle[:5])}{'...' if len(cycle) > 5 else ''}. "
                    "Modules that import each other are tightly coupled and fragile to load order."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action=(
                    "Break the cycle: extract the shared surface into a third module, "
                    "or defer one import into the function that needs it."
                ),
                confidence=CONFIDENCE_HIGH,
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
