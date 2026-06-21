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
- Only files with known text/code suffixes (.py, .js, .ts, .sh, .sql, .md, .toml, ...) are processed.
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

import ast
import dataclasses
from dataclasses import dataclass
from datetime import datetime, UTC
import hashlib
from pathlib import Path
import re
from typing import Protocol

ACI_TOOL_VERSION = "0.1.8"

try:
    from .detectors import PER_FILE_REGISTRY, CROSS_FILE_REGISTRY
    from .detectors._helpers import _relative_path
    from .aci_analyzer_execution import run_analyzer, _readiness_for
    from .aci_domain_contract import AciDomainRules, CORE_ONLY_DOMAIN_ID
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
        find_resolved_baseline_entries,
        load_operations_state,
    )
    from .aci_profile_catalog import PROFILE_ENABLED_LANES
    from .aci_profiles import (
        build_profile_signals, PROFILE_REQUIRES_TARGETED_SCOPE,
        PROFILE_QUICK_GATE, PROFILE_FULL, PROFILE_SELF_AUDIT, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW,
    )
    from .aci_signals import (
        STRUCTURE_SIGNALS as _STRUCTURE_SIGNALS,
        SIGNAL_SIDE_PROGRAM_LEAK,
        SAFE_SIDE_PROGRAM_PATTERN,
        compile_keyword_pattern,
    )
    from .aci_known_limits import known_limits, detection_disclosure
except ImportError:  # pragma: no cover - direct script/module import path
    from detectors import PER_FILE_REGISTRY, CROSS_FILE_REGISTRY  # type: ignore[no-redef]
    from detectors._helpers import _relative_path  # type: ignore[no-redef]
    from aci_analyzer_execution import run_analyzer, _readiness_for
    from aci_domain_contract import AciDomainRules, CORE_ONLY_DOMAIN_ID
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
        find_resolved_baseline_entries,
        load_operations_state,
    )
    from aci_profile_catalog import PROFILE_ENABLED_LANES
    from aci_profiles import (
        build_profile_signals, PROFILE_REQUIRES_TARGETED_SCOPE,
        PROFILE_QUICK_GATE, PROFILE_FULL, PROFILE_SELF_AUDIT, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW,
    )
    from aci_signals import (
        STRUCTURE_SIGNALS as _STRUCTURE_SIGNALS,
        SIGNAL_SIDE_PROGRAM_LEAK,
        SAFE_SIDE_PROGRAM_PATTERN,
        compile_keyword_pattern,
    )
    from aci_known_limits import known_limits, detection_disclosure


