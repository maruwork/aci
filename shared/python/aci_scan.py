#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded real-target scan runtime for ACI.

Traversal and path normalization rules (T50):
- File discovery uses Path.rglob("*"), whose OS-level order is non-deterministic.
- Collected files are sorted by their POSIX-normalized relative path
  (forward-slash separated, case-sensitive) so scan order is identical across
  Windows and POSIX systems regardless of filesystem traversal order.
- Skipped-target entries are sorted by the same POSIX relative path so that
  the skipped_targets list in the report is also deterministic.
- All target_file values in findings and report fields use as_posix() via
  _relative_path() — backslash separators never appear in output.
- target_root is accepted as-is; callers are responsible for resolving symlinks
  in the root before passing it if absolute-path stability is required.

Scan safety guidance for untrusted targets (T51):
- All file access is read-only; ACI never writes to the target directory.
- Symlinks are skipped and never followed (symlink-skipped).
- Binary files are detected via null-byte probe and skipped (binary-skipped).
- Files exceeding DEFAULT_MAX_FILE_BYTES (1 MB) are skipped (max-file-size-exceeded).
- Only files with known text suffixes (.py, .md, .toml, ...) are processed.
- SyntaxError during AST parsing is caught per-file; malformed code cannot
  crash the scan process.
- The total number of collected files is capped at MAX_SCAN_FILE_COUNT; files
  beyond the cap are recorded as skipped (scan-file-count-limit-exceeded) so
  that adversarially large directory trees cannot exhaust memory or time.
- ACI does NOT execute or import any file it scans.
- ACI does NOT sandbox the target; operators scanning production system paths
  (e.g. / or C:\\) should use include_paths to restrict scope explicitly.

Artifact hygiene and generated-output boundaries (T52):
- ACI never writes to the target directory; all output goes to stdout or
  caller-specified paths (report files, SARIF files).
- No temporary files are created inside the target directory during a scan.
- Generated paths (virtual environments, build artifacts, caches) are skipped
  automatically via DEFAULT_GENERATED_PATH_SEGMENTS; the full list is recorded
  in scope_rules.generated_path_segments in every scan report.
- Downstream callers are responsible for managing the lifecycle of any report
  or SARIF files they write; ACI does not track, rotate, or delete them.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import replace
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
import re
import subprocess
from typing import cast, Protocol

ACI_TOOL_VERSION = "0.1.0"

