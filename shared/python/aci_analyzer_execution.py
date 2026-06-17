#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""External-analyzer execution helpers for ACI.

Subprocess isolation rules (T49):
- shell=False is always enforced; no shell expansion of analyzer arguments.
- Analyzers inherit the parent environment (PATH, PYTHONPATH) — required for
  virtual-environment-local executables to resolve correctly.
- stdout and stderr are captured in memory; each is truncated to
  ANALYZER_MAX_OUTPUT_CHARS characters to prevent runaway output from
  exhausting memory (subprocess.run with text=True returns str, not bytes).
- Version probes time out after VERSION_PROBE_TIMEOUT_SECONDS.
- Analyzer invocations time out after ANALYZER_TIMEOUT_SECONDS.
- On timeout the partial output (if any) is captured and the run is recorded
  with runtime_state="timeout"; the calling gate decides whether to fail.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast
import json
import re
import subprocess
from shutil import which

try:
    from .aci_analyzers import ANALYZER_CATALOG
    from .aci_findings import AciFinding, build_finding, LANE_EXTERNAL_ANALYZER, VERIFICATION_EXECUTED
    from .aci_profile_catalog import profile_catalog
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_analyzers import ANALYZER_CATALOG
    from aci_findings import AciFinding, build_finding, LANE_EXTERNAL_ANALYZER, VERIFICATION_EXECUTED
    from aci_profile_catalog import profile_catalog


ANALYZER_EXECUTION_SUPPORT_LEVELS: dict[str, str] = {
    "execution-ready": (
        "The common shelf can check executable visibility, attempt a version probe, and run a bounded invocation "
        "against a target directory for supported analyzers."
    ),
}

VERSION_PROBE_TIMEOUT_SECONDS: int = 10
ANALYZER_TIMEOUT_SECONDS: int = 30
ANALYZER_MAX_OUTPUT_CHARS: int = 10 * 1024 * 1024  # 10 M chars per stream (≈10 MB for ASCII output)

MINIMUM_ANALYZER_VERSIONS: dict[str, tuple[int, ...]] = {
    "ruff": (0, 1, 0),
    "pyflakes": (3, 0, 0),
    "mypy": (1, 0, 0),
    "pytest": (7, 0, 0),
    "eslint": (8, 0, 0),
    "shellcheck": (0, 7, 0),
    "sqlfluff": (2, 0, 0),
}

VERSION_PATTERN = re.compile(r"(\d+)\.(\d+)\.(\d+)")


@dataclass(frozen=True)
class AnalyzerReadiness:
    analyzer_id: str
    executable_path: str | None
    availability_state: str
    version_text: str | None
    version_ok: bool
    minimum_version: str | None
    execution_support_level: str = "execution-ready"

    def as_dict(self) -> dict[str, object]:
        return {
            "analyzer_id": self.analyzer_id,
            "executable_path": self.executable_path,
            "availability_state": self.availability_state,
            "version_text": self.version_text,
            "version_ok": self.version_ok,
            "minimum_version": self.minimum_version,
            "execution_support_level": self.execution_support_level,
        }


@dataclass(frozen=True)
class AnalyzerRunResult:
    analyzer_id: str
    ok: bool
    exit_code: int | None
    runtime_state: str
    stdout: str
    stderr: str
    findings: tuple[AciFinding, ...]
    skipped_source_file_count: int = 0

    def as_dict(self) -> dict[str, object]:
        return {
            "analyzer_id": self.analyzer_id,
            "ok": self.ok,
            "exit_code": self.exit_code,
            "runtime_state": self.runtime_state,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "finding_count": len(self.findings),
            "skipped_source_file_count": self.skipped_source_file_count,
        }


def _minimum_version_text(analyzer_id: str) -> str | None:
    version = MINIMUM_ANALYZER_VERSIONS.get(analyzer_id)
    if version is None:
        return None
    return ".".join(str(part) for part in version)


def _parse_version(version_text: str | None) -> tuple[int, ...] | None:
    if not version_text:
        return None
    match = VERSION_PATTERN.search(version_text)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def _version_probe_command(analyzer_id: str) -> list[str]:
    return [analyzer_id, "--version"]


