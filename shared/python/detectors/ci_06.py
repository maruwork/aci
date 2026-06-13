"""CI-06 Magic Number detector."""
from __future__ import annotations

import ast
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_LOW,
    )
    from ._helpers import _relative_path, _build_parent_map
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_LOW,
    )
    from detectors._helpers import _relative_path, _build_parent_map  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI06_MAGIC_NUMBER"})

_TRIVIAL_NUMBERS: frozenset = frozenset({
    0, 1, 2, 3, 4, 5, 10, 100, 1000,
    0.0, 1.0, 0.5,
})


def _is_low_value_number(val: int | float) -> bool:
    """Numbers that are pervasive and not 'magic' in the configuration sense.

    Calibrated (P1-4): small integers (|n| <= 16, common loop/index/byte values)
    and exact powers of two (bit masks, buffer/window sizes) dominate the
    cross-file repetition noise on mature code, so they are not reported.
    """
    if val in _TRIVIAL_NUMBERS:
        return True
    if isinstance(val, int):
        n = abs(val)
        if n <= 16:
            return True
        if n & (n - 1) == 0:  # exact power of two
            return True
    return False


def scan(paths: list[Path], root: Path, next_id: int) -> list[AciFinding]:
    occurrences: dict[int | float, list[tuple[Path, int]]] = {}
    for path in [p for p in paths if p.suffix.lower() == ".py"]:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(text)
        except SyntaxError:
            continue
        parent_map = _build_parent_map(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue
            val = node.value
            if isinstance(val, bool):
                continue
            if not isinstance(val, (int, float)):
                continue
            if _is_low_value_number(val):
                continue
            parent = parent_map.get(node)
            if isinstance(parent, ast.UnaryOp):
                continue
            if isinstance(parent, ast.arguments):
                continue
            if isinstance(parent, ast.Assign):
                if any(isinstance(t, ast.Name) and t.id.isupper() for t in parent.targets):
                    continue
            occurrences.setdefault(val, []).append((path, getattr(node, "lineno", 0)))

    findings: list[AciFinding] = []
    for val, refs in occurrences.items():
        distinct = {_relative_path(p, root) for p, _ in refs}
        if len(distinct) < 3:
            continue
        first_path, first_line = refs[0]
        files_sample = ", ".join(sorted(distinct)[:3])
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-06",
                signal="CI06_MAGIC_NUMBER",
                severity="low",
                target_file=_relative_path(first_path, root),
                line=first_line,
                excerpt=repr(val),
                reason=(
                    f"Numeric literal {val!r} appears across {len(distinct)} files without a named constant: "
                    f"{files_sample}"
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Define the value as a named constant at a canonical owner and import it from there.",
                confidence=CONFIDENCE_LOW,
                priority="P3",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
