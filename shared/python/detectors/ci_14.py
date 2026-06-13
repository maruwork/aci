"""CI-14 Security Neglect detectors (eval/exec, subprocess shell=True, plaintext secrets, insecure HTTP)."""
from __future__ import annotations

import re
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        SEVERITY_CRITICAL, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
    )
    from ._helpers import _relative_path, _line_excerpt, _line_number_from_index
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        SEVERITY_CRITICAL, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
    )
    from detectors._helpers import _relative_path, _line_excerpt, _line_number_from_index  # type: ignore[no-redef]

SIGNALS_EVAL_EXEC: frozenset[str] = frozenset({"CI14_DYNAMIC_CODE_EXECUTION"})
SIGNALS_SUBPROCESS: frozenset[str] = frozenset({"CI14_SUBPROCESS_SHELL_TRUE"})
SIGNALS_SECRET: frozenset[str] = frozenset({"CI14_PLAINTEXT_SECRET"})
SIGNALS_HTTP: frozenset[str] = frozenset({"CI14_INSECURE_HTTP"})

_EVAL_EXEC_PATTERN = re.compile(r"\b(eval|exec)\s*\(")
_SUBPROCESS_SHELL_TRUE_PATTERN = re.compile(
    r"\bsubprocess\.(run|Popen|call|check_call|check_output)\s*\([^)]*shell\s*=\s*True",
    re.DOTALL,
)
_PLAINTEXT_SECRET_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][A-Za-z0-9_\-]{8,}['\"]"
)
_INSECURE_HTTP_PATTERN = re.compile(r"(?i)http://[A-Za-z0-9._:/\-]+")


def scan_eval_exec(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() != ".py":
        return findings
    for match in _EVAL_EXEC_PATTERN.finditer(text):
        line = _line_number_from_index(text, match.start())
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-14",
                signal="CI14_DYNAMIC_CODE_EXECUTION",
                severity="high",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason="Dynamic code execution through eval/exec expands the attack surface and weakens reviewability.",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Replace dynamic code execution with bounded parsing or explicit dispatch tables.",
                confidence=CONFIDENCE_HIGH,
                priority="P1",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def scan_subprocess_shell_true(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() != ".py":
        return findings
    for match in _SUBPROCESS_SHELL_TRUE_PATTERN.finditer(text):
        line = _line_number_from_index(text, match.start())
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-14",
                signal="CI14_SUBPROCESS_SHELL_TRUE",
                severity="high",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason="subprocess with shell=True can widen command injection risk and obscure execution boundaries.",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Prefer argument arrays with shell=False and explicit escaping boundaries.",
                confidence=CONFIDENCE_HIGH,
                priority="P1",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def scan_plaintext_secrets(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    for match in _PLAINTEXT_SECRET_PATTERN.finditer(text):
        line = _line_number_from_index(text, match.start())
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-14",
                signal="CI14_PLAINTEXT_SECRET",
                severity=SEVERITY_CRITICAL,
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason="Possible plaintext secret material is committed directly in the scanned target.",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Move the value into a secret store or environment boundary and rotate it if it is real.",
                confidence=CONFIDENCE_MEDIUM,
                priority="P1",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _http_match_is_noise(line_text: str, col: int) -> bool:
    """Skip http:// occurrences that are not live transport: in a comment, or
    in a doctest example line (>>> / ...). These dominate the false positives
    (doc links, docstring examples) on real codebases."""
    before = line_text[:col]
    if "#" in before:
        return True
    stripped = line_text.lstrip()
    return stripped.startswith(">>>") or stripped.startswith("...")


def scan_insecure_http(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() not in {".py", ".json", ".yml", ".yaml", ".toml", ".txt", ".md"}:
        return findings
    lines = text.splitlines()
    for match in _INSECURE_HTTP_PATTERN.finditer(text):
        line = _line_number_from_index(text, match.start())
        line_text = lines[line - 1] if 0 <= line - 1 < len(lines) else ""
        col = match.start() - (text.rfind("\n", 0, match.start()) + 1)
        if _http_match_is_noise(line_text, col):
            continue
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-14",
                signal="CI14_INSECURE_HTTP",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason="Plain HTTP endpoint usage can weaken transport guarantees if the target is expected to be protected.",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Prefer HTTPS or document why plaintext transport is intentionally bounded and safe.",
                confidence=CONFIDENCE_MEDIUM,
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