def _probe_version(analyzer_id: str, executable_path: str) -> tuple[str | None, bool]:
    try:
        completed = subprocess.run(
            _version_probe_command(analyzer_id),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=VERSION_PROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, False
    version_text = (completed.stdout or completed.stderr).strip() or None
    minimum = MINIMUM_ANALYZER_VERSIONS.get(analyzer_id)
    actual = _parse_version(version_text)
    if minimum is None:
        return version_text, completed.returncode == 0
    return version_text, completed.returncode == 0 and actual is not None and actual >= minimum


def _readiness_for(entry_analyzer_id: str) -> AnalyzerReadiness:
    executable_path = which(entry_analyzer_id)
    if not executable_path:
        return AnalyzerReadiness(
            analyzer_id=entry_analyzer_id,
            executable_path=None,
            availability_state="not-installed",
            version_text=None,
            version_ok=False,
            minimum_version=_minimum_version_text(entry_analyzer_id),
        )
    version_text, version_ok = _probe_version(entry_analyzer_id, executable_path)
    availability_state = "ready" if version_ok else "version-or-runtime-problem"
    return AnalyzerReadiness(
        analyzer_id=entry_analyzer_id,
        executable_path=executable_path,
        availability_state=availability_state,
        version_text=version_text,
        version_ok=version_ok,
        minimum_version=_minimum_version_text(entry_analyzer_id),
    )


def analyzer_availability() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for entry in ANALYZER_CATALOG:
        readiness = _readiness_for(entry.analyzer_id)
        rows.append(
            readiness.as_dict()
            | {
                "referenced_by_profiles": entry.referenced_by_profiles,
                "ownership_boundary": (
                    "The common shelf checks executable visibility, version readiness, and bounded invocation support. "
                    "Project-local flags and deeper repository tuning still belong downstream."
                ),
            }
        )
    return rows


def profile_execution_plan() -> list[dict[str, object]]:
    readiness_map = {entry["analyzer_id"]: entry for entry in analyzer_availability()}
    rows: list[dict[str, object]] = []
    for entry in profile_catalog():
        analyzers = cast("list[str]", entry["default_external_analyzers"])
        rows.append(
            {
                "profile_id": entry["profile_id"],
                "enabled_lanes": entry["enabled_lanes"],
                "default_external_analyzers": analyzers,
                "execution_support_level": "execution-ready",
                "readiness_summary": {
                    analyzer_id: readiness_map[analyzer_id]["availability_state"]
                    for analyzer_id in analyzers
                },
                "execution_plan": (
                    "Use the common profile defaults as a bounded runtime surface: verify analyzer readiness, then run "
                    "supported analyzers against the chosen target directory."
                ),
                "ownership_boundary": (
                    "The common shelf can execute bounded analyzer defaults. Repository-specific rule tuning remains local."
                ),
            }
        )
    return rows


def analyzer_execution_support_levels() -> dict[str, str]:
    return dict(ANALYZER_EXECUTION_SUPPORT_LEVELS)


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

# Specific ruff codes whose category is a different native CI-ID than their
# prefix bucket. Checked before the prefix lookup so native/external dedup lines
# up (see _deduplicate_findings in aci_scan).
_RUFF_CODE_TO_CI: dict[str, str] = {
    "PLR0913": "CI-18",  # too-many-arguments -> data clump
    "PLW0603": "CI-26",  # global-statement -> race hazard
}

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


def _ruff_command(target_root: Path) -> list[str]:
    return ["ruff", "check", str(target_root), "--output-format", "json"]


def _pyflakes_command(target_root: Path) -> list[str]:
    return ["pyflakes", str(target_root)]


_PYTHON_ANALYZER_SKIP_SEGMENTS: frozenset[str] = frozenset({
    ".git", "__pycache__", ".venv", "venv", "env", "node_modules", "dist", ".tox",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "aci.egg-info",
    ".claude", "archive", "common", "workspace",
})


def _find_python_files(target_root: Path) -> list[str]:
    return sorted(
        str(p)
        for p in target_root.rglob("*.py")
        if p.is_file() and not any(seg in _PYTHON_ANALYZER_SKIP_SEGMENTS for seg in p.parts)
    )


def _mypy_command(target_root: Path, python_files: list[str]) -> list[str]:
    command = [
        "mypy",
        "--hide-error-context",
        "--no-color-output",
        "--show-column-numbers",
        "--no-error-summary",
    ]
    workspace_dir = target_root / "workspace"
    if workspace_dir.is_dir():
        command.extend(["--cache-dir", str(workspace_dir / ".aci-mypy-cache")])
    command.extend(python_files)
    return command


def _pytest_command(target_root: Path) -> list[str]:
    command = ["pytest", "-q", "-p", "no:cacheprovider"]
    workspace_dir = target_root / "workspace"
    if workspace_dir.is_dir():
        command.extend(["--basetemp", str(workspace_dir / ".aci-pytest-tmp")])
    command.append(str(target_root))
    return command


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


def _eslint_ci_id(rule_id: str | None) -> str:
    if not rule_id:
        return "CI-02"
    for prefix, ci_id in _ESLINT_RULE_PREFIX_MAP:
        if rule_id.startswith(prefix):
            return ci_id
    return "CI-02"


def _eslint_command(target_root: Path) -> list[str]:
    return ["eslint", "--format", "json", str(target_root)]


_TSC_LINE_PATTERN = re.compile(r"(.+?)\((\d+),(\d+)\):\s*(?:error|warning)\s*(TS\d+):\s*(.+)")


def _find_tsconfig(target_root: Path) -> Path | None:
    tsconfig = target_root / "tsconfig.json"
    return tsconfig if tsconfig.is_file() else None


def _tsc_command(tsconfig_path: Path) -> list[str]:
    return ["tsc", "--noEmit", "--pretty", "false", "-p", str(tsconfig_path)]


_SHELLCHECK_SKIP_SEGMENTS: frozenset[str] = frozenset({
    ".git", "__pycache__", ".venv", "venv", "env", "node_modules", "dist", ".tox",
})


def _shellcheck_ci_id(level: str) -> str:
    return "CI-21" if level in ("error", "warning") else "CI-02"


def _find_shell_files(target_root: Path) -> list[str]:
    return sorted(
        str(p)
        for p in target_root.rglob("*")
        if p.suffix in (".sh", ".bash")
        and p.is_file()
        and not any(seg in _SHELLCHECK_SKIP_SEGMENTS for seg in p.parts)
    )


def _shellcheck_command(shell_files: list[str]) -> list[str]:
    return ["shellcheck", "--format", "json"] + shell_files[:200]


def _sqlfluff_command(target_root: Path) -> list[str]:
    return ["sqlfluff", "lint", "--format", "json", str(target_root)]


def _analyzer_command(analyzer_id: str, target_root: Path) -> list[str] | None:
    """Return the subprocess command for directory-level analyzers.

    tsc and shellcheck require source-file discovery before the command can be
    built; they are handled separately in run_analyzer and must NOT appear here.
    """
    if analyzer_id == "ruff":
        return _ruff_command(target_root)
    if analyzer_id == "pyflakes":
        return _pyflakes_command(target_root)
    if analyzer_id == "pytest":
        return _pytest_command(target_root)
    if analyzer_id == "eslint":
        return _eslint_command(target_root)
    if analyzer_id == "sqlfluff":
        return _sqlfluff_command(target_root)
    return None


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


def _resolve_analyzer_command(analyzer_id: str, target_root: Path) -> tuple[list[str] | None, int, bool]:
    skipped_source_count = 0
    if analyzer_id == "tsc":
        tsconfig = _find_tsconfig(target_root)
        return (_tsc_command(tsconfig) if tsconfig else None, skipped_source_count, True)
    if analyzer_id == "mypy":
        python_files = _find_python_files(target_root)
        return (_mypy_command(target_root, python_files) if python_files else None, skipped_source_count, True)
    if analyzer_id == "shellcheck":
        shell_files = _find_shell_files(target_root)
        skipped_source_count = max(0, len(shell_files) - 200)
        return (_shellcheck_command(shell_files) if shell_files else None, skipped_source_count, True)
    return _analyzer_command(analyzer_id, target_root), skipped_source_count, False


def _no_source_result(analyzer_id: str, no_source: bool) -> AnalyzerRunResult:
    return AnalyzerRunResult(
        analyzer_id=analyzer_id,
        ok=False,
        exit_code=None,
        runtime_state="no-applicable-source" if no_source else "unsupported-in-common-shelf",
        stdout="",
        stderr=(
            "No applicable source files or configuration found for this analyzer."
            if no_source
            else "Analyzer is cataloged but not yet runnable from the common shelf."
        ),
        findings=(),
    )


def _execute_analyzer_command(analyzer_id: str, command: list[str]) -> tuple[subprocess.CompletedProcess[str] | None, AnalyzerRunResult | None]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=ANALYZER_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return None, AnalyzerRunResult(
            analyzer_id=analyzer_id,
            ok=False,
            exit_code=None,
            runtime_state="timeout",
            stdout=exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
            stderr=exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
            findings=(),
        )
    except OSError as exc:
        return None, AnalyzerRunResult(
            analyzer_id=analyzer_id,
            ok=False,
            exit_code=None,
            runtime_state="spawn-failure",
            stdout="",
            stderr=str(exc),
            findings=(),
        )
    return completed, None


def _parse_analyzer_findings(
    analyzer_id: str,
    stdout: str,
    stderr: str,
    target_root: Path,
    next_id: int,
) -> tuple[list[AciFinding], bool]:
    try:
        if analyzer_id == "ruff":
            return _ruff_findings(stdout, target_root, next_id), True
        if analyzer_id == "pyflakes":
            return _pyflakes_findings(stdout, stderr, target_root, next_id), True
        if analyzer_id == "mypy":
            return _mypy_findings(stdout, stderr, target_root, next_id), True
        if analyzer_id == "pytest":
            return _pytest_findings(stdout, stderr, next_id), True
        if analyzer_id == "eslint":
            return _eslint_findings(stdout, target_root, next_id), True
        if analyzer_id == "tsc":
            return _tsc_findings(stdout, stderr, target_root, next_id), True
        if analyzer_id == "shellcheck":
            return _shellcheck_findings(stdout, target_root, next_id), True
        if analyzer_id == "sqlfluff":
            return _sqlfluff_findings(stdout, target_root, next_id), True
    except json.JSONDecodeError:
        return [], False
    return [], True


def _evaluate_analyzer_outcome(analyzer_id: str, exit_code: int, parse_ok: bool) -> tuple[bool, str]:
    ok_exit_codes = {0, 1}
    runtime_state = VERIFICATION_EXECUTED
    if analyzer_id == "pytest" and exit_code == 5:
        ok_exit_codes.add(5)
        runtime_state = "no-tests-collected"
    exit_ok = exit_code in ok_exit_codes
    ok = exit_ok and parse_ok
    if not ok:
        runtime_state = "parse-failure" if exit_ok and not parse_ok else "runtime-failure"
    return ok, runtime_state


def run_analyzer(analyzer_id: str, target_root: Path, next_id: int) -> AnalyzerRunResult:
    readiness = _readiness_for(analyzer_id)
    if readiness.availability_state != "ready":
        return AnalyzerRunResult(
            analyzer_id=analyzer_id,
            ok=False,
            exit_code=None,
            runtime_state=readiness.availability_state,
            stdout="",
            stderr=readiness.version_text or "",
            findings=(),
        )
    command, skipped_source_count, no_source = _resolve_analyzer_command(analyzer_id, target_root)

    if command is None:
        return _no_source_result(analyzer_id, no_source)
    completed, error_result = _execute_analyzer_command(analyzer_id, command)
    if error_result is not None or completed is None:
        return cast(AnalyzerRunResult, error_result)

    stdout = completed.stdout[:ANALYZER_MAX_OUTPUT_CHARS]
    stderr = completed.stderr[:ANALYZER_MAX_OUTPUT_CHARS]
    findings, parse_ok = _parse_analyzer_findings(analyzer_id, stdout, stderr, target_root, next_id)
    ok, runtime_state = _evaluate_analyzer_outcome(analyzer_id, completed.returncode, parse_ok)
    return AnalyzerRunResult(
        analyzer_id=analyzer_id,
        ok=ok,
        exit_code=completed.returncode,
        runtime_state=runtime_state,
        stdout=stdout,
        stderr=stderr,
        findings=tuple(findings),
        skipped_source_file_count=skipped_source_count,
    )
