"""External-analyzer output parsers.

Extracted from aci_analyzer_execution.py to keep that orchestration module under a
maintainable size. These are pure stdout/stderr -> normalized-finding functions;
the CI-ID/severity mappers they depend on still live in aci_analyzer_execution and
are imported back here (one-directional: the orchestrator imports these parsers).
"""
from __future__ import annotations

from pathlib import Path
import json
import re

try:
    from .aci_findings import AciFinding, build_finding, LANE_EXTERNAL_ANALYZER, VERIFICATION_EXECUTED
    from .aci_analyzer_execution import (
        _TSC_LINE_PATTERN, _eslint_ci_id, _pyflakes_ci_id, _ruff_ci_id, _ruff_severity, _shellcheck_ci_id,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_EXTERNAL_ANALYZER, VERIFICATION_EXECUTED,
    )
    from aci_analyzer_execution import (  # type: ignore[no-redef]
        _TSC_LINE_PATTERN, _eslint_ci_id, _pyflakes_ci_id, _ruff_ci_id, _ruff_severity, _shellcheck_ci_id,
    )


def _ruff_findings(stdout: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    payload = json.loads(stdout or "[]")
    for item in payload:
        filename = Path(item["filename"])
        try:
            relative = filename.resolve().relative_to(target_root.resolve()).as_posix()
        except ValueError:
            relative = filename.as_posix()
        location = item.get("location", {})
        line = location.get("row")
        code = item.get("code", "")
        findings.append(
            build_finding(
                finding_id=f"F-EXT-{next_id + len(findings):04d}",
                ci_id=_ruff_ci_id(code),
                signal="EXT_RUFF",
                severity=_ruff_severity(code),
                confidence="medium",
                actor_label=LANE_EXTERNAL_ANALYZER,
                triage_state="review-first",
                priority="P2",
                fixability="owner-decision",
                baseline_status="new",
                waiver_status="none",
                lifecycle_state="open",
                owner_lane=LANE_EXTERNAL_ANALYZER,
                target_file=relative,
                line=line,
                excerpt=item.get("message", ""),
                reason=item.get("message", "ruff reported a finding"),
                evidence_ref=f"ruff:{code or 'unknown'}",
                recommended_action="Review the analyzer message and align code or rule configuration.",
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _pyflakes_findings(stdout: str, stderr: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    for raw_line in (stdout + "\n" + stderr).splitlines():
        match = re.match(r"(.+?):(\d+):\s*(.+)", raw_line.strip())
        if not match:
            continue
        filename, line_text, message = match.groups()
        path = Path(filename)
        try:
            relative = path.resolve().relative_to(target_root.resolve()).as_posix()
        except ValueError:
            relative = path.as_posix()
        findings.append(
            build_finding(
                finding_id=f"F-EXT-{next_id + len(findings):04d}",
                ci_id=_pyflakes_ci_id(message),
                signal="EXT_PYFLAKES",
                severity="medium",
                confidence="medium",
                actor_label=LANE_EXTERNAL_ANALYZER,
                triage_state="review-first",
                priority="P2",
                fixability="owner-decision",
                baseline_status="new",
                waiver_status="none",
                lifecycle_state="open",
                owner_lane=LANE_EXTERNAL_ANALYZER,
                target_file=relative,
                line=int(line_text),
                excerpt=message,
                reason=message,
                evidence_ref="pyflakes",
                recommended_action="Review the analyzer message and align code or imports accordingly.",
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _mypy_findings(stdout: str, stderr: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    for raw_line in (stdout + "\n" + stderr).splitlines():
        match = re.match(r"(.+?):(\d+):(?:(\d+):)?\s*(error|note):\s*(.+)", raw_line.strip())
        if not match:
            continue
        filename, line_text, _column_text, level_text, message = match.groups()
        path = Path(filename)
        try:
            relative = path.resolve().relative_to(target_root.resolve()).as_posix()
        except ValueError:
            relative = path.as_posix()
        code_match = re.search(r"\[([^\]]+)\]$", message.strip())
        mypy_code = code_match.group(1) if code_match else None
        findings.append(
            build_finding(
                finding_id=f"F-EXT-{next_id + len(findings):04d}",
                ci_id="CI-23",
                signal="EXT_MYPY",
                severity="high" if level_text == "error" else "low",
                confidence="medium",
                actor_label=LANE_EXTERNAL_ANALYZER,
                triage_state="review-first",
                priority="P2",
                fixability="owner-decision",
                baseline_status="new",
                waiver_status="none",
                lifecycle_state="open",
                owner_lane=LANE_EXTERNAL_ANALYZER,
                target_file=relative,
                line=int(line_text),
                excerpt=message,
                reason=message,
                evidence_ref=f"mypy:{mypy_code}" if mypy_code else "mypy",
                recommended_action="Align declared and actual interfaces so the type contract stays explicit.",
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _pytest_findings(stdout: str, stderr: str, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    for raw_line in stdout.splitlines():
        stripped = raw_line.strip()
        if not stripped.startswith("FAILED "):
            continue
        message = stripped.removeprefix("FAILED ").strip()
        target_file = message.split("::", 1)[0]
        findings.append(
            build_finding(
                finding_id=f"F-EXT-{next_id + len(findings):04d}",
                ci_id="CI-09",
                signal="EXT_PYTEST",
                severity="high",
                confidence="medium",
                actor_label=LANE_EXTERNAL_ANALYZER,
                triage_state="review-first",
                priority="P1",
                fixability="owner-decision",
                baseline_status="new",
                waiver_status="none",
                lifecycle_state="open",
                owner_lane=LANE_EXTERNAL_ANALYZER,
                target_file=target_file,
                line=None,
                excerpt=message,
                reason=message,
                evidence_ref="pytest",
                recommended_action="Inspect the failing test and restore the broken behavior or fixture contract.",
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    if findings:
        return findings
    if "failed" in stdout.lower():
        findings.append(
            build_finding(
                finding_id=f"F-EXT-{next_id:04d}",
                ci_id="CI-09",
                signal="EXT_PYTEST",
                severity="high",
                confidence="low",
                actor_label=LANE_EXTERNAL_ANALYZER,
                triage_state="review-first",
                priority="P1",
                fixability="owner-decision",
                baseline_status="new",
                waiver_status="none",
                lifecycle_state="open",
                owner_lane=LANE_EXTERNAL_ANALYZER,
                target_file="pytest-session",
                line=None,
                excerpt="pytest reported failing tests",
                reason="pytest reported failing tests but the failure lines were not individually parsed.",
                evidence_ref="pytest",
                recommended_action="Open the pytest session output and repair the failing test or fixture contract.",
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _eslint_findings(stdout: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    payload = json.loads(stdout or "[]")
    for file_result in payload:
        filepath = Path(file_result["filePath"])
        try:
            relative = filepath.resolve().relative_to(target_root.resolve()).as_posix()
        except ValueError:
            relative = filepath.as_posix()
        for msg in file_result.get("messages", []):
            rule_id = msg.get("ruleId")
            severity_level = msg.get("severity", 1)
            findings.append(
                build_finding(
                    finding_id=f"F-EXT-{next_id + len(findings):04d}",
                    ci_id=_eslint_ci_id(rule_id),
                    signal="EXT_ESLINT",
                    severity="high" if severity_level == 2 else "medium",
                    confidence="medium",
                    actor_label=LANE_EXTERNAL_ANALYZER,
                    triage_state="review-first",
                    priority="P2",
                    fixability="owner-decision",
                    baseline_status="new",
                    waiver_status="none",
                    lifecycle_state="open",
                    owner_lane=LANE_EXTERNAL_ANALYZER,
                    target_file=relative,
                    line=msg.get("line"),
                    excerpt=msg.get("message", ""),
                    reason=msg.get("message", "eslint reported a finding"),
                    evidence_ref=f"eslint:{rule_id or 'unknown'}",
                    recommended_action="Review the ESLint rule violation and align code or rule configuration.",
                    verification_status=VERIFICATION_EXECUTED,
                )
            )
    return findings


def _semgrep_ci_id(check_id: str) -> str:
    lowered = check_id.lower()
    if ".ci22." in lowered:
        return "CI-22"
    if ".ci23." in lowered:
        return "CI-23"
    if ".ci26." in lowered:
        return "CI-26"
    if ".ci21." in lowered:
        return "CI-21"
    return "CI-14"


def _semgrep_severity(value: str) -> str:
    severity = value.upper()
    if severity == "ERROR":
        return "high"
    if severity == "INFO":
        return "low"
    return "medium"


def _semgrep_findings(stdout: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    payload = json.loads(stdout or "{}")
    for item in payload.get("results", []):
        raw_path = item.get("path", "")
        if not raw_path:
            continue
        path = Path(raw_path)
        try:
            relative = path.resolve().relative_to(target_root.resolve()).as_posix()
        except ValueError:
            relative = path.as_posix()
        extra = item.get("extra", {})
        check_id = str(item.get("check_id", "semgrep.unknown"))
        message = str(extra.get("message", "semgrep reported a finding"))
        line = ((item.get("start") or {}) if isinstance(item.get("start"), dict) else {}).get("line")
        findings.append(
            build_finding(
                finding_id=f"F-EXT-{next_id + len(findings):04d}",
                ci_id=_semgrep_ci_id(check_id),
                signal="EXT_SEMGREP",
                severity=_semgrep_severity(str(extra.get("severity", "WARNING"))),
                confidence="medium",
                actor_label=LANE_EXTERNAL_ANALYZER,
                triage_state="review-first",
                priority="P1" if _semgrep_severity(str(extra.get("severity", "WARNING"))) == "high" else "P2",
                fixability="owner-decision",
                baseline_status="new",
                waiver_status="none",
                lifecycle_state="open",
                owner_lane=LANE_EXTERNAL_ANALYZER,
                target_file=relative,
                line=line if isinstance(line, int) else None,
                excerpt=message,
                reason=message,
                evidence_ref=f"semgrep:{check_id}",
                recommended_action="Review the Semgrep finding and either harden the code path or narrow the rule scope.",
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _tsc_findings(stdout: str, stderr: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    for raw_line in (stdout + "\n" + stderr).splitlines():
        match = _TSC_LINE_PATTERN.match(raw_line.strip())
        if not match:
            continue
        filename, line_text, _col, ts_code, message = match.groups()
        path = Path(filename)
        try:
            relative = path.resolve().relative_to(target_root.resolve()).as_posix()
        except ValueError:
            relative = path.as_posix()
        findings.append(
            build_finding(
                finding_id=f"F-EXT-{next_id + len(findings):04d}",
                ci_id="CI-23",
                signal="EXT_TSC",
                severity="high",
                confidence="high",
                actor_label=LANE_EXTERNAL_ANALYZER,
                triage_state="review-first",
                priority="P1",
                fixability="owner-decision",
                baseline_status="new",
                waiver_status="none",
                lifecycle_state="open",
                owner_lane=LANE_EXTERNAL_ANALYZER,
                target_file=relative,
                line=int(line_text),
                excerpt=message,
                reason=f"{ts_code}: {message}",
                evidence_ref=f"tsc:{ts_code}",
                recommended_action="Resolve the TypeScript type error to maintain type contract integrity.",
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _shellcheck_findings(stdout: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    payload = json.loads(stdout or "[]")
    for item in payload:
        filepath = Path(item["file"])
        try:
            relative = filepath.resolve().relative_to(target_root.resolve()).as_posix()
        except ValueError:
            relative = filepath.as_posix()
        level = item.get("level", "style")
        code = item.get("code", 0)
        message = item.get("message", "")
        findings.append(
            build_finding(
                finding_id=f"F-EXT-{next_id + len(findings):04d}",
                ci_id=_shellcheck_ci_id(level),
                signal="EXT_SHELLCHECK",
                severity="high" if level == "error" else "medium",
                confidence="medium",
                actor_label=LANE_EXTERNAL_ANALYZER,
                triage_state="review-first",
                priority="P2",
                fixability="owner-decision",
                baseline_status="new",
                waiver_status="none",
                lifecycle_state="open",
                owner_lane=LANE_EXTERNAL_ANALYZER,
                target_file=relative,
                line=item.get("line"),
                excerpt=message,
                reason=message,
                evidence_ref=f"shellcheck:SC{code}",
                recommended_action="Review the ShellCheck finding and fix the shell script issue.",
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _sqlfluff_findings(stdout: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    payload = json.loads(stdout or "[]")
    file_list = payload.get("files", payload) if isinstance(payload, dict) else payload
    for file_result in file_list:
        raw_path = file_result.get("filepath", "")
        if not raw_path:
            continue
        filepath = Path(raw_path)
        try:
            relative = filepath.resolve().relative_to(target_root.resolve()).as_posix()
        except ValueError:
            relative = filepath.as_posix()
        for violation in file_result.get("violations", []):
            code = violation.get("code", "")
            description = violation.get("description", "")
            is_warning = violation.get("warning", False)
            findings.append(
                build_finding(
                    finding_id=f"F-EXT-{next_id + len(findings):04d}",
                    ci_id="CI-02",
                    signal="EXT_SQLFLUFF",
                    severity="low" if is_warning else "medium",
                    confidence="medium",
                    actor_label=LANE_EXTERNAL_ANALYZER,
                    triage_state="review-first",
                    priority="P2",
                    fixability="owner-decision",
                    baseline_status="new",
                    waiver_status="none",
                    lifecycle_state="open",
                    owner_lane=LANE_EXTERNAL_ANALYZER,
                    target_file=relative,
                    line=violation.get("line_no"),
                    excerpt=description,
                    reason=description,
                    evidence_ref=f"sqlfluff:{code}",
                    recommended_action="Review the SQL style violation and align with SQL best practices.",
                    verification_status=VERIFICATION_EXECUTED,
                )
            )
    return findings