try:
    from ._scan_scope import (  # noqa: F401  (re-exported for downstream/test imports)
        TEXT_SUFFIXES, DEFAULT_MAX_FILE_BYTES, MAX_SCAN_FILE_COUNT, DEFAULT_GENERATED_PATH_SEGMENTS,
        SCOPE_MODE_FULL_REPO, SCOPE_MODE_SOURCE_ONLY, SCOPE_MODE_DOGFOOD, SCOPE_MODE_SELF_AUDIT, SUPPORTED_SCOPE_MODES,
        SCOPE_CLASS_RUNTIME_SOURCE, SCOPE_CLASS_TESTS, SCOPE_CLASS_FIXTURES, SCOPE_CLASS_DOCS_EVIDENCE,
        SCOPE_CLASS_ROADMAP_EVIDENCE, SCOPE_CLASS_MAINTAINER_PROBES, SCOPE_CLASS_SUPPORT, SCOPE_CLASS_GENERATED,
        SkippedTarget, _classify_relative_path, _resolve_scope_filters, _gate_scope_classes,
        _select_external_analyzers, _iter_target_files, _git_changed_files, _git_changed_lines, _path_matches_filters,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from _scan_scope import (  # type: ignore[no-redef]  # noqa: F401
        TEXT_SUFFIXES, DEFAULT_MAX_FILE_BYTES, MAX_SCAN_FILE_COUNT, DEFAULT_GENERATED_PATH_SEGMENTS,
        SCOPE_MODE_FULL_REPO, SCOPE_MODE_SOURCE_ONLY, SCOPE_MODE_DOGFOOD, SCOPE_MODE_SELF_AUDIT, SUPPORTED_SCOPE_MODES,
        SCOPE_CLASS_RUNTIME_SOURCE, SCOPE_CLASS_TESTS, SCOPE_CLASS_FIXTURES, SCOPE_CLASS_DOCS_EVIDENCE,
        SCOPE_CLASS_ROADMAP_EVIDENCE, SCOPE_CLASS_MAINTAINER_PROBES, SCOPE_CLASS_SUPPORT, SCOPE_CLASS_GENERATED,
        SkippedTarget, _classify_relative_path, _resolve_scope_filters, _gate_scope_classes,
        _select_external_analyzers, _iter_target_files, _git_changed_files, _git_changed_lines, _path_matches_filters,
    )




SEVERITY_RANK = {
    SEVERITY_LOW: 1,
    SEVERITY_MEDIUM: 2,
    SEVERITY_HIGH: 3,
    SEVERITY_CRITICAL: 4,
}


# CI-06 (Magic Number) helpers

# Profile signal catalog (wires build_profile_signals to the native detector set).
#
# Default-vs-opt-in is decided by ONE principled criterion: a native detector
# runs by default only if ACI is confident (>= MEDIUM) in at least one of its
# signals. Detectors whose every signal is CONFIDENCE_LOW -- i.e. ACI itself
# signals it is not confident -- are opt-in (the `full` / `self-audit` profiles),
# not applied by the default scan. Confidence is field-calibrated (see
# examples/aci-field-precision/), so this criterion is grounded in measured
# reliability, not taste. The detector-level run filter (_run_*_detectors keys on
# `required_signals & active_signals`) means only WHOLLY-low-confidence,
# single-purpose detectors can be cleanly withheld; CI-02 and CI-22 stay in the
# default because each also emits a >= MEDIUM signal.
_NATIVE_HYGIENE_SIGNALS: tuple[str, ...] = (
    "CI02_SPAGHETTI_CODE",
    "CI02_LONG_FUNCTION",
    "CI03_TODO_HACK",
    "CI07_UNUSED_PRIVATE_SYMBOL",
    "CI12_POLTERGEIST",
    "CI13_CIRCULAR_IMPORT",
    "CI14_PLAINTEXT_SECRET",
    "CI14_DYNAMIC_CODE_EXECUTION",
    "CI14_SUBPROCESS_SHELL_TRUE",
    "CI14_INSECURE_HTTP",
    "CI14_UNSAFE_DESERIALIZATION",
    "CI14_UNSAFE_YAML_LOAD",
    "CI14_SUPPLY_CHAIN_DRIFT",
    "CI14_TAINTED_FLOW",
    "CI20_SCATTERED_CONSTANT",
    "CI21_BROAD_EXCEPTION_SWALLOW",
    "CI21_SILENT_EXCEPTION_RETURN",
    "CI22_RESOURCE_CLEANUP_GAP",
    "CI25_ENVIRONMENT_DRIFT",
    "CI26_RACE_HAZARD",
)
# Wholly-LOW-confidence detectors: opt-in (full / self-audit only), not default.
# CI-04 (god class) and CI-05 (copy-paste) measured weakest in the field
# (0% / 40% precision); CI-06/CI-18/CI-23 are low-confidence stylistic signals.
_OPT_IN_NATIVE_SIGNALS: tuple[str, ...] = (
    "CI04_GOD_CLASS",
    "CI05_COPY_PASTE_CODE",
    "CI06_MAGIC_NUMBER",
    "CI18_PARAMETER_CLUSTER",
    "CI23_CONTRACT_FIELD_DRIFT",
)
_EXTERNAL_EVIDENCE_SIGNALS: tuple[str, ...] = ("EXTERNAL_STATIC_ANALYSIS",)
_HUMAN_JUDGMENT_SIGNALS: tuple[str, ...] = ()
_RUFF_DELEGATED_SIGNALS: frozenset[str] = frozenset({
    "CI02_LONG_FUNCTION",
    "CI03_TODO_HACK",
    "CI18_PARAMETER_CLUSTER",
    "CI21_BROAD_EXCEPTION_SWALLOW",
    "CI26_RACE_HAZARD",
})

_PROFILE_SIGNALS: dict[str, tuple[str, ...]] = build_profile_signals(
    structure_signals=_STRUCTURE_SIGNALS,
    external_evidence_signals=_EXTERNAL_EVIDENCE_SIGNALS,
    human_judgment_signals=_HUMAN_JUDGMENT_SIGNALS,
    native_hygiene_signals=_NATIVE_HYGIENE_SIGNALS,
    opt_in_native_signals=_OPT_IN_NATIVE_SIGNALS,
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
    scope_mode: str
    gate_scope_classes: tuple[str, ...]
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
class ScanOptions:
    operations_file: Path | None = None
    include_paths: tuple[str, ...] = ()
    exclude_paths: tuple[str, ...] = ()
    severity_threshold: str = "high"
    fail_on_new_findings: bool = False
    include_external_analyzers: bool = True
    fail_on_analyzer_errors: bool = False
    ignore_file: Path | None = None
    domain_file: Path | None = None
    fail_on_unreviewed_review_required: bool = False
    diff_from: str | None = None
    scope_mode: str = SCOPE_MODE_FULL_REPO


@dataclass(frozen=True)
class ScanArtifacts:
    skipped_targets: list[SkippedTarget]
    analyzer_runs: list[dict[str, object]]
    findings: list[AciFinding]
    resolved_baseline: list[dict[str, object]]
    suppressed_count: int


























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

try:
    from ._scan_report import (
        _build_summary, _build_review_brief, _build_gate_result, _build_blockers, _build_residuals,
    )
    from ._scan_postprocess import _deduplicate_findings, _filter_scope_noise, _apply_operations
except ImportError:  # pragma: no cover - direct script/module import path
    from _scan_report import (  # type: ignore[no-redef]
        _build_summary, _build_review_brief, _build_gate_result, _build_blockers, _build_residuals,
    )
    from _scan_postprocess import _deduplicate_findings, _filter_scope_noise, _apply_operations  # type: ignore[no-redef]


def _validate_scan_request(resolved_root: Path, target_root: Path, profile_id: str, include_paths: tuple[str, ...]) -> None:
    if not resolved_root.exists():
        raise FileNotFoundError(f"Scan target does not exist: {target_root}")
    if not resolved_root.is_dir():
        raise ValueError(f"Scan target must be a directory: {target_root}")
    if profile_id in PROFILE_REQUIRES_TARGETED_SCOPE and not include_paths:
        raise ValueError(
            f"Profile '{profile_id}' requires targeted scope: provide include_paths to limit the scan surface."
        )


def _build_scan_session(
    resolved_root: Path,
    profile_id: str,
    domain_rules: AciDomainRules,
    options: ScanOptions,
) -> ScanSession:
    domain_excluded = tuple(
        item.replace("\\", "/").strip("/")
        for item in (*domain_rules.excluded_files, *domain_rules.excluded_prefixes)
        if item
    )
    resolved_include, resolved_exclude = _resolve_scope_filters(
        resolved_root,
        options.scope_mode,
        options.include_paths,
        options.exclude_paths,
    )
    effective_exclude = tuple(sorted(set(resolved_exclude) | set(domain_excluded)))
    return ScanSession(
        target_root=resolved_root,
        profile_id=profile_id,
        domain_id=domain_rules.domain_id,
        operations=load_operations_state(options.operations_file),
        scope_mode=options.scope_mode,
        gate_scope_classes=_gate_scope_classes(options.scope_mode),
        include_paths=resolved_include,
        exclude_paths=effective_exclude,
        severity_threshold=options.severity_threshold,
        fail_on_new_findings=options.fail_on_new_findings,
        fail_on_unreviewed_review_required=options.fail_on_unreviewed_review_required,
        include_external_analyzers=options.include_external_analyzers,
        fail_on_analyzer_errors=options.fail_on_analyzer_errors,
        ignore_patterns=load_ignore_patterns(
            resolved_root,
            options.ignore_file.resolve() if options.ignore_file is not None else None,
        ),
        diff_from=options.diff_from,
    )


def _load_domain_context(domain_id: str, domain_file: Path | None) -> tuple[AciDomainRules, _DomainPatterns]:
    domain_rules = load_domain_rules(None if domain_id == CORE_ONLY_DOMAIN_ID else domain_id, domain_file)
    return domain_rules, _DomainPatterns(
        side_program=compile_keyword_pattern(*domain_rules.side_program_terms),
        authority=compile_keyword_pattern(*domain_rules.authority_terms),
    )


def _target_files_for_session(session: ScanSession) -> tuple[list[Path], list[SkippedTarget]]:
    target_files, skipped_targets = _iter_target_files(
        session.target_root,
        session.include_paths,
        tuple(sorted(set(session.exclude_paths + session.ignore_patterns))),
    )
    if session.diff_from is None:
        return target_files, skipped_targets
    changed = _git_changed_files(session.target_root, session.diff_from)
    return [path for path in target_files if _relative_path(path, session.target_root) in changed], skipped_targets


def _run_per_file_detectors(
    target_files: list[Path],
    session: ScanSession,
    active_signals: set[str],
    next_id: int,
) -> tuple[list[AciFinding], int]:
    findings: list[AciFinding] = []
    for file_path in target_files:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for required_signals, detector in PER_FILE_REGISTRY:
            if required_signals & active_signals:
                new = detector(file_path, text, session.target_root, next_id)
                next_id += len(new)
                findings.extend(new)
    return findings, next_id


def _run_cross_file_detectors(
    target_files: list[Path],
    target_root: Path,
    active_signals: set[str],
    next_id: int,
) -> tuple[list[AciFinding], int]:
    findings: list[AciFinding] = []
    for required_signals, detector in CROSS_FILE_REGISTRY:
        if required_signals & active_signals:
            new = detector(target_files, target_root, next_id)
            next_id += len(new)
            findings.extend(new)
    return findings, next_id


def _run_domain_structure_detectors(
    target_files: list[Path],
    session: ScanSession,
    active_signals: set[str],
    domain_patterns: _DomainPatterns,
    next_id: int,
) -> tuple[list[AciFinding], int]:
    if SIGNAL_SIDE_PROGRAM_LEAK not in active_signals or domain_patterns.side_program.pattern == "(?!)":
        return [], next_id
    findings = _scan_side_program_leak(target_files, session.target_root, next_id, domain_patterns)
    return findings, next_id + len(findings)


def _external_target_files_for_session(session: ScanSession, target_files: list[Path]) -> list[Path]:
    if session.scope_mode != SCOPE_MODE_FULL_REPO:
        return target_files
    allowed_scope_classes = {SCOPE_CLASS_RUNTIME_SOURCE, SCOPE_CLASS_TESTS}
    return [
        path
        for path in target_files
        if _classify_relative_path(_relative_path(path, session.target_root)) in allowed_scope_classes
    ]


def _delegated_native_signals(
    session: ScanSession,
    target_files: list[Path],
    enabled_lanes: set[str],
) -> frozenset[str]:
    if not session.include_external_analyzers or LANE_EXTERNAL_ANALYZER not in enabled_lanes:
        return frozenset()
    analyzer_ids = _select_external_analyzers(session.profile_id, target_files, session.target_root)
    if "ruff" not in analyzer_ids:
        return frozenset()
    if _readiness_for("ruff").availability_state != "ready":
        return frozenset()
    return _RUFF_DELEGATED_SIGNALS


def _run_external_analyzers_for_session(
    session: ScanSession,
    target_files: list[Path],
    enabled_lanes: set[str],
    next_id: int,
) -> tuple[list[AciFinding], list[dict[str, object]], int]:
    analyzer_runs: list[dict[str, object]] = []
    if (
        not session.include_external_analyzers
        or LANE_EXTERNAL_ANALYZER not in enabled_lanes
        or session.profile_id not in {PROFILE_QUICK_GATE, PROFILE_BUILD_PREFLIGHT, PROFILE_BUILD_REVIEW, PROFILE_FULL, PROFILE_SELF_AUDIT}
    ):
        return [], analyzer_runs, next_id

    findings: list[AciFinding] = []
    external_target_files = _external_target_files_for_session(session, target_files)
    scoped_rel_paths = frozenset(_relative_path(path, session.target_root) for path in external_target_files)
    analyzer_ids = _select_external_analyzers(session.profile_id, external_target_files, session.target_root)
    for analyzer_id in analyzer_ids:
        run_result = run_analyzer(analyzer_id, session.target_root, next_id)
        scoped = [finding for finding in run_result.findings if finding.target_file in scoped_rel_paths]
        analyzer_runs.append(run_result.as_dict())
        next_id += len(scoped)
        findings.extend(scoped)
    return findings, analyzer_runs, next_id


def _collect_scan_findings(
    session: ScanSession,
    domain_patterns: _DomainPatterns,
) -> tuple[list[Path], list[SkippedTarget], list[AciFinding], list[dict[str, object]]]:
    enabled_lanes = set(
        PROFILE_ENABLED_LANES.get(
            session.profile_id,
            (LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER, LANE_HUMAN_JUDGMENT),
        )
    )
    target_files, skipped_targets = _target_files_for_session(session)
    active_signals = set(_PROFILE_SIGNALS.get(session.profile_id, _PROFILE_SIGNALS[PROFILE_FULL]))
    active_signals -= _delegated_native_signals(session, target_files, enabled_lanes)
    findings, next_id = _run_per_file_detectors(target_files, session, active_signals, 1)
    cross_file_findings, next_id = _run_cross_file_detectors(target_files, session.target_root, active_signals, next_id)
    findings.extend(cross_file_findings)
    structure_findings, next_id = _run_domain_structure_detectors(
        target_files,
        session,
        active_signals,
        domain_patterns,
        next_id,
    )
    findings.extend(structure_findings)
    external_findings, analyzer_runs, next_id = _run_external_analyzers_for_session(
        session,
        target_files,
        enabled_lanes,
        next_id,
    )
    findings.extend(external_findings)
    if session.diff_from is not None:
        findings = _restrict_findings_to_changed_lines(findings, session.target_root, session.diff_from)
    findings = _stabilize_fingerprints(findings, session.target_root)
    return target_files, skipped_targets, findings, analyzer_runs


def _enclosing_qualname_spans(source: str) -> list[tuple[int, int, str]]:
    """Return (start_line, end_line, dotted_name) for every function/class.

    Used to anchor a finding to the *symbol* it lives in rather than its line
    number, so the identity is stable when unrelated edits shift lines around.
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    spans: list[tuple[int, int, str]] = []

    def walk(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qualname = prefix + child.name
                end = getattr(child, "end_lineno", None) or child.lineno
                spans.append((child.lineno, end, qualname))
                walk(child, qualname + ".")
            else:
                walk(child, prefix)

    walk(tree, "")
    return spans


def _qualname_at(spans: list[tuple[int, int, str]], line: int) -> str:
    best: tuple[int, int, str] | None = None
    for start, end, qualname in spans:
        if start <= line <= end and (best is None or (end - start) < (best[1] - best[0])):
            best = (start, end, qualname)
    return best[2] if best else ""


def _stabilize_fingerprints(findings: list[AciFinding], target_root: Path) -> list[AciFinding]:
    """Recompute each finding's fingerprint from a line-number-independent key.

    The default fingerprint includes the line number and the (volatile) reason
    text, so an unrelated edit above a finding -- or a change to a function's
    length -- shifts its fingerprint and a baseline/waiver keyed on the old value
    stops matching, re-surfacing pre-existing findings as "new". This keys on the
    enclosing symbol plus the flagged line's own (whitespace-normalized) content,
    which is stable under line shifts and changes only when the flagged code or
    its symbol actually changes.
    """
    if not findings:
        return findings
    cache: dict[str, tuple[list[tuple[int, int, str]], list[str]]] = {}
    stabilized: list[AciFinding] = []
    for finding in findings:
        rel = finding.target_file
        if rel not in cache:
            try:
                source = (target_root / rel).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                source = ""
            cache[rel] = (_enclosing_qualname_spans(source), source.splitlines())
        spans, lines = cache[rel]
        line = finding.line
        qualname = _qualname_at(spans, line) if line else ""
        content = " ".join(lines[line - 1].split()) if line and 1 <= line <= len(lines) else ""
        stable_key = "|".join([finding.ci_id, finding.signal, rel, qualname, content])
        new_fp = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:16]
        stabilized.append(dataclasses.replace(finding, fingerprint=new_fp))
    return stabilized


def _construct_spans(source: str) -> dict[int, int]:
    """Map each function/class definition line to the construct's last line.

    Lets a structural finding (anchored at the def line) be scoped to the whole
    function/class span, so a change anywhere inside it counts as touching it.
    """
    spans: dict[int, int] = {}
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return spans
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            end = getattr(node, "end_lineno", None) or node.lineno
            spans[node.lineno] = max(spans.get(node.lineno, 0), end)
    return spans


def _restrict_findings_to_changed_lines(
    findings: list[AciFinding], target_root: Path, ref: str
) -> list[AciFinding]:
    """Keep only findings that overlap the lines a change actually touched.

    Diff scoping is otherwise file-level: the whole changed file is scanned, so
    pre-existing issues in a touched file are reported even though the change
    never went near them. This narrows the result to findings whose flagged
    construct (a function/class span for structural signals, the exact line for
    line-specific ones) intersects the changed lines.
    """
    try:
        changed_lines = _git_changed_lines(target_root, ref)
    except ValueError:
        return findings  # cannot compute line diff; leave file-level result untouched
    spans_by_file: dict[str, dict[int, int]] = {}
    kept: list[AciFinding] = []
    for finding in findings:
        line = finding.line
        if line is None:
            continue  # no line anchor: cannot attribute to a changed line
        changed = changed_lines.get(finding.target_file)
        if not changed:
            continue  # file had no changed lines (e.g. pure rename/metadata)
        if finding.target_file not in spans_by_file:
            path = target_root / finding.target_file
            try:
                spans_by_file[finding.target_file] = _construct_spans(path.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                spans_by_file[finding.target_file] = {}
        end = spans_by_file[finding.target_file].get(line, line)
        if not changed.isdisjoint(range(line, end + 1)):
            kept.append(finding)
    return kept


def _report_findings(findings: list[AciFinding]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in findings:
        row = item.as_dict()
        row["scope_class"] = _classify_relative_path(item.target_file)
        rows.append(row)
    return rows


def _build_scan_report(session: ScanSession, operations_file: Path | None, artifacts: ScanArtifacts) -> dict[str, object]:
    summary = _build_summary(artifacts.findings)
    summary["suppressed_count"] = artifacts.suppressed_count
    summary["resolved_baseline_count"] = len(artifacts.resolved_baseline)
    gated_findings = [
        item for item in artifacts.findings
        if _classify_relative_path(item.target_file) in session.gate_scope_classes
    ]
    gate = _build_gate_result(
        gated_findings,
        severity_threshold=session.severity_threshold,
        fail_on_new_findings=session.fail_on_new_findings,
        fail_on_unreviewed_review_required=session.fail_on_unreviewed_review_required,
        fail_on_analyzer_errors=session.fail_on_analyzer_errors,
        analyzer_runs=artifacts.analyzer_runs,
    )
    blockers = _build_blockers(gated_findings, gate)
    residuals = _build_residuals(artifacts.findings)
    summary["blocker_count"] = len(blockers)
    summary["residual_count"] = len(residuals)
    review_brief = _build_review_brief(artifacts.findings, blockers, artifacts.analyzer_runs, session, gate)
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
            "scope_mode": session.scope_mode,
            "gate_scope_classes": list(session.gate_scope_classes),
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
        "skipped_targets": [item.__dict__ for item in artifacts.skipped_targets],
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verification_status": "executed",
        "external_analyzer_runs": artifacts.analyzer_runs,
        "detection_disclosure": detection_disclosure(),
        "known_limits": known_limits(),
        "operations_file": None if operations_file is None else operations_file.resolve().as_posix(),
        "summary": summary,
        "findings": _report_findings(artifacts.findings),
        "blockers": blockers,
        "residuals": residuals,
        "review_brief": review_brief,
        "resolved_baseline_entries": artifacts.resolved_baseline,
        "gate": gate,
        "next_actions": [
            "Review blocking findings first.",
            "Decide which low-severity patchwork markers should stay visible versus become tracked follow-up work.",
        ],
    }


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
    scope_mode: str = SCOPE_MODE_FULL_REPO,
) -> dict[str, object]:
    resolved_root = target_root.resolve()
    options = ScanOptions(
        operations_file=operations_file,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
        severity_threshold=severity_threshold,
        fail_on_new_findings=fail_on_new_findings,
        include_external_analyzers=include_external_analyzers,
        fail_on_analyzer_errors=fail_on_analyzer_errors,
        ignore_file=ignore_file,
        domain_file=domain_file,
        fail_on_unreviewed_review_required=fail_on_unreviewed_review_required,
        diff_from=diff_from,
        scope_mode=scope_mode,
    )
    _validate_scan_request(resolved_root, target_root, profile_id, options.include_paths)
    domain_rules, domain_patterns = _load_domain_context(domain_id, options.domain_file)
    session = _build_scan_session(
        resolved_root,
        profile_id,
        domain_rules,
        options,
    )
    target_files, skipped_targets, findings, analyzer_runs = _collect_scan_findings(session, domain_patterns)
    findings = _deduplicate_findings(findings)
    findings = _filter_scope_noise(findings)
    # Resolution is only determinable for files the scan actually examined; a diff
    # scan only looks at changed files, so bound it to avoid reporting every
    # baseline finding in an untouched file as "resolved".
    scanned_files = frozenset(_relative_path(path, session.target_root) for path in target_files)
    resolved_baseline = find_resolved_baseline_entries(session.operations, findings, scanned_files)
    findings, suppressed_count = _apply_operations(findings, session.operations)
    findings = sorted(findings, key=lambda f: SEVERITY_RANK.get(f.severity, 0), reverse=True)
    return _build_scan_report(
        session,
        options.operations_file,
        ScanArtifacts(
            skipped_targets=skipped_targets,
            analyzer_runs=analyzer_runs,
            findings=findings,
            resolved_baseline=resolved_baseline,
            suppressed_count=suppressed_count,
        ),
    )
