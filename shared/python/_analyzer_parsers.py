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
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_EXTERNAL_ANALYZER, VERIFICATION_EXECUTED,
    )



_RUFF_PREFIX_TO_CI: dict[str, str] = {
    "F":   "CI-07",  # pyflakes — unused imports, dead names
    "UP":  "CI-07",  # pyupgrade — deprecated / obsolete patterns
    "ERA": "CI-07",  # eradicate — commented-out dead code
    "I":   "CI-13",  # isort — import ordering / dependency surface
    "D":   "CI-15",  # pydocstyle — documentation rot
    "ANN": "CI-23",  # annotations — type contract drift
    "S":   "CI-14",  # bandit — security neglect
    "PT":  "CI-09",  # pytest style — test rot
    "DTZ": "CI-25",  # timezone-naive — nondeterminism
    "E":   "CI-02",  # pycodestyle style — spaghetti / readability
    "W":   "CI-02",
    "C":   "CI-02",  # mccabe complexity
    "N":   "CI-02",  # naming
    "SIM": "CI-02",  # simplify
    "PL":  "CI-02",  # pylint
    "B":   "CI-21",  # flake8-bugbear — e.g. B904 broken exception chain (raise without `from e`)
    "TRY": "CI-21",  # flake8-tryceratops — e.g. TRY400 missing logging.exception
    "BLE": "CI-21",  # flake8-blind-except — BLE001 broad except (same as native CI-21)
    "TD":  "CI-03",  # flake8-todos — patchwork markers (same as native CI-03)
    "FIX": "CI-03",  # flake8-fixme — patchwork markers
    "PLR": "CI-02",  # pylint refactor (complexity-ish) — default bucket
    "PLW": "CI-02",  # pylint warning — default bucket
    "PLC": "CI-02",
}


_RUFF_CODE_TO_CI: dict[str, str] = {
    "PLR0913": "CI-18",  # too-many-arguments -> data clump
    "PLW0603": "CI-26",  # global-statement -> race hazard
}


_ESLINT_RULE_PREFIX_MAP: tuple[tuple[str, str], ...] = (
    ("@typescript-eslint/", "CI-23"),
    ("import/",             "CI-13"),
    ("security/",          "CI-14"),
    ("no-unused",          "CI-07"),
    ("no-unreachable",     "CI-07"),
    ("no-empty",           "CI-21"),
    ("no-eval",            "CI-14"),
    ("no-new-func",        "CI-14"),
    ("no-implied-eval",    "CI-14"),
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


_RUFF_PREFIX_PATTERN = re.compile(r"^([A-Z]+)")


def _ruff_ci_id(code: str) -> str:
    if code in _RUFF_CODE_TO_CI:
        return _RUFF_CODE_TO_CI[code]
    m = _RUFF_PREFIX_PATTERN.match(code or "")
    if not m:
        return "CI-21"
    return _RUFF_PREFIX_TO_CI.get(m.group(1), "CI-21")


def _ruff_severity(code: str) -> str:
    m = _RUFF_PREFIX_PATTERN.match(code or "")
    return "high" if m and m.group(1) == "S" else "medium"


def _pyflakes_ci_id(message: str) -> str:
    msg = message.lower()
    if "imported but unused" in msg or "redefinition of unused" in msg or "assigned to but never used" in msg:
        return "CI-07"
    if "undefined name" in msg:
        return "CI-21"
    return "CI-07"


def _eslint_ci_id(rule_id: str | None) -> str:
    if not rule_id:
        return "CI-02"
    for prefix, ci_id in _ESLINT_RULE_PREFIX_MAP:
        if rule_id.startswith(prefix):
            return ci_id
    return "CI-02"


_TSC_LINE_PATTERN = re.compile(r"(.+?)\((\d+),(\d+)\):\s*(?:error|warning)\s*(TS\d+):\s*(.+)")


def _shellcheck_ci_id(level: str) -> str:
    return "CI-21" if level in ("error", "warning") else "CI-02"


def _gitleaks_findings(report_text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    payload = json.loads(report_text or "[]")
    if not isinstance(payload, list):
        return findings
    for item in payload:
        if not isinstance(item, dict):
            continue
        rule = item.get("RuleID") or item.get("Description") or "secret"
        filename = item.get("File", "")
        try:
            relative = Path(filename).resolve().relative_to(target_root.resolve()).as_posix()
        except (ValueError, OSError):
            relative = Path(filename).as_posix() if filename else ""
        line = item.get("StartLine") or 1
        findings.append(
            build_finding(
                finding_id=f"F-EXT-{next_id + len(findings):04d}",
                ci_id="CI-14",
                signal="EXT_GITLEAKS",
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
                target_file=relative,
                line=int(line) if isinstance(line, int) else 1,
                excerpt=str(rule),
                reason=f"gitleaks flagged a committed secret ({rule}); rotate it and move it to a secret store.",
                evidence_ref=f"gitleaks:{rule}",
                recommended_action="Rotate the exposed credential and load it from an environment or secret manager.",
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings
