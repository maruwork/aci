"""CI-25 Nondeterminism (Environment Drift) detector."""
from __future__ import annotations

import ast
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM, CONFIDENCE_LOW,
    )
    from ._helpers import _relative_path, _line_excerpt, _cached_parse, ImportResolver
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM, CONFIDENCE_LOW,
    )
    from detectors._helpers import _relative_path, _line_excerpt, _cached_parse, ImportResolver  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI25_ENVIRONMENT_DRIFT"})

_RANDOM_METHODS: frozenset[str] = frozenset({
    "random", "randint", "choice", "shuffle", "uniform", "sample",
})
# Owner expressions that resolve to the stdlib datetime class, across spellings:
# `from datetime import datetime` (-> "datetime.datetime"), `import datetime`
# then `datetime.datetime.now()` (-> "datetime.datetime"), and the legacy bare
# `datetime.now()` form (owner resolves to the module name "datetime").
_DATETIME_OWNER_QUALNAMES: frozenset[str] = frozenset({"datetime", "datetime.datetime"})


def _call_text(node: ast.Call, resolver: ImportResolver) -> str | None:
    func = node.func
    if not isinstance(func, ast.Attribute):
        return None
    owner_qual = resolver.qualname(func.value)
    if func.attr in {"now", "today"} and not node.args and not node.keywords:
        if owner_qual in _DATETIME_OWNER_QUALNAMES:
            return f"datetime.{func.attr}()"
    if func.attr in _RANDOM_METHODS and owner_qual == "random":
        return f"random.{func.attr}"
    return None


def scan(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = _cached_parse(text)
    except SyntaxError:
        return []
    resolver = ImportResolver(tree)
    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        call_text = _call_text(node, resolver)
        if call_text is None:
            continue
        line = node.lineno
        # Confidence reflects evidence quality, not certainty of a defect. A bare
        # naive datetime.now()/today() is a well-known timezone-and-replay smell
        # (medium). random.* is far more often deliberate -- jitter, sampling,
        # shuffling, backoff, cryptographic nonces -- so without dataflow we can
        # only mark it as a determinism-review candidate (low).
        is_datetime = call_text.startswith("datetime")
        confidence = CONFIDENCE_MEDIUM if is_datetime else CONFIDENCE_LOW
        reason = (
            f"'{call_text}' reads wall-clock time; naive datetime is timezone- and "
            "replay-dependent and can differ across machines and CI."
            if is_datetime else
            f"'{call_text}' draws on the global PRNG; if this value feeds logic, IDs, "
            "or output it makes runs non-reproducible. Confirm the randomness is intended."
        )
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-25",
                signal="CI25_ENVIRONMENT_DRIFT",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason=reason,
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action=(
                    "Inject time/randomness as explicit parameters (or use a seeded "
                    "Random / timezone-aware datetime.now(UTC)) so callers control determinism."
                ),
                confidence=confidence,
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