try:
    from .detectors import PER_FILE_REGISTRY, CROSS_FILE_REGISTRY
    from .detectors._helpers import _relative_path
    from .aci_analyzer_execution import run_analyzer
    from .aci_domain_contract import CORE_ONLY_DOMAIN_ID
    from .aci_domain_loader import load_domain_rules
    from .aci_findings import (
        AciFinding, build_structure_finding,
        LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER, LANE_HUMAN_JUDGMENT,
        SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW,
        CONFIDENCE_MEDIUM,
    )
    from .aci_ignore import load_ignore_patterns
    from .aci_operations import (
        OperationsState,
        find_active_waiver,
        find_matching_suppression,
        find_resolved_baseline_entries,
        is_existing_baseline,
        load_operations_state,
    )
    from .aci_profile_catalog import PROFILE_ENABLED_LANES
    from .aci_profiles import (
        build_profile_signals, PROFILE_REQUIRES_TARGETED_SCOPE,
        PROFILE_QUICK_GATE, PROFILE_FULL, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW,
    )
    from .aci_signals import (
        STRUCTURE_SIGNALS as _STRUCTURE_SIGNALS,
        SIGNAL_SIDE_PROGRAM_LEAK,
        SAFE_SIDE_PROGRAM_PATTERN,
        compile_keyword_pattern,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from detectors import PER_FILE_REGISTRY, CROSS_FILE_REGISTRY  # type: ignore[no-redef]
    from detectors._helpers import _relative_path  # type: ignore[no-redef]
    from aci_analyzer_execution import run_analyzer
    from aci_domain_contract import CORE_ONLY_DOMAIN_ID
    from aci_domain_loader import load_domain_rules
    from aci_findings import (
        AciFinding, build_structure_finding,
        LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER, LANE_HUMAN_JUDGMENT,
        SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW,
        CONFIDENCE_MEDIUM,
    )
    from aci_ignore import load_ignore_patterns
    from aci_operations import (
        OperationsState,
        find_active_waiver,
        find_matching_suppression,
        find_resolved_baseline_entries,
        is_existing_baseline,
        load_operations_state,
    )
    from aci_profile_catalog import PROFILE_ENABLED_LANES
    from aci_profiles import (
        build_profile_signals, PROFILE_REQUIRES_TARGETED_SCOPE,
        PROFILE_QUICK_GATE, PROFILE_FULL, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW,
    )
    from aci_signals import (
        STRUCTURE_SIGNALS as _STRUCTURE_SIGNALS,
        SIGNAL_SIDE_PROGRAM_LEAK,
        SAFE_SIDE_PROGRAM_PATTERN,
        compile_keyword_pattern,
    )


TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".yml",
    ".yaml",
    ".json",
}
DEFAULT_MAX_FILE_BYTES = 1_000_000
MAX_SCAN_FILE_COUNT = 10_000
DEFAULT_GENERATED_PATH_SEGMENTS = {
    # Python interpreter and tool caches
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    # Version control
    ".git",
    # Build and distribution artifacts
    "build",
    "dist",
    "aci.egg-info",
    ".eggs",
    # Virtual environments
    ".venv",
    "venv",
    "env",
    # Test and coverage artifacts
    ".tox",
    "htmlcov",
    ".coverage",
    # Node / other ecosystems (common in full-stack repos)
    "node_modules",
    # Local tool state and session scratch space (non-canonical; never in distributed packages)
    ".claude",
    "workspace",
}

SEVERITY_RANK = {
    SEVERITY_LOW: 1,
    SEVERITY_MEDIUM: 2,
    SEVERITY_HIGH: 3,
    SEVERITY_CRITICAL: 4,
}


# CI-06 (Magic Number) helpers

# Profile signal catalog (wires build_profile_signals to the native detector set)
_NATIVE_HYGIENE_SIGNALS: tuple[str, ...] = (
    "CI02_SPAGHETTI_CODE",
    "CI02_LONG_FUNCTION",
    "CI04_GOD_CLASS",
    "CI03_TODO_HACK",
    "CI05_COPY_PASTE_CODE",
    "CI06_MAGIC_NUMBER",
    "CI12_POLTERGEIST",
    "CI14_PLAINTEXT_SECRET",
    "CI14_DYNAMIC_CODE_EXECUTION",
    "CI14_SUBPROCESS_SHELL_TRUE",
    "CI14_INSECURE_HTTP",
    "CI18_PARAMETER_CLUSTER",
    "CI20_SCATTERED_CONSTANT",
    "CI21_BROAD_EXCEPTION_SWALLOW",
    "CI21_SILENT_EXCEPTION_RETURN",
    "CI22_RESOURCE_CLEANUP_GAP",
    "CI23_CONTRACT_FIELD_DRIFT",
    "CI25_ENVIRONMENT_DRIFT",
    "CI26_RACE_HAZARD",
)
_EXTERNAL_EVIDENCE_SIGNALS: tuple[str, ...] = ("EXTERNAL_STATIC_ANALYSIS",)
_HUMAN_JUDGMENT_SIGNALS: tuple[str, ...] = ()

_PROFILE_SIGNALS: dict[str, tuple[str, ...]] = build_profile_signals(
    structure_signals=_STRUCTURE_SIGNALS,
    external_evidence_signals=_EXTERNAL_EVIDENCE_SIGNALS,
    human_judgment_signals=_HUMAN_JUDGMENT_SIGNALS,
    native_hygiene_signals=_NATIVE_HYGIENE_SIGNALS,
)


class PerFileDetector(Protocol):
    """Interface for single-file native detectors."""

    def __call__(
        self, path: Path, text: str, target_root: Path, next_id: int
    ) -> list[AciFinding]: ...


class CrossFileDetector(Protocol):
    """Interface for multi-file native detectors that need corpus context."""

    def __call__(
        self, paths: list[Path], root: Path, next_id: int
    ) -> list[AciFinding]: ...


@dataclass(frozen=True)
class ScanSession:
    target_root: Path
    profile_id: str
    domain_id: str
    operations: OperationsState
    include_paths: tuple[str, ...]
    exclude_paths: tuple[str, ...]
    severity_threshold: str
    fail_on_new_findings: bool
    fail_on_unreviewed_review_required: bool
    include_external_analyzers: bool
    fail_on_analyzer_errors: bool
    ignore_patterns: tuple[str, ...]
    diff_from: str | None = None


@dataclass(frozen=True)
class SkippedTarget:
    path: str
    reason: str


def _is_supported_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def _path_matches_filters(
    path: Path,
    target_root: Path,
    include_paths: tuple[str, ...],
    exclude_paths: tuple[str, ...],
) -> bool:
    relative = _relative_path(path, target_root)
    if include_paths and not any(
        relative == item or relative.startswith(f"{item.rstrip('/')}/") for item in include_paths
    ):
        return False
    if any(
        relative == item or relative.startswith(f"{item.rstrip('/')}/") for item in exclude_paths
    ):
        return False
    return True


def _is_binary_bytes(raw: bytes) -> bool:
    return b"\x00" in raw


def _is_generated_path(relative_path: str) -> bool:
    parts = set(relative_path.split("/"))
    return any(part in DEFAULT_GENERATED_PATH_SEGMENTS for part in parts)


