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


def _function_body_content(node: ast.FunctionDef | ast.AsyncFunctionDef, text: str) -> tuple[str, ...] | None:
    if not hasattr(node, "end_lineno") or node.end_lineno is None:
        return None
    lines = text.splitlines()
    body_lines = lines[node.lineno : node.end_lineno]
    stripped = [ln.strip() for ln in body_lines if ln.strip()]
    if stripped and (stripped[0].startswith('"""') or stripped[0].startswith("'''")):
        for i, ln in enumerate(stripped):
            if i > 0 and (ln.endswith('"""') or ln.endswith("'''")):
                stripped = stripped[i + 1 :]
                break
    if len(stripped) < 4:
        return None
    return tuple(stripped)


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
            content = _function_body_content(node, text)
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
                    f"Function body is duplicated across {len(distinct)} files without a shared abstraction: "
                    f"{files_sample}"
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
