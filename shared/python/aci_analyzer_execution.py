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
    "availability-check-only": (
        "The common shelf can check executable visibility and version readiness, but bounded invocation and finding "
        "normalization are intentionally not claimed. Repository-local setup and execution remain downstream."
    ),
}

VERSION_PROBE_TIMEOUT_SECONDS: int = 10
ANALYZER_TIMEOUT_SECONDS: int = 60
ANALYZER_MAX_OUTPUT_CHARS: int = 10 * 1024 * 1024  # 10 M chars per stream (≈10 MB for ASCII output)

MINIMUM_ANALYZER_VERSIONS: dict[str, tuple[int, ...]] = {
    "gitleaks": (8, 0, 0),
    "osv-scanner": (1, 0, 0),
    "trivy": (0, 40, 0),
    "semgrep": (1, 0, 0),
    "ruff": (0, 1, 0),
    "pyflakes": (3, 0, 0),
    "mypy": (1, 0, 0),
    "pytest": (7, 0, 0),
    "eslint": (8, 0, 0),
    "shellcheck": (0, 7, 0),
    "sqlfluff": (2, 0, 0),
}

VERSION_PATTERN = re.compile(r"(\d+)\.(\d+)\.(\d+)")
_CATALOG_DEFAULT_POLICY_BY_ANALYZER: dict[str, str] = {
    entry.analyzer_id: entry.support_level for entry in ANALYZER_CATALOG
}
_ANALYZER_PURPOSE_BY_ID: dict[str, str] = {
    entry.analyzer_id: entry.purpose for entry in ANALYZER_CATALOG
}
_ANALYZER_CATEGORY_BY_ID: dict[str, str] = {
    entry.analyzer_id: entry.category for entry in ANALYZER_CATALOG
}
_ANALYZER_TYPICAL_CI_IDS_BY_ID: dict[str, tuple[str, ...]] = {
    entry.analyzer_id: entry.typical_ci_ids for entry in ANALYZER_CATALOG
}
_ANALYZER_OWNERSHIP_BOUNDARY_BY_ID: dict[str, str] = {
    entry.analyzer_id: entry.ownership_boundary for entry in ANALYZER_CATALOG
}
_EXECUTION_READY_ANALYZERS: frozenset[str] = frozenset({
    "semgrep",
    "ruff",
    "pyflakes",
    "mypy",
    "pytest",
    "eslint",
    "tsc",
    "shellcheck",
    "sqlfluff",
    # Deep dependency/vulnerability scanners with a single JSON-on-stdout model.
    # gitleaks (file-report output) and codeql (requires a prebuilt database) do
    # not fit the bounded single-invocation contract and stay availability-only.
    "osv-scanner",
    "trivy",
})
_ANALYZER_VERSION_POLICY: dict[str, dict[str, str]] = {
    "codeql": {
        "policy": "repo-local-pin-required",
        "ecosystem": "binary",
        "install_spec": "Install the CodeQL CLI and pin a repository-local release before enabling it.",
    },
    "gitleaks": {
        "policy": "repo-local-pin-required",
        "ecosystem": "binary",
        "install_spec": "Install gitleaks and pin an explicit repository-local version before enabling it.",
    },
    "osv-scanner": {
        "policy": "repo-local-pin-required",
        "ecosystem": "binary",
        "install_spec": "Install osv-scanner and pin an explicit repository-local version before enabling it.",
    },
    "trivy": {
        "policy": "repo-local-pin-required",
        "ecosystem": "binary",
        "install_spec": "Install Trivy and pin an explicit repository-local version before enabling it.",
    },
    "semgrep": {
        "policy": "minimum-only",
        "ecosystem": "pip",
        "install_spec": "python -m pip install \"semgrep>=1.0.0\"",
    },
    "ruff": {
        "policy": "aci-maintained-pin",
        "ecosystem": "pip",
        "tested_version": "0.4.8",
        "install_spec": "ruff==0.4.8",
    },
    "pyflakes": {
        "policy": "aci-maintained-pin",
        "ecosystem": "pip",
        "tested_version": "3.2.0",
        "install_spec": "pyflakes==3.2.0",
    },
    "mypy": {
        "policy": "aci-maintained-pin",
        "ecosystem": "pip",
        "tested_version": "1.10.0",
        "install_spec": "mypy==1.10.0",
    },
    "pytest": {
        "policy": "aci-maintained-pin",
        "ecosystem": "pip",
        "tested_version": "9.0.3",
        "install_spec": "pytest==9.0.3",
    },
    "eslint": {
        "policy": "repo-local-pin-required",
        "ecosystem": "npm",
        "install_spec": "npm install --save-dev eslint@<pin>",
    },
    "tsc": {
        "policy": "repo-local-pin-required",
        "ecosystem": "npm",
        "install_spec": "npm install --save-dev typescript@<pin>",
    },
    "shellcheck": {
        "policy": "repo-local-pin-required",
        "ecosystem": "binary",
        "install_spec": "Install a pinned ShellCheck release from your platform package manager or upstream archive.",
    },
    "sqlfluff": {
        "policy": "minimum-only",
        "ecosystem": "pip",
        "install_spec": "python -m pip install \"sqlfluff>=2.0.0\"",
    },
}
_ANALYZER_SETUP_HINTS: dict[str, str] = {
    "codeql": "Requires a repository-local CodeQL database and query pack; the common shelf only reports availability.",
    "gitleaks": "Optional secret-scanning lane; add a repository-local config and allowlist policy before enabling it.",
    "osv-scanner": "Optional dependency audit lane; choose the manifest or lockfile scope in the consuming repository.",
    "trivy": "Optional dependency, container, and IaC audit lane; define repo-local targets and policy thresholds first.",
    "semgrep": "Install Semgrep if this environment should run the bundled baseline rule pack.",
    "ruff": "Install the pinned maintainer analyzer set with `python -m pip install -r requirements-dev-analyzers.txt`.",
    "pyflakes": "Install the pinned maintainer analyzer set with `python -m pip install -r requirements-dev-analyzers.txt`.",
    "mypy": "Install the pinned maintainer analyzer set with `python -m pip install -r requirements-dev-analyzers.txt`.",
    "pytest": "Install the pinned maintainer analyzer set with `python -m pip install -r requirements-dev-analyzers.txt`.",
    "eslint": "Install ESLint in the target repository and keep its config/plugins pinned locally.",
    "tsc": "Install TypeScript in the target repository and keep `typescript` pinned next to `tsconfig.json`.",
    "shellcheck": "Install ShellCheck from a pinned OS package or upstream release before expecting shell evidence.",
    "sqlfluff": "Install sqlfluff if SQL lint evidence is required in this environment.",
}
_ANALYZER_REMEDIATION_HINTS: dict[str, str] = {
    "not-installed": "Install the analyzer if this lane is required here, or keep it out of the profile defaults for this environment.",
    "version-or-runtime-problem": "Align the analyzer version with the advertised minimum or pinned maintainer spec, then retry the readiness check.",
    "downstream-setup-required": "The analyzer is visible, but the common shelf does not claim runnable wiring; finish repository-local setup before relying on it.",
}


