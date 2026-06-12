"""CI-03 TODO Decay detector."""
from __future__ import annotations

import re
import tokenize
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_HUMAN_JUDGMENT, VERIFICATION_EXECUTED,
        CONFIDENCE_HIGH,
    )
    from ._helpers import _relative_path, _line_excerpt
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_HUMAN_JUDGMENT, VERIFICATION_EXECUTED,
        CONFIDENCE_HIGH,
    )
    from detectors._helpers import _relative_path, _line_excerpt  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI03_TODO_HACK"})

_TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK)\b")
_COMMENT_PREFIXES = ("#", "//", ";", "<!--")


def _todo_matches_from_python_comments(text: str) -> list[int]:
    lines: list[int] = []
    try:
        for token in tokenize.generate_tokens(iter(text.splitlines(keepends=True)).__next__):
            if token.type != tokenize.COMMENT:
                continue
            if _TODO_PATTERN.search(token.string):
                lines.append(token.start[0])
    except tokenize.TokenError:
        return []
    return lines


def _todo_matches_from_comment_lines(text: str) -> list[int]:
    lines: list[int] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.lstrip()
        if not stripped.startswith(_COMMENT_PREFIXES):
            continue
        if _TODO_PATTERN.search(stripped):
            lines.append(line_no)
    return lines


def scan(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    if path.suffix.lower() == ".py":
        line_numbers = _todo_matches_from_python_comments(text)
    elif path.suffix.lower() in {".md", ".txt", ".json"}:
        line_numbers = []
    else:
        line_numbers = _todo_matches_from_comment_lines(text)

    findings: list[AciFinding] = []
    for line in line_numbers:
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-03",
                signal="CI03_TODO_HACK",
                severity="low",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason="Patchwork markers such as TODO/FIXME/HACK remain in the scanned target.",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Decide whether the marker should become tracked follow-up work or be removed from the authority surface.",
                confidence=CONFIDENCE_HIGH,
                priority="P3",
                owner_lane=LANE_HUMAN_JUDGMENT,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