def _git_changed_files(repo_root: Path, ref: str) -> frozenset[str]:
    """Return POSIX-relative paths of files changed since *ref* in *repo_root*.

    Runs ``git diff --name-only <ref> --`` so that only tracked-file changes are
    returned.  Raises ValueError with a descriptive message when git is not
    available, the repository is not found, or the ref is invalid.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", ref, "--"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise ValueError("git is not available on PATH; --diff-from requires a git installation") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"git diff timed out for ref {ref!r} in {repo_root}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or "no stderr"
        raise ValueError(f"git diff --name-only {ref!r} failed in {repo_root}: {detail}")
    return frozenset(line.strip() for line in result.stdout.splitlines() if line.strip())


def _iter_target_files(
    target_root: Path,
    include_paths: tuple[str, ...],
    exclude_paths: tuple[str, ...],
) -> tuple[list[Path], list[SkippedTarget]]:
    files: list[Path] = []
    skipped: list[SkippedTarget] = []
    for path in target_root.rglob("*"):
        relative = _relative_path(path, target_root)
        if path.is_symlink():
            skipped.append(SkippedTarget(path=relative, reason="symlink-skipped"))
            continue
        if not path.is_file():
            continue
        # Apply include/exclude scope first: files outside the requested scope are
        # silently dropped and never appear in skipped_targets.  This prevents
        # generated-path noise (e.g. .git/, .claude/) from polluting skipped_targets
        # when --include-path narrows the scan surface.
        if not _path_matches_filters(path, target_root, include_paths, exclude_paths):
            continue
        # Generated paths that fall inside the requested scope are recorded as skipped
        # so the caller can see what was intentionally bypassed.
        if _is_generated_path(relative):
            skipped.append(SkippedTarget(path=relative, reason="generated-path-skipped"))
            continue
        if not _is_supported_text_file(path):
            skipped.append(SkippedTarget(path=relative, reason="unsupported-suffix"))
            continue
        if path.stat().st_size > DEFAULT_MAX_FILE_BYTES:
            skipped.append(SkippedTarget(path=relative, reason="max-file-size-exceeded"))
            continue
        sample = path.read_bytes()[:1024]
        if _is_binary_bytes(sample):
            skipped.append(SkippedTarget(path=relative, reason="binary-skipped"))
            continue
        if len(files) >= MAX_SCAN_FILE_COUNT:
            skipped.append(SkippedTarget(path=relative, reason="scan-file-count-limit-exceeded"))
            continue
        files.append(path)
    return (
        sorted(files, key=lambda p: _relative_path(p, target_root)),
        sorted(skipped, key=lambda s: s.path),
    )


# ── CI-18 (Parameter Cluster) ──────────────────────────────────────────────

# ── Structure signal detectors (domain-vocabulary-driven) ──────────────────

@dataclass(frozen=True, slots=True)
class _DomainPatterns:
    side_program: re.Pattern[str]
    authority: re.Pattern[str]


def _scan_side_program_leak(
    paths: list[Path],
    root: Path,
    next_id: int,
    patterns: _DomainPatterns,
) -> list[AciFinding]:
    findings: list[AciFinding] = []
    for path in paths:
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            if not patterns.side_program.search(line):
                continue
            if SAFE_SIDE_PROGRAM_PATTERN.search(line) or not patterns.authority.search(line):
                continue
            findings.append(
                build_structure_finding(
                    finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                    signal=SIGNAL_SIDE_PROGRAM_LEAK,
                    severity="high",
                    confidence=CONFIDENCE_MEDIUM,
                    target_file=_relative_path(path, root),
                    line=lineno,
                    excerpt=line.strip(),
                    reason="A secondary program or concern appears to be treated as an authority surface.",
                    evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                )
            )
    return findings



# ── CI-02 (Spaghetti Code) ────────────────────────────────────────────────



# ── CI-05 (Copy-Paste Programming) ────────────────────────────────────────

# ── CI-06 (Magic Number) ──────────────────────────────────────────────────

# ── CI-12 (Poltergeist) ───────────────────────────────────────────────────

def _build_summary(findings: list[AciFinding]) -> dict[str, object]:
    severity_counts = Counter(item.severity for item in findings)
    confidence_counts = Counter(item.confidence for item in findings)
    actor_counts = Counter(item.actor_label for item in findings)
    triage_counts = Counter(item.triage_state for item in findings)
    priority_counts = Counter(item.priority for item in findings)
    baseline_counts = Counter(item.baseline_status for item in findings)
    lifecycle_counts = Counter(item.lifecycle_state for item in findings)
    blocking = [
        item
        for item in findings
        if item.severity in {SEVERITY_CRITICAL, SEVERITY_HIGH} and item.waiver_status == "none"
    ]
    return {
        "total_findings": len(findings),
        "by_severity": dict(severity_counts),
        "by_confidence": dict(confidence_counts),
        "by_actor_label": dict(actor_counts),
        "by_triage_state": dict(triage_counts),
        "by_priority": dict(priority_counts),
        "by_baseline_status": dict(baseline_counts),
        "by_lifecycle_state": dict(lifecycle_counts),
        "waived_count": sum(1 for item in findings if item.waiver_status != "none"),
        "suppressed_count": 0,
        "new_count": sum(1 for item in findings if item.baseline_status == "new"),
        "existing_baseline_count": sum(
            1 for item in findings if item.baseline_status == "existing-baseline"
        ),
        "blocker_count": len(blocking),
        "residual_count": sum(1 for item in findings if item.triage_state == "accepted-residual"),
    }


def _build_gate_result(
    findings: list[AciFinding],
    *,
    severity_threshold: str,
    fail_on_new_findings: bool,
    fail_on_unreviewed_review_required: bool,
    fail_on_analyzer_errors: bool,
    analyzer_runs: list[dict[str, object]],
) -> dict[str, object]:
    threshold_rank = SEVERITY_RANK[severity_threshold]
    blocking = [
        item
        for item in findings
        if SEVERITY_RANK[item.severity] >= threshold_rank and item.waiver_status == "none"
    ]
    reasons: list[str] = []
    if blocking:
        reasons.append("severity-threshold")
    if fail_on_new_findings and any(
        item.baseline_status == "new" and item.waiver_status == "none" for item in findings
    ):
        reasons.append("new-findings-present")
    unreviewed = [
        item
        for item in findings
        if (
            item.owner_lane == LANE_HUMAN_JUDGMENT
            and item.waiver_status == "none"
            and item.baseline_status == "new"
        )
    ]
    if fail_on_unreviewed_review_required and unreviewed:
        reasons.append("unreviewed-review-required")
    analyzer_failures = [item for item in analyzer_runs if not item["ok"]]
    if fail_on_analyzer_errors and analyzer_failures:
        reasons.append("analyzer-runtime-error")
    reason_details: list[dict[str, object]] = []
    if "severity-threshold" in reasons:
        reason_details.append(
            {
                "reason": "severity-threshold",
                "count": len(blocking),
                "finding_ids": [item.finding_id for item in blocking],
            }
        )
    if "new-findings-present" in reasons:
        new_findings = [
            item for item in findings
            if item.baseline_status == "new" and item.waiver_status == "none"
        ]
        reason_details.append(
            {
                "reason": "new-findings-present",
                "count": len(new_findings),
                "finding_ids": [item.finding_id for item in new_findings],
            }
        )
    if "unreviewed-review-required" in reasons:
        reason_details.append(
            {
                "reason": "unreviewed-review-required",
                "count": len(unreviewed),
                "finding_ids": [item.finding_id for item in unreviewed],
            }
        )
    if "analyzer-runtime-error" in reasons:
        reason_details.append(
            {
                "reason": "analyzer-runtime-error",
                "count": len(analyzer_failures),
                "analyzers": [item["analyzer_id"] for item in analyzer_failures],
            }
        )
    return {
        "decision": "fail" if reasons else "pass",
        "blocking_severities": [
            severity for severity, rank in SEVERITY_RANK.items() if rank >= threshold_rank
        ],
        "blocking_count": len(blocking),
        "unreviewed_review_required_count": len(unreviewed),
        "analyzer_failure_count": len(analyzer_failures),
        "reasons": reasons,
        "reason_details": reason_details,
        "severity_threshold": severity_threshold,
        "fail_on_new_findings": fail_on_new_findings,
        "fail_on_unreviewed_review_required": fail_on_unreviewed_review_required,
        "fail_on_analyzer_errors": fail_on_analyzer_errors,
    }


def _build_blockers(findings: list[AciFinding], gate: dict[str, object]) -> list[dict[str, object]]:
    threshold_levels = set(cast("list[str]", gate["blocking_severities"]))
    blockers: list[dict[str, object]] = []
    for finding in findings:
        if finding.severity not in threshold_levels:
            continue
        if finding.waiver_status != "none":
            continue
        blockers.append(
            {
                "blocker_id": f"B-{finding.finding_id}",
                "finding_id": finding.finding_id,
                "signal": finding.signal,
                "severity": finding.severity,
                "target_file": finding.target_file,
                "line": finding.line,
                "reason": finding.reason,
                "required_decision": "resolve-or-waive",
                "resume_condition": "all blockers resolved or explicitly waived",
            }
        )
    return blockers


def _build_residuals(findings: list[AciFinding]) -> list[dict[str, object]]:
    residuals: list[dict[str, object]] = []
    for finding in findings:
        if finding.triage_state != "accepted-residual":
            continue
        residuals.append(
            {
                "residual_id": f"R-{finding.finding_id}",
                "classification": "accepted-risk",
                "reason": finding.reason,
                "target_file": finding.target_file,
                "line": finding.line,
                "next_wave": "recheck when the owning boundary changes",
            }
        )
    return residuals


def _deduplicate_findings(findings: list[AciFinding]) -> list[AciFinding]:
    deduplicated: dict[str, AciFinding] = {}
    for finding in findings:
        deduplicated.setdefault(finding.fingerprint, finding)
    return list(deduplicated.values())


def _apply_operations(
    findings: list[AciFinding],
    operations: OperationsState,
) -> tuple[list[AciFinding], int]:
    visible_findings: list[AciFinding] = []
    suppressed_count = 0
    for finding in findings:
        suppression = find_matching_suppression(finding, operations)
        if suppression is not None:
            suppressed_count += 1
            continue
        baseline_status = "existing-baseline" if is_existing_baseline(finding, operations) else "new"
        waiver = find_active_waiver(finding, operations)
        visible_findings.append(
            replace(
                finding,
                baseline_status=baseline_status,
                waiver_status="active-waiver" if waiver is not None else "none",
                lifecycle_state="accepted" if waiver is not None else finding.lifecycle_state,
                triage_state="accepted-residual" if waiver is not None else finding.triage_state,
            )
        )
    return visible_findings, suppressed_count


def scan_target(
    target_root: Path,
    profile_id: str,
    domain_id: str,
    operations_file: Path | None = None,
    include_paths: tuple[str, ...] = (),
    exclude_paths: tuple[str, ...] = (),
    severity_threshold: str = "high",
    fail_on_new_findings: bool = False,
    include_external_analyzers: bool = True,
    fail_on_analyzer_errors: bool = False,
    ignore_file: Path | None = None,
    domain_file: Path | None = None,
    fail_on_unreviewed_review_required: bool = False,
    diff_from: str | None = None,
) -> dict[str, object]:
    resolved_root = target_root.resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"Scan target does not exist: {target_root}")
    if not resolved_root.is_dir():
        raise ValueError(f"Scan target must be a directory: {target_root}")

    # Enforce targeted-scope requirement before loading anything else
    if profile_id in PROFILE_REQUIRES_TARGETED_SCOPE and not include_paths:
        raise ValueError(
            f"Profile '{profile_id}' requires targeted scope: provide include_paths to limit the scan surface."
        )

    # Load domain rules; apply domain-level exclusions to exclude_paths
    domain_rules = load_domain_rules(None if domain_id == CORE_ONLY_DOMAIN_ID else domain_id, domain_file)
    domain_excluded = tuple(
        item.replace("\\", "/").strip("/")
        for item in (*domain_rules.excluded_files, *domain_rules.excluded_prefixes)
        if item
    )
    effective_exclude = tuple(
        sorted(
            set(item.replace("\\", "/").strip("/") for item in exclude_paths if item)
            | set(domain_excluded)
        )
    )

    # Compile domain vocabulary patterns (never-match when terms are empty)
    domain_patterns = _DomainPatterns(
        side_program=compile_keyword_pattern(*domain_rules.side_program_terms),
        authority=compile_keyword_pattern(*domain_rules.authority_terms),
    )

    session = ScanSession(
        target_root=resolved_root,
        profile_id=profile_id,
        domain_id=domain_rules.domain_id,
        operations=load_operations_state(operations_file),
        include_paths=tuple(item.replace("\\", "/").strip("/") for item in include_paths if item),
        exclude_paths=effective_exclude,
        severity_threshold=severity_threshold,
        fail_on_new_findings=fail_on_new_findings,
        fail_on_unreviewed_review_required=fail_on_unreviewed_review_required,
        include_external_analyzers=include_external_analyzers,
        fail_on_analyzer_errors=fail_on_analyzer_errors,
        ignore_patterns=load_ignore_patterns(
            resolved_root,
            ignore_file.resolve() if ignore_file is not None else None,
        ),
        diff_from=diff_from,
    )

    # Determine active signals for this profile (gate which detectors run)
    active_signals = set(_PROFILE_SIGNALS.get(profile_id, _PROFILE_SIGNALS[PROFILE_FULL]))
    enabled_lanes = set(PROFILE_ENABLED_LANES.get(profile_id, (LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER, LANE_HUMAN_JUDGMENT)))

    findings: list[AciFinding] = []
    analyzer_runs: list[dict[str, object]] = []
    next_id = 1
    target_files, skipped_targets = _iter_target_files(
        session.target_root,
        session.include_paths,
        tuple(sorted(set(session.exclude_paths + session.ignore_patterns))),
    )

    if session.diff_from is not None:
        changed = _git_changed_files(session.target_root, session.diff_from)
        target_files = [f for f in target_files if _relative_path(f, session.target_root) in changed]

    for file_path in target_files:
        text = file_path.read_text(encoding="utf-8", errors="ignore")

        for required_signals, detector in PER_FILE_REGISTRY:
            if required_signals & active_signals:
                new = detector(file_path, text, session.target_root, next_id)
                next_id += len(new)
                findings.extend(new)

    # Cross-file detectors (run once over all collected files)
    for required_signals, detector in CROSS_FILE_REGISTRY:
        if required_signals & active_signals:
            new = detector(target_files, session.target_root, next_id)
            next_id += len(new)
            findings.extend(new)

    # Domain-vocabulary structure signal detectors
    if SIGNAL_SIDE_PROGRAM_LEAK in active_signals and domain_rules.side_program_terms:
        side = _scan_side_program_leak(
            target_files, session.target_root, next_id, domain_patterns
        )
        next_id += len(side)
        findings.extend(side)

    # External analyzers (only when lane is enabled)
    if (
        session.include_external_analyzers
        and LANE_EXTERNAL_ANALYZER in enabled_lanes
        and session.profile_id in {PROFILE_QUICK_GATE, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_FULL}
    ):
        analyzer_ids = {
            PROFILE_QUICK_GATE: ("ruff", "pyflakes"),
            PROFILE_BUILD_PREFLIGHT: ("ruff", "pyflakes", "mypy"),
            PROFILE_BUILD_REVIEW: ("ruff", "pyflakes", "mypy", "pytest"),
            PROFILE_FULL: ("ruff", "pyflakes", "mypy", "pytest"),
        }[session.profile_id]
        for analyzer_id in analyzer_ids:
            run_result = run_analyzer(analyzer_id, session.target_root, next_id)
            analyzer_runs.append(run_result.as_dict())
            next_id += len(run_result.findings)
            findings.extend(run_result.findings)

    findings = _deduplicate_findings(findings)
    # Compute resolved baseline entries before suppression (suppressed findings are still detected)
    resolved_baseline = find_resolved_baseline_entries(session.operations, findings)
    findings, suppressed_count = _apply_operations(findings, session.operations)

    # Sort by severity descending (contract requirement)
    findings = sorted(findings, key=lambda f: SEVERITY_RANK.get(f.severity, 0), reverse=True)

    summary = _build_summary(findings)
    summary["suppressed_count"] = suppressed_count
    summary["resolved_baseline_count"] = len(resolved_baseline)

    gate = _build_gate_result(
        findings,
        severity_threshold=session.severity_threshold,
        fail_on_new_findings=session.fail_on_new_findings,
        fail_on_unreviewed_review_required=session.fail_on_unreviewed_review_required,
        fail_on_analyzer_errors=session.fail_on_analyzer_errors,
        analyzer_runs=analyzer_runs,
    )
    blockers = _build_blockers(findings, gate)
    residuals = _build_residuals(findings)
    summary["blocker_count"] = len(blockers)
    summary["residual_count"] = len(residuals)

    return {
        "tool": "ACI",
        "command": "scan",
        "report_format_version": "1.0.0",
        "report_id": f"aci-scan-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
        "tool_id": "aci_scan",
        "tool_version": ACI_TOOL_VERSION,
        "mode": "aci runtime scan",
        "profile_id": session.profile_id,
        "domain": session.domain_id,
        "scan_scope": session.target_root.as_posix(),
        "scope_rules": {
            "include_paths": list(session.include_paths),
            "exclude_paths": list(session.exclude_paths),
            "ignore_patterns": list(session.ignore_patterns),
            "diff_from": session.diff_from,
            "max_file_bytes": DEFAULT_MAX_FILE_BYTES,
            "max_scan_file_count": MAX_SCAN_FILE_COUNT,
            "skip_binary_files": True,
            "skip_symlinks": True,
            "skip_generated_paths": True,
            "generated_path_segments": sorted(DEFAULT_GENERATED_PATH_SEGMENTS),
        },
        "skipped_targets": [item.__dict__ for item in skipped_targets],
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verification_status": "executed",
        "external_analyzer_runs": analyzer_runs,
        "operations_file": None if operations_file is None else operations_file.resolve().as_posix(),
        "summary": summary,
        "findings": [item.as_dict() for item in findings],
        "blockers": blockers,
        "residuals": residuals,
        "resolved_baseline_entries": resolved_baseline,
        "gate": gate,
        "next_actions": [
            "Review blocking findings first.",
            "Decide which low-severity patchwork markers should stay visible versus become tracked follow-up work.",
        ],
    }