@dataclass(frozen=True)
class AnalyzerReadiness:
    analyzer_id: str
    executable_path: str | None
    availability_state: str
    version_text: str | None
    version_ok: bool
    minimum_version: str | None
    availability_check: str = "path-and-version-probe"
    tested_version: str | None = None
    version_policy: str = "minimum-only"
    install_spec: str | None = None
    setup_hint: str = ""
    remediation_hint: str = ""
    default_policy: str = "opt-in"
    execution_support_level: str = "execution-ready"

    def as_dict(self) -> dict[str, object]:
        return {
            "analyzer_id": self.analyzer_id,
            "executable_path": self.executable_path,
            "availability_check": self.availability_check,
            "availability_state": self.availability_state,
            "version_text": self.version_text,
            "version_ok": self.version_ok,
            "minimum_version": self.minimum_version,
            "tested_version": self.tested_version,
            "version_policy": self.version_policy,
            "install_spec": self.install_spec,
            "setup_hint": self.setup_hint,
            "remediation_hint": self.remediation_hint,
            "default_policy": self.default_policy,
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


def analyzer_version_policy() -> dict[str, dict[str, str]]:
    return {analyzer_id: dict(policy) for analyzer_id, policy in _ANALYZER_VERSION_POLICY.items()}


def _version_policy_for(analyzer_id: str) -> dict[str, str]:
    return dict(_ANALYZER_VERSION_POLICY.get(analyzer_id, {}))


def _execution_support_level_for(analyzer_id: str) -> str:
    if analyzer_id in _EXECUTION_READY_ANALYZERS:
        return "execution-ready"
    return "availability-check-only"


def _setup_hint_for(analyzer_id: str) -> str:
    return _ANALYZER_SETUP_HINTS.get(analyzer_id, "Install and configure this analyzer in the local environment before depending on its evidence.")


def _remediation_hint_for(state: str) -> str:
    return _ANALYZER_REMEDIATION_HINTS.get(state, "Inspect the analyzer environment and retry once the runtime surface is stable.")


def _parse_version(version_text: str | None) -> tuple[int, ...] | None:
    if not version_text:
        return None
    match = VERSION_PATTERN.search(version_text)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def _version_probe_command(analyzer_id: str) -> list[str]:
    if analyzer_id == "codeql":
        return [analyzer_id, "version"]
    if analyzer_id == "gitleaks":
        return [analyzer_id, "version"]
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
    execution_support_level = _execution_support_level_for(entry_analyzer_id)
    default_policy = _CATALOG_DEFAULT_POLICY_BY_ANALYZER.get(entry_analyzer_id, "opt-in")
    version_policy = _version_policy_for(entry_analyzer_id)
    tested_version = version_policy.get("tested_version")
    install_spec = version_policy.get("install_spec")
    executable_path = which(entry_analyzer_id)
    if not executable_path:
        availability_state = "not-installed"
        return AnalyzerReadiness(
            analyzer_id=entry_analyzer_id,
            executable_path=None,
            availability_check="path-and-version-probe",
            availability_state=availability_state,
            version_text=None,
            version_ok=False,
            minimum_version=_minimum_version_text(entry_analyzer_id),
            tested_version=tested_version,
            version_policy=version_policy.get("policy", "minimum-only"),
            install_spec=install_spec,
            setup_hint=_setup_hint_for(entry_analyzer_id),
            remediation_hint=_remediation_hint_for(availability_state),
            default_policy=default_policy,
            execution_support_level=execution_support_level,
        )
    version_text, version_ok = _probe_version(entry_analyzer_id, executable_path)
    if execution_support_level == "availability-check-only":
        availability_state = "downstream-setup-required" if version_ok else "version-or-runtime-problem"
    else:
        availability_state = "ready" if version_ok else "version-or-runtime-problem"
    return AnalyzerReadiness(
        analyzer_id=entry_analyzer_id,
        executable_path=executable_path,
        availability_check="path-and-version-probe",
        availability_state=availability_state,
        version_text=version_text,
        version_ok=version_ok,
        minimum_version=_minimum_version_text(entry_analyzer_id),
        tested_version=tested_version,
        version_policy=version_policy.get("policy", "minimum-only"),
        install_spec=install_spec,
        setup_hint=_setup_hint_for(entry_analyzer_id),
        remediation_hint=_remediation_hint_for(availability_state),
        default_policy=default_policy,
        execution_support_level=execution_support_level,
    )


def analyzer_availability() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for entry in ANALYZER_CATALOG:
        readiness = _readiness_for(entry.analyzer_id)
        rows.append(
            readiness.as_dict()
            | {
                "category": _ANALYZER_CATEGORY_BY_ID.get(entry.analyzer_id, ""),
                "purpose": _ANALYZER_PURPOSE_BY_ID.get(entry.analyzer_id, ""),
                "support_level": entry.support_level,
                "referenced_by_profiles": entry.referenced_by_profiles,
                "typical_ci_ids": _ANALYZER_TYPICAL_CI_IDS_BY_ID.get(entry.analyzer_id, ()),
                "ownership_boundary": _ANALYZER_OWNERSHIP_BOUNDARY_BY_ID.get(entry.analyzer_id, ""),
            }
        )
    return rows


def profile_execution_plan() -> list[dict[str, object]]:
    readiness_map = {entry["analyzer_id"]: entry for entry in analyzer_availability()}
    opt_in_analyzers = [
        entry.analyzer_id
        for entry in ANALYZER_CATALOG
        if entry.support_level == "opt-in"
    ]
    rows: list[dict[str, object]] = []
    for entry in profile_catalog():
        analyzers = cast("list[str]", entry["default_external_analyzers"])
        execution_support_level = "execution-ready"
        if any(
            readiness_map[analyzer_id]["execution_support_level"] != "execution-ready"
            for analyzer_id in analyzers
        ):
            execution_support_level = "availability-check-only"
        rows.append(
            {
                "profile_id": entry["profile_id"],
                "enabled_lanes": entry["enabled_lanes"],
                "default_external_analyzers": analyzers,
                "optional_opt_in_analyzers": opt_in_analyzers,
                "execution_support_level": execution_support_level,
                "readiness_summary": {
                    analyzer_id: readiness_map[analyzer_id]["availability_state"]
                    for analyzer_id in analyzers
                },
                "execution_plan": (
                    "Use the common profile defaults as a bounded runtime surface: verify analyzer readiness, then run "
                    "supported analyzers against the chosen target directory. Optional security analyzers remain "
                    "opt-in and are not auto-selected by these defaults."
                ),
                "ownership_boundary": (
                    "The common shelf can execute bounded analyzer defaults. Repository-specific rule tuning remains local."
                ),
            }
        )
    return rows


def analyzer_execution_support_levels() -> dict[str, str]:
    return dict(ANALYZER_EXECUTION_SUPPORT_LEVELS)



# Specific ruff codes whose category is a different native CI-ID than their
# prefix bucket. Checked before the prefix lookup so native/external dedup lines
# up (see _deduplicate_findings in aci_scan).









try:
    from ._analyzer_commands import (
        _analyzer_command, _find_python_files, _find_shell_files, _find_tsconfig,
        _mypy_command, _semgrep_command, _shellcheck_command, _tsc_command,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from _analyzer_commands import (  # type: ignore[no-redef]
        _analyzer_command, _find_python_files, _find_shell_files, _find_tsconfig,
        _mypy_command, _semgrep_command, _shellcheck_command, _tsc_command,
    )

















































def _external_relative(filename: str, target_root: Path) -> str:
    path = Path(filename)
    try:
        return path.resolve().relative_to(target_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix() if filename else ""


def _osv_scanner_findings(stdout: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    payload = json.loads(stdout or "{}")
    for result in payload.get("results", []) or []:
        source_path = (result.get("source") or {}).get("path", "")
        relative = _external_relative(source_path, target_root)
        for package in result.get("packages", []) or []:
            info = package.get("package", {}) or {}
            name = info.get("name", "?")
            version = info.get("version", "?")
            for vuln in package.get("vulnerabilities", []) or []:
                vuln_id = vuln.get("id", "unknown")
                summary = vuln.get("summary") or vuln.get("details") or vuln_id
                findings.append(
                    build_finding(
                        finding_id=f"F-EXT-{next_id + len(findings):04d}",
                        ci_id="CI-14",
                        signal="EXT_OSV_SCANNER",
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
                        line=1,
                        excerpt=f"{name} {version}: {vuln_id}",
                        reason=f"{name} {version} is affected by {vuln_id}: {str(summary)[:160]}",
                        evidence_ref=f"osv-scanner:{vuln_id}",
                        recommended_action="Upgrade or patch the dependency to a version without the reported advisory.",
                        verification_status=VERIFICATION_EXECUTED,
                    )
                )
    return findings


def _trivy_findings(stdout: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    payload = json.loads(stdout or "{}")
    for result in payload.get("Results", []) or []:
        relative = _external_relative(result.get("Target", ""), target_root)
        for vuln in result.get("Vulnerabilities", []) or []:
            vuln_id = vuln.get("VulnerabilityID", "unknown")
            pkg_name = vuln.get("PkgName", "?")
            version = vuln.get("InstalledVersion", "?")
            raw_severity = (vuln.get("Severity") or "MEDIUM").lower()
            severity = "high" if raw_severity in ("high", "critical") else "medium"
            title = vuln.get("Title") or vuln.get("Description") or vuln_id
            findings.append(
                build_finding(
                    finding_id=f"F-EXT-{next_id + len(findings):04d}",
                    ci_id="CI-14",
                    signal="EXT_TRIVY",
                    severity=severity,
                    confidence="medium",
                    actor_label=LANE_EXTERNAL_ANALYZER,
                    triage_state="review-first",
                    priority="P1" if severity == "high" else "P2",
                    fixability="owner-decision",
                    baseline_status="new",
                    waiver_status="none",
                    lifecycle_state="open",
                    owner_lane=LANE_EXTERNAL_ANALYZER,
                    target_file=relative,
                    line=1,
                    excerpt=f"{pkg_name} {version}: {vuln_id}",
                    reason=f"{pkg_name} {version} is affected by {vuln_id}: {str(title)[:160]}",
                    evidence_ref=f"trivy:{vuln_id}",
                    recommended_action="Upgrade the affected dependency or apply the vendor-provided fix.",
                    verification_status=VERIFICATION_EXECUTED,
                )
            )
    return findings




try:
    from ._analyzer_parsers import (
        _ruff_findings, _pyflakes_findings, _mypy_findings, _pytest_findings,
        _eslint_findings, _semgrep_findings, _tsc_findings, _shellcheck_findings, _sqlfluff_findings,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from _analyzer_parsers import (  # type: ignore[no-redef]
        _ruff_findings, _pyflakes_findings, _mypy_findings, _pytest_findings,
        _eslint_findings, _semgrep_findings, _tsc_findings, _shellcheck_findings, _sqlfluff_findings,
    )


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
    if analyzer_id == "semgrep":
        return _semgrep_command(target_root), skipped_source_count, True
    if analyzer_id == "codeql":
        return None, skipped_source_count, False
    return _analyzer_command(analyzer_id, target_root), skipped_source_count, False


def _no_source_result(analyzer_id: str, no_source: bool) -> AnalyzerRunResult:
    return AnalyzerRunResult(
        analyzer_id=analyzer_id,
        ok=False,
        exit_code=None,
        runtime_state="no-applicable-source" if no_source else "downstream-setup-required",
        stdout="",
        stderr=(
            "No applicable source files or configuration found for this analyzer."
            if no_source
            else "Analyzer is cataloged, but runnable execution remains a downstream responsibility."
        ),
        findings=(),
    )


def _execute_analyzer_command(
    analyzer_id: str,
    command: list[str],
    *,
    cwd: Path,
) -> tuple[subprocess.CompletedProcess[str] | None, AnalyzerRunResult | None]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=ANALYZER_TIMEOUT_SECONDS,
            check=False,
            cwd=str(cwd),
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
        if analyzer_id == "semgrep":
            return _semgrep_findings(stdout, target_root, next_id), True
        if analyzer_id == "eslint":
            return _eslint_findings(stdout, target_root, next_id), True
        if analyzer_id == "tsc":
            return _tsc_findings(stdout, stderr, target_root, next_id), True
        if analyzer_id == "shellcheck":
            return _shellcheck_findings(stdout, target_root, next_id), True
        if analyzer_id == "sqlfluff":
            return _sqlfluff_findings(stdout, target_root, next_id), True
        if analyzer_id == "osv-scanner":
            return _osv_scanner_findings(stdout, target_root, next_id), True
        if analyzer_id == "trivy":
            return _trivy_findings(stdout, target_root, next_id), True
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
            stderr=readiness.version_text or readiness.remediation_hint,
            findings=(),
        )
    command, skipped_source_count, no_source = _resolve_analyzer_command(analyzer_id, target_root)

    if command is None:
        return _no_source_result(analyzer_id, no_source)
    completed, error_result = _execute_analyzer_command(analyzer_id, command, cwd=target_root)
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
