"""Shared utilities for all native detector modules."""
from __future__ import annotations

import ast
import functools
from pathlib import Path


@functools.lru_cache(maxsize=1024)
def _cached_parse(text: str) -> ast.Module:
    """Parse source text, memoized by the text itself.

    During one scan every per-file detector and every cross-file detector parses
    the same files; without caching that is ~18 ast.parse calls per file. The key
    is the source text (identical text always yields the same AST), so the cache
    is correctness-safe and self-invalidating. Callers treat the returned tree as
    read-only (detectors only walk it / build separate parent maps)."""
    return ast.parse(text)


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _line_number_from_index(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _line_excerpt(text: str, line_number: int) -> str:
    lines = text.splitlines()
    if 1 <= line_number <= len(lines):
        return lines[line_number - 1].strip()
    return ""


def _build_parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


class ImportResolver:
    """Resolve a call/attribute expression to a canonical dotted name.

    Detectors that key on a module owner (``pickle.loads``, ``subprocess.run``,
    ``datetime.datetime.now``) used to match the *literal* spelling, so an alias
    (``import pickle as p``) or a ``from`` binding (``from pickle import loads``)
    silently evaded them. This builds the local import bindings once per tree so
    those forms resolve to the same canonical name as the explicit spelling.

    Limits (intentionally conservative): only ``import``/``from import`` bindings
    are tracked. Variable aliasing (``m = pickle; m.loads()``), dynamic
    ``importlib.import_module`` lookups, and relative imports are not resolved.
    """

    def __init__(self, tree: ast.AST) -> None:
        # local name -> canonical module dotted path (e.g. {"p": "pickle"})
        self._module_aliases: dict[str, str] = {}
        # local name -> canonical "module.symbol" (e.g. {"loads": "pickle.loads"})
        self._symbol_aliases: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.asname:
                        self._module_aliases[alias.asname] = alias.name
                    else:
                        top = alias.name.split(".")[0]
                        self._module_aliases[top] = top
            elif isinstance(node, ast.ImportFrom):
                # Skip relative imports (level > 0): they cannot be canonicalized
                # to a stable module path from a single file.
                if node.level or node.module is None:
                    continue
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    local = alias.asname or alias.name
                    self._symbol_aliases[local] = f"{node.module}.{alias.name}"

    def qualname(self, node: ast.AST) -> str | None:
        """Return the canonical dotted name for a Name/Attribute expression."""
        if isinstance(node, ast.Name):
            if node.id in self._symbol_aliases:
                return self._symbol_aliases[node.id]
            if node.id in self._module_aliases:
                return self._module_aliases[node.id]
            return node.id
        if isinstance(node, ast.Attribute):
            base = self.qualname(node.value)
            if base is None:
                return None
            return f"{base}.{node.attr}"
        return None

    def call_qualname(self, node: ast.Call) -> str | None:
        """Canonical dotted name of a call's callee, or None if unresolvable."""
        return self.qualname(node.func)

    def imported_roots(self) -> set[str]:
        """Top-level module names actually brought in by an import in this tree.

        Used to require that a dangerous canonical name (``pickle.loads``) was
        reached through a real import, so a local object that merely happens to
        be named ``pickle``/``marshal`` is not a false positive."""
        roots = {name.split(".")[0] for name in self._module_aliases.values()}
        roots |= {value.split(".")[0] for value in self._symbol_aliases.values()}
        return roots
