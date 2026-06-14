"""CI-04 God Class detector."""
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

SIGNALS: frozenset[str] = frozenset({"CI04_GOD_CLASS"})

# A god class is LARGE *and* LOW-COHESION. Size alone flags cohesive facades
# (BaseModel, Console). We require both: many methods AND the methods split into
# 2+ unrelated responsibility groups (LCOM4 >= 2) — i.e. the class is genuinely
# splittable.
_METHOD_COUNT_THRESHOLD = 15


def _count_non_dunder_methods(class_node: ast.ClassDef) -> int:
    return sum(
        1 for node in class_node.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not (node.name.startswith("__") and node.name.endswith("__"))
    )


def _self_members(method: ast.AST) -> set[str]:
    """Instance members (attributes and self-method names) a method touches."""
    members: set[str] = set()
    for node in ast.walk(method):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            members.add(node.attr)
    return members


def _cohesion_component_sizes(class_node: ast.ClassDef) -> list[int]:
    """Sizes of the connected components when non-dunder methods are linked by
    shared instance members (LCOM4 component structure). Each component is one
    responsibility cluster. Constructors/dunders are excluded (they touch
    everything and would mask the split); methods touching no member are skipped."""
    methods = [
        m for m in class_node.body
        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not (m.name.startswith("__") and m.name.endswith("__"))
    ]
    member_sets = {m.name: _self_members(m) for m in methods}
    active = [name for name, members in member_sets.items() if members]
    if len(active) < 2:
        return [len(active)] if active else []

    parent = {name: name for name in active}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        parent[find(a)] = find(b)

    for i in range(len(active)):
        for j in range(i + 1, len(active)):
            if member_sets[active[i]] & member_sets[active[j]]:
                union(active[i], active[j])

    sizes: dict[str, int] = {}
    for name in active:
        root = find(name)
        sizes[root] = sizes.get(root, 0) + 1
    return sorted(sizes.values(), reverse=True)


def scan(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = _cached_parse(text)
    except SyntaxError:
        return []
    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        method_count = _count_non_dunder_methods(node)
        if method_count < _METHOD_COUNT_THRESHOLD:
            continue
        component_sizes = _cohesion_component_sizes(node)
        substantial = [s for s in component_sizes if s >= 2]
        if len(substantial) < 2:
            # cohesive, or only one real responsibility cluster (+ stray helpers)
            continue
        lcom = len(component_sizes)
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-04",
                signal="CI04_GOD_CLASS",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=node.lineno,
                excerpt=f"class {node.name}",
                reason=(
                    f"Class {node.name!r} has {method_count} methods split into {lcom} "
                    "unrelated responsibility groups (low cohesion / LCOM4)."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action=(
                    "Split the class along its cohesion groups: methods that share no "
                    "instance state belong in separate, focused classes."
                ),
                confidence=CONFIDENCE_MEDIUM,
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
