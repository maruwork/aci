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

import ast
from collections import Counter
from dataclasses import replace
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
import re
import tokenize
from typing import Protocol

ACI_TOOL_VERSION = "0.1.0"

try:
    from .aci_analyzer_execution import run_analyzer
    from .aci_domain_contract import CORE_ONLY_DOMAIN_ID
    from .aci_domain_loader import load_domain_rules
    from .aci_findings import (
        AciFinding, build_finding, build_structure_finding,
        LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER, LANE_HUMAN_JUDGMENT,
        VERIFICATION_EXECUTED,
        SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW,
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
        LOW_INFO_SCATTERED_LITERALS,
        LOW_INFO_SCATTERED_LITERAL_SUFFIXES,
        SAFE_SIDE_PROGRAM_PATTERN,
        compile_keyword_pattern,
    )
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_analyzer_execution import run_analyzer
    from aci_domain_contract import CORE_ONLY_DOMAIN_ID
    from aci_domain_loader import load_domain_rules
    from aci_findings import (
        AciFinding, build_finding, build_structure_finding,
        LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER, LANE_HUMAN_JUDGMENT,
        VERIFICATION_EXECUTED,
        SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW,
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
        LOW_INFO_SCATTERED_LITERALS,
        LOW_INFO_SCATTERED_LITERAL_SUFFIXES,
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
}

TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK)\b")
BROAD_EXCEPTION_PATTERN = re.compile(r"^\s*except\s+Exception\s*:", re.MULTILINE)
EVAL_EXEC_PATTERN = re.compile(r"\b(eval|exec)\s*\(")
SUBPROCESS_SHELL_TRUE_PATTERN = re.compile(r"\bsubprocess\.(run|Popen|call|check_call|check_output)\s*\([^)]*shell\s*=\s*True", re.DOTALL)
PLAINTEXT_SECRET_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][A-Za-z0-9_\-]{8,}['\"]"
)
INSECURE_HTTP_PATTERN = re.compile(r"(?i)http://[A-Za-z0-9._:/\-]+")
COMMENT_PREFIXES = ("#", "//", ";", "<!--")
SEVERITY_RANK = {
    SEVERITY_LOW: 1,
    SEVERITY_MEDIUM: 2,
    SEVERITY_HIGH: 3,
    SEVERITY_CRITICAL: 4,
}

# CI-18 (Parameter Cluster) helpers
BOUNDARY_INTERFACE_NAME_PATTERN = re.compile(
    r"^(?:_)?(check|record|emit|notify|validate|reset|release|acquire|load|resolve|approve|insert)_"
)
NON_BLOCKING_HINT_PATTERN = re.compile(r"(non-blocking|非ブロッキング|best-effort)", re.IGNORECASE)  # 非ブロッキング is the Japanese equivalent; intentionally included to match Japanese-language annotations
LOGGING_HELPER_NAME_PATTERN = re.compile(r"^(log|record|emit)_[a-z0-9_]+$")
# CI-20 (Scattered Constant) helpers
CONTRACT_FIELD_LITERAL_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,}$")
WINDOWS_PROJECT_PATH_LITERAL_PATTERN = re.compile(r"^[A-Za-z]:\\Users\\[^\\]+\\project\\")
CODE_FENCE_SPLITTER_LITERAL = r"(```[\s\S]*?```)"
PYTHON_DUNDER_LITERAL_PATTERN = re.compile(r"^__[a-zA-Z_]+__$")
ARGPARSE_ACTION_LITERALS: frozenset[str] = frozenset({
    "store_true", "store_false", "store_const", "append_const",
})

# CI-22 (Resource Lifecycle Leak) helpers
RESOURCE_OPENER_NAMES: frozenset[str] = frozenset({
    "open",
    "Popen",
    "NamedTemporaryFile",
    "TemporaryFile",
    "SpooledTemporaryFile",
})

# CI-02 (Spaghetti Code) helpers
CI02_NESTING_THRESHOLD = 4
CI02_LONG_FUNCTION_THRESHOLD = 50

# CI-06 (Magic Number) helpers
CI06_TRIVIAL_NUMBERS: frozenset = frozenset({
    0, 1, 2, 3, 4, 5, 10, 100, 1000,
    0.0, 1.0, 0.5,
})

# CI-25 (Environment Drift) helpers
NONDETERMINISTIC_CALL_PATTERN = re.compile(
    r"\b(datetime\.now\(\s*\)|datetime\.today\(\s*\)"
    r"|random\.(random|randint|choice|shuffle|uniform|sample)\s*\()"
)

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
        if _is_generated_path(relative):
            skipped.append(SkippedTarget(path=relative, reason="generated-path-skipped"))
            continue
        if not _path_matches_filters(path, target_root, include_paths, exclude_paths):
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


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _line_number_from_index(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _line_excerpt(text: str, line_number: int) -> str:
    lines = text.splitlines()
    if 1 <= line_number <= len(lines):
        return lines[line_number - 1].strip()
    return ""


def _todo_matches_from_python_comments(text: str) -> list[int]:
    lines: list[int] = []
    try:
        for token in tokenize.generate_tokens(iter(text.splitlines(keepends=True)).__next__):
            if token.type != tokenize.COMMENT:
                continue
            if TODO_PATTERN.search(token.string):
                lines.append(token.start[0])
    except tokenize.TokenError:
        return []
    return lines


def _todo_matches_from_comment_lines(text: str) -> list[int]:
    lines: list[int] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.lstrip()
        if not stripped.startswith(COMMENT_PREFIXES):
            continue
        if TODO_PATTERN.search(stripped):
            lines.append(line_no)
    return lines


def _scan_todo_markers(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() == ".py":
        line_numbers = _todo_matches_from_python_comments(text)
    elif path.suffix.lower() in {".md", ".txt", ".json"}:
        line_numbers = []
    else:
        line_numbers = _todo_matches_from_comment_lines(text)
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
                priority="P3",
                owner_lane=LANE_HUMAN_JUDGMENT,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _is_bounded_retry_handler(
    handler: ast.ExceptHandler,
    parent_map: dict[ast.AST, ast.AST],
) -> bool:
    """Return True when `except Exception: continue` is inside a loop (bounded retry)."""
    if len(handler.body) != 1 or not isinstance(handler.body[0], ast.Continue):
        return False
    current = parent_map.get(handler)
    while current is not None:
        if isinstance(current, (ast.For, ast.While, ast.AsyncFor)):
            return True
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            break
        current = parent_map.get(current)
    return False


def _is_silent_return_value(node: ast.expr | None) -> bool:
    if node is None:
        return True
    if isinstance(node, ast.Constant):
        return node.value in (None, False, 0, "", b"")
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return len(node.elts) == 0
    if isinstance(node, ast.Dict):
        return len(node.keys) == 0
    return False


def _scan_silent_exception_return(
    path: Path, text: str, target_root: Path, next_id: int
) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() != ".py":
        return findings
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return findings
    for handler in ast.walk(tree):
        if not isinstance(handler, ast.ExceptHandler):
            continue
        # Only flag broad catches (bare except or except Exception)
        if handler.type is not None:
            if not (isinstance(handler.type, ast.Name) and handler.type.id == "Exception"):
                continue
        if len(handler.body) != 1:
            continue
        stmt = handler.body[0]
        if not isinstance(stmt, ast.Return) or not _is_silent_return_value(stmt.value):
            continue
        line = handler.lineno
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-21",
                signal="CI21_SILENT_EXCEPTION_RETURN",
                severity="high",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason="Exception handler returns a silent sentinel value instead of propagating or logging the failure.",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Raise the exception, re-raise with context, or return an explicit error type that callers are required to handle.",
                priority="P1",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _scan_broad_exceptions(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() != ".py":
        return findings
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return findings
    parent_map = _build_parent_map(tree)
    for handler in ast.walk(tree):
        if not isinstance(handler, ast.ExceptHandler):
            continue
        if not isinstance(handler.type, ast.Name) or handler.type.id != "Exception":
            continue
        if handler.name is not None:
            continue
        if _is_bounded_retry_handler(handler, parent_map):
            continue
        line = handler.lineno
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-21",
                signal="CI21_BROAD_EXCEPTION_SWALLOW",
                severity="high",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason="A broad `except Exception:` handler can hide unexpected failures and blur the recovery contract.",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Narrow the exception type or add explicit failure routing that preserves the real error boundary.",
                priority="P1",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _scan_eval_exec(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() != ".py":
        return findings
    for match in EVAL_EXEC_PATTERN.finditer(text):
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
                priority="P1",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _scan_subprocess_shell_true(
    path: Path,
    text: str,
    target_root: Path,
    next_id: int,
) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() != ".py":
        return findings
    for match in SUBPROCESS_SHELL_TRUE_PATTERN.finditer(text):
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
                priority="P1",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _scan_plaintext_secrets(
    path: Path,
    text: str,
    target_root: Path,
    next_id: int,
) -> list[AciFinding]:
    findings: list[AciFinding] = []
    for match in PLAINTEXT_SECRET_PATTERN.finditer(text):
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
                priority="P1",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _scan_insecure_http(
    path: Path,
    text: str,
    target_root: Path,
    next_id: int,
) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() not in {".py", ".json", ".yml", ".yaml", ".toml", ".txt", ".md"}:
        return findings
    for match in INSECURE_HTTP_PATTERN.finditer(text):
        line = _line_number_from_index(text, match.start())
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
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


# ── CI-18 (Parameter Cluster) ──────────────────────────────────────────────

def _build_parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _get_node_docstring(node: ast.AST) -> str | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
        return ast.get_docstring(node)
    return None


def _get_ancestor_docstring(
    node: ast.AST,
    parent_map: dict[ast.AST, ast.AST],
    target_type: type,
) -> str | None:
    current = parent_map.get(node)
    while current is not None:
        if isinstance(current, target_type):
            return _get_node_docstring(current)
        current = parent_map.get(current)
    return None


def _is_boundary_interface_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    if not BOUNDARY_INTERFACE_NAME_PATTERN.match(node.name):
        return False
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    if not body or len(body) > 30:
        return False
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name) and func.id in {
                "_emit", "_notify", "_release_task_lock", "_acquire_task_lock",
                "_record_transition", "_record_violation", "check_and_record", "queue_notification",
            }:
                return True
            if isinstance(func, ast.Attribute) and func.attr in {"execute", "commit", "record", "notify", "write"}:
                return True
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "sys" and func.attr == "exit":
                return True
            if isinstance(func, ast.Name) and func.id in {"print", "_emit"}:
                return True
        elif isinstance(child, ast.Raise):
            return True
        elif isinstance(child, ast.Return) and child.value is not None:
            return True
    return False


def _is_pytest_parametrized_test_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    path: Path,
) -> bool:
    posix = path.as_posix()
    if "/tests/" not in posix and "\\tests\\" not in str(path):
        return False
    if not node.name.startswith("test_"):
        return False
    for dec in getattr(node, "decorator_list", []):
        if not isinstance(dec, ast.Call):
            continue
        func = dec.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "parametrize"
            and isinstance(func.value, ast.Attribute)
            and func.value.attr == "mark"
            and isinstance(func.value.value, ast.Name)
            and func.value.value.id == "pytest"
        ):
            return True
    return False


def _is_non_blocking_logging_helper_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    parent_map: dict[ast.AST, ast.AST],
) -> bool:
    if not LOGGING_HELPER_NAME_PATTERN.match(node.name):
        return False
    docs = [
        _get_node_docstring(node),
        _get_ancestor_docstring(node, parent_map, ast.ClassDef),
        _get_ancestor_docstring(node, parent_map, ast.Module),
    ]
    if not any(d and NON_BLOCKING_HINT_PATTERN.search(d) for d in docs):
        return False
    for child in ast.walk(ast.Module(body=node.body, type_ignores=[])):
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr in {
            "warning", "info", "exception", "error", "debug", "add", "commit",
        }:
            return True
    return False


def _scan_parameter_clusters(paths: list[Path], root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    for path in [p for p in paths if p.suffix.lower() == ".py"]:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        parent_map = _build_parent_map(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            arg_names = [a.arg for a in node.args.args if a.arg not in {"self", "cls"}]
            if len(arg_names) < 5:
                continue
            if _is_boundary_interface_function(node):
                continue
            if _is_pytest_parametrized_test_function(node, path):
                continue
            if _is_non_blocking_logging_helper_function(node, parent_map):
                continue
            findings.append(
                build_finding(
                    finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                    ci_id="CI-18",
                    signal="CI18_PARAMETER_CLUSTER",
                    severity="medium",
                    target_file=_relative_path(path, root),
                    line=node.lineno,
                    excerpt=f"def {node.name}({', '.join(arg_names[:5])}{'...' if len(arg_names) > 5 else ''})",
                    reason=f"Function takes {len(arg_names)} positional arguments; consider a named parameter object.",
                    evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                    recommended_action="Group related parameters into a named data structure or configuration object.",
                    priority="P2",
                    owner_lane=LANE_NATIVE_STATIC,
                    verification_status=VERIFICATION_EXECUTED,
                )
            )
    return findings


# ── CI-20 (Scattered Constant) ─────────────────────────────────────────────

def _is_low_information_scattered_literal(text: str) -> bool:
    if text in LOW_INFO_SCATTERED_LITERALS:
        return True
    if text == CODE_FENCE_SPLITTER_LITERAL:
        return True
    if text.endswith(LOW_INFO_SCATTERED_LITERAL_SUFFIXES):
        return True
    if WINDOWS_PROJECT_PATH_LITERAL_PATTERN.match(text):
        return True
    if PYTHON_DUNDER_LITERAL_PATTERN.match(text):
        return True
    if text in ARGPARSE_ACTION_LITERALS:
        return True
    return False


def _is_contract_field_literal_context(
    node: ast.Constant,
    parent_map: dict[ast.AST, ast.AST],
) -> bool:
    parent = parent_map.get(node)
    grandparent = parent_map.get(parent) if parent is not None else None
    if isinstance(parent, ast.Dict):
        if node in parent.keys:
            return True
        if node in parent.values:
            vals = [v.value for v in parent.values if isinstance(v, ast.Constant) and isinstance(v.value, str)]
            if vals and all(CONTRACT_FIELD_LITERAL_PATTERN.match(v) for v in vals):
                return True
    if isinstance(parent, ast.Call):
        func = parent.func
        if isinstance(func, ast.Attribute) and func.attr in {"get", "pop", "setdefault"}:
            return bool(parent.args) and parent.args[0] is node
        if isinstance(func, ast.Attribute) and func.attr == "label":
            return bool(parent.args) and parent.args[0] is node
    if isinstance(parent, ast.Subscript):
        return parent.slice is node
    if isinstance(parent, (ast.List, ast.Tuple, ast.Set)) and isinstance(grandparent, ast.Assign):
        targets = [t.id for t in grandparent.targets if isinstance(t, ast.Name)]
        if any(tok in name.lower() for name in targets for tok in ("field", "column", "col", "key")):
            return True
    if isinstance(parent, ast.keyword) and parent.arg in {"fieldnames", "columns", "keys"}:
        return True
    return False


def _is_contract_field_literal_family(
    literal: str,
    refs: list[tuple[Path, int, bool]],
) -> bool:
    if not CONTRACT_FIELD_LITERAL_PATTERN.match(literal) or len(refs) < 3:
        return False
    return sum(1 for _, _, ctx in refs if ctx) / len(refs) >= 0.75


def _is_date_format_literal_family(
    literal: str,
    refs: list[tuple[Path, int, bool]],
) -> bool:
    return len(refs) >= 3 and "%" in literal and all(t in literal for t in ("%Y", "%m", "%d"))


def _is_api_route_literal_family(
    literal: str,
    refs: list[tuple[Path, int, bool]],
) -> bool:
    return len(refs) >= 3 and literal.startswith("/api/")


def _is_test_memory_sqlite_literal_family(
    literal: str,
    refs: list[tuple[Path, int, bool]],
) -> bool:
    return (
        literal == "sqlite:///:memory:"
        and len(refs) >= 3
        and all("/tests/" in p.as_posix() for p, _, _ in refs)
    )


def _is_severity_literal_family(
    literal: str,
    refs: list[tuple[Path, int, bool]],
) -> bool:
    return len(refs) >= 3 and literal in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "WARN", "ERROR"}


def _scan_scattered_constants(paths: list[Path], root: Path, next_id: int) -> list[AciFinding]:
    occurrences: dict[str, list[tuple[Path, int, bool]]] = {}
    for path in [p for p in paths if p.suffix.lower() == ".py"]:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        parent_map = _build_parent_map(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            text = node.value.strip()
            if len(text) < 8 or " " in text:
                continue
            if _is_low_information_scattered_literal(text):
                continue
            occurrences.setdefault(text, []).append(
                (path, getattr(node, "lineno", 0), _is_contract_field_literal_context(node, parent_map))
            )
    findings: list[AciFinding] = []
    for literal, refs in occurrences.items():
        if _is_contract_field_literal_family(literal, refs):
            continue
        if _is_date_format_literal_family(literal, refs):
            continue
        if _is_api_route_literal_family(literal, refs):
            continue
        if _is_test_memory_sqlite_literal_family(literal, refs):
            continue
        if _is_severity_literal_family(literal, refs):
            continue
        distinct = {_relative_path(p, root) for p, _, _ in refs}
        if len(distinct) < 3:
            continue
        first_path, first_line, _ = refs[0]
        files_sample = ", ".join(sorted(distinct)[:3])
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-20",
                signal="CI20_SCATTERED_CONSTANT",
                severity="medium",
                target_file=_relative_path(first_path, root),
                line=first_line or None,
                excerpt=repr(literal),
                reason=f"String constant appears in {len(distinct)} files without a single defining owner: {files_sample}",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Extract the shared constant into a named symbol at its canonical owner and import from there.",
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


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
                    target_file=_relative_path(path, root),
                    line=lineno,
                    excerpt=line.strip(),
                    reason="A secondary program or concern appears to be treated as an authority surface.",
                    evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                )
            )
    return findings



# ── CI-22 (Resource Lifecycle Leak) ───────────────────────────────────────

def _scan_resource_lifecycle_leak(
    path: Path, text: str, target_root: Path, next_id: int
) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    # Collect Call nodes that are already in a with-statement context_expr
    with_wrapped: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                with_wrapped.add(id(item.context_expr))
                # Also allow resource openers passed as args to a wrapper (e.g. contextlib.closing)
                if isinstance(item.context_expr, ast.Call):
                    for arg in item.context_expr.args:
                        with_wrapped.add(id(arg))

    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if id(node) in with_wrapped:
            continue
        if isinstance(node.func, ast.Name):
            fname = node.func.id
        elif isinstance(node.func, ast.Attribute):
            fname = node.func.attr
        else:
            continue
        if fname not in RESOURCE_OPENER_NAMES:
            continue
        line = node.lineno
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-22",
                signal="CI22_RESOURCE_CLEANUP_GAP",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason=(
                    f"'{fname}' opens a resource without a context manager; "
                    "the lifecycle may not be closed on exception paths."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action=(
                    "Wrap resource-opening calls in a 'with' statement to ensure "
                    "deterministic cleanup."
                ),
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


# ── CI-23 (Contract Field Drift) ───────────────────────────────────────────

def _scan_contract_field_drift(
    path: Path, text: str, target_root: Path, next_id: int
) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.args.kwarg is None:
            continue
        kwargs_name = node.args.kwarg.arg
        body_mod = ast.Module(body=node.body, type_ignores=[])
        hidden_fields: dict[str, int] = {}
        for child in ast.walk(body_mod):
            # kwargs["key"] pattern
            if (
                isinstance(child, ast.Subscript)
                and isinstance(child.value, ast.Name)
                and child.value.id == kwargs_name
                and isinstance(child.slice, ast.Constant)
                and isinstance(child.slice.value, str)
            ):
                field = child.slice.value
                if field not in hidden_fields:
                    hidden_fields[field] = child.lineno
            # kwargs.get("key") pattern
            elif (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and isinstance(child.func.value, ast.Name)
                and child.func.value.id == kwargs_name
                and child.func.attr == "get"
                and child.args
                and isinstance(child.args[0], ast.Constant)
                and isinstance(child.args[0].value, str)
            ):
                field = child.args[0].value
                if field not in hidden_fields:
                    hidden_fields[field] = child.lineno
        if len(hidden_fields) < 2:
            continue
        field_list = ", ".join(f'"{f}"' for f in sorted(hidden_fields.keys())[:5])
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-23",
                signal="CI23_CONTRACT_FIELD_DRIFT",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=node.lineno,
                excerpt=_line_excerpt(text, node.lineno),
                reason=(
                    f"Function '{node.name}' hides {len(hidden_fields)} implicit field(s) "
                    f"({field_list}) inside **{kwargs_name}; the call contract is invisible to callers."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action=(
                    "Replace **kwargs with explicit named parameters or a typed "
                    "dataclass/TypedDict to make the field contract visible and checkable."
                ),
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


# ── CI-25 (Environment Drift) ──────────────────────────────────────────────

def _scan_environment_drift(
    path: Path, text: str, target_root: Path, next_id: int
) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    findings: list[AciFinding] = []
    for match in NONDETERMINISTIC_CALL_PATTERN.finditer(text):
        line = _line_number_from_index(text, match.start())
        call_text = match.group(0).rstrip("(")
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-25",
                signal="CI25_ENVIRONMENT_DRIFT",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason=(
                    f"'{call_text}' produces results that vary between runs or environments; "
                    "behavior may differ unpredictably in CI, replay, or multi-environment deployments."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action=(
                    "Inject time/randomness as explicit parameters or use "
                    "timezone-aware datetime (datetime.now(UTC)) so callers control determinism."
                ),
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


# ── CI-26 (Race Hazard) ────────────────────────────────────────────────────

def _scan_race_hazard(
    path: Path, text: str, target_root: Path, next_id: int
) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body_mod = ast.Module(body=node.body, type_ignores=[])
        for child in ast.walk(body_mod):
            if not isinstance(child, ast.Global):
                continue
            for name in child.names:
                findings.append(
                    build_finding(
                        finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                        ci_id="CI-26",
                        signal="CI26_RACE_HAZARD",
                        severity="medium",
                        target_file=_relative_path(path, target_root),
                        line=child.lineno,
                        excerpt=_line_excerpt(text, child.lineno),
                        reason=(
                            f"Function '{node.name}' modifies module-level state '{name}' via "
                            "'global'; concurrent calls share this mutable state without explicit "
                            "synchronization."
                        ),
                        evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                        recommended_action=(
                            "Eliminate the global by passing state as a parameter, using a class, "
                            "or protecting with a threading.Lock / asyncio.Lock."
                        ),
                        priority="P2",
                        owner_lane=LANE_NATIVE_STATIC,
                        verification_status=VERIFICATION_EXECUTED,
                    )
                )
    return findings


# ── CI-02 (Spaghetti Code) ────────────────────────────────────────────────

def _max_control_flow_depth(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    CONTROL_TYPES = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.AsyncWith)

    def _depth(node: ast.AST, d: int) -> int:
        if isinstance(node, CONTROL_TYPES):
            d += 1
        best = d
        if isinstance(node, ast.If):
            for stmt in node.body:
                best = max(best, _depth(stmt, d))
            # elif is orelse:[If(...)]: traverse at same depth to avoid double-counting
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                best = max(best, _depth(node.orelse[0], d - 1))
            else:
                for stmt in node.orelse:
                    best = max(best, _depth(stmt, d))
        else:
            for child in ast.iter_child_nodes(node):
                best = max(best, _depth(child, d))
        return best

    body_mod = ast.Module(body=func_node.body, type_ignores=[])
    return _depth(body_mod, 0)


def _scan_long_functions(
    path: Path, text: str, target_root: Path, next_id: int
) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not hasattr(node, "end_lineno") or node.end_lineno is None:
            continue
        body_lines = node.end_lineno - node.lineno
        if body_lines < CI02_LONG_FUNCTION_THRESHOLD:
            continue
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-02",
                signal="CI02_LONG_FUNCTION",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=node.lineno,
                excerpt=f"def {node.name}(...)",
                reason=(
                    f"Function body spans {body_lines} lines, "
                    f"exceeding the {CI02_LONG_FUNCTION_THRESHOLD}-line threshold."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Extract cohesive sub-operations into named helper functions.",
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


CI04_METHOD_COUNT_THRESHOLD = 15
CI04_ATTRIBUTE_COUNT_THRESHOLD = 10


def _count_non_dunder_methods(class_node: ast.ClassDef) -> int:
    return sum(
        1 for node in class_node.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not (node.name.startswith("__") and node.name.endswith("__"))
    )


def _count_instance_attributes(class_node: ast.ClassDef) -> int:
    attrs: set[str] = set()
    for node in ast.walk(class_node):
        if not isinstance(node, ast.FunctionDef) or node.name != "__init__":
            continue
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        attrs.add(target.attr)
            elif isinstance(stmt, ast.AnnAssign):
                if (
                    isinstance(stmt.target, ast.Attribute)
                    and isinstance(stmt.target.value, ast.Name)
                    and stmt.target.value.id == "self"
                ):
                    attrs.add(stmt.target.attr)
    return len(attrs)


def _scan_god_class(
    path: Path, text: str, target_root: Path, next_id: int
) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        method_count = _count_non_dunder_methods(node)
        attr_count = _count_instance_attributes(node)
        if method_count <= CI04_METHOD_COUNT_THRESHOLD and attr_count <= CI04_ATTRIBUTE_COUNT_THRESHOLD:
            continue
        reason_parts = []
        if method_count > CI04_METHOD_COUNT_THRESHOLD:
            reason_parts.append(
                f"{method_count} non-dunder methods (threshold: {CI04_METHOD_COUNT_THRESHOLD})"
            )
        if attr_count > CI04_ATTRIBUTE_COUNT_THRESHOLD:
            reason_parts.append(
                f"{attr_count} instance attributes (threshold: {CI04_ATTRIBUTE_COUNT_THRESHOLD})"
            )
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-04",
                signal="CI04_GOD_CLASS",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=node.lineno,
                excerpt=f"class {node.name}",
                reason=f"Class {node.name!r} shows God Class indicators: {'; '.join(reason_parts)}.",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action=(
                    "Split responsibilities into focused classes or extract cohesive groups "
                    "of methods and attributes into separate units."
                ),
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _scan_spaghetti_code(
    path: Path, text: str, target_root: Path, next_id: int
) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        depth = _max_control_flow_depth(node)
        if depth < CI02_NESTING_THRESHOLD:
            continue
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-02",
                signal="CI02_SPAGHETTI_CODE",
                severity="medium",
                target_file=_relative_path(path, target_root),
                line=node.lineno,
                excerpt=f"def {node.name}(...) [nesting depth {depth}]",
                reason=(
                    f"Function '{node.name}' has control-flow nesting depth {depth}; "
                    "tangled branching obscures state movement and makes the function hard to follow."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Extract inner blocks into named helper functions to flatten the control flow.",
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


# ── CI-05 (Copy-Paste Programming) ────────────────────────────────────────

def _function_body_content(node: ast.FunctionDef | ast.AsyncFunctionDef, text: str) -> tuple[str, ...] | None:
    if not hasattr(node, "end_lineno") or node.end_lineno is None:
        return None
    lines = text.splitlines()
    body_lines = lines[node.lineno : node.end_lineno]
    stripped = [ln.strip() for ln in body_lines if ln.strip()]
    # skip leading docstring
    if stripped and (stripped[0].startswith('"""') or stripped[0].startswith("'''")):
        for i, ln in enumerate(stripped):
            if i > 0 and (ln.endswith('"""') or ln.endswith("'''")):
                stripped = stripped[i + 1 :]
                break
    if len(stripped) < 4:
        return None
    return tuple(stripped)


def _scan_copy_paste_code(paths: list[Path], root: Path, next_id: int) -> list[AciFinding]:
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
                priority="P2",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


# ── CI-06 (Magic Number) ──────────────────────────────────────────────────

def _scan_magic_numbers(paths: list[Path], root: Path, next_id: int) -> list[AciFinding]:
    occurrences: dict[int | float, list[tuple[Path, int]]] = {}
    for path in [p for p in paths if p.suffix.lower() == ".py"]:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(text)
        except SyntaxError:
            continue
        parent_map = _build_parent_map(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue
            val = node.value
            if isinstance(val, bool):
                continue
            if not isinstance(val, (int, float)):
                continue
            if val in CI06_TRIVIAL_NUMBERS:
                continue
            parent = parent_map.get(node)
            # skip if inside a UnaryOp (negative literal component — avoid double-counting)
            if isinstance(parent, ast.UnaryOp):
                continue
            # skip function parameter defaults (e.g. limit=30, offset=0)
            if isinstance(parent, ast.arguments):
                continue
            # skip named constant definitions (UPPER_CASE = <value>)
            if isinstance(parent, ast.Assign):
                if any(isinstance(t, ast.Name) and t.id.isupper() for t in parent.targets):
                    continue
            occurrences.setdefault(val, []).append((path, getattr(node, "lineno", 0)))

    findings: list[AciFinding] = []
    for val, refs in occurrences.items():
        distinct = {_relative_path(p, root) for p, _ in refs}
        if len(distinct) < 3:
            continue
        first_path, first_line = refs[0]
        files_sample = ", ".join(sorted(distinct)[:3])
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-06",
                signal="CI06_MAGIC_NUMBER",
                severity="low",
                target_file=_relative_path(first_path, root),
                line=first_line,
                excerpt=repr(val),
                reason=(
                    f"Numeric literal {val!r} appears across {len(distinct)} files without a named constant: "
                    f"{files_sample}"
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Define the value as a named constant at a canonical owner and import it from there.",
                priority="P3",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


# ── CI-12 (Poltergeist) ───────────────────────────────────────────────────

def _get_init_single_delegate(init_node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """If __init__ stores exactly one external arg as self.X, return attribute name; else None."""
    if len(init_node.args.args) != 2:  # self + one arg only
        return None
    real_body = [
        s for s in init_node.body
        if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
    ]
    if len(real_body) != 1 or not isinstance(real_body[0], ast.Assign):
        return None
    stmt = real_body[0]
    if len(stmt.targets) != 1:
        return None
    target = stmt.targets[0]
    if not (
        isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == "self"
    ):
        return None
    return target.attr


def _is_method_pure_delegation(
    method: ast.FunctionDef | ast.AsyncFunctionDef,
    delegate_attr: str,
) -> bool:
    real_body = [
        s for s in method.body
        if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
    ]
    if not real_body or len(real_body) > 2:
        return False
    for stmt in real_body:
        call = None
        if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
            call = stmt.value
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
        if call is None:
            return False
        if not (
            isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Attribute)
            and isinstance(call.func.value.value, ast.Name)
            and call.func.value.value.id == "self"
            and call.func.value.attr == delegate_attr
        ):
            return False
    return True


def _scan_poltergeist(
    path: Path, text: str, target_root: Path, next_id: int
) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if node.bases:
            continue
        init = next(
            (m for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == "__init__"),
            None,
        )
        if init is None:
            continue
        delegate_attr = _get_init_single_delegate(init)
        if delegate_attr is None:
            continue
        public_methods = [
            m for m in node.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not m.name.startswith("__")
        ]
        if not public_methods or len(public_methods) > 3:
            continue
        if not all(_is_method_pure_delegation(m, delegate_attr) for m in public_methods):
            continue
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-12",
                signal="CI12_POLTERGEIST",
                severity="low",
                target_file=_relative_path(path, target_root),
                line=node.lineno,
                excerpt=f"class {node.name}",
                reason=(
                    f"Class '{node.name}' wraps a single dependency and delegates all "
                    f"{len(public_methods)} public method(s) without adding logic."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Remove the wrapper class and call the underlying object directly.",
                priority="P3",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


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
    threshold_levels = set(gate["blocking_severities"])  # type: ignore[arg-type]
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

    for file_path in target_files:
        text = file_path.read_text(encoding="utf-8", errors="ignore")

        if "CI03_TODO_HACK" in active_signals:
            todo_findings = _scan_todo_markers(file_path, text, session.target_root, next_id)
            next_id += len(todo_findings)
            findings.extend(todo_findings)

        if "CI21_BROAD_EXCEPTION_SWALLOW" in active_signals:
            broad_findings = _scan_broad_exceptions(file_path, text, session.target_root, next_id)
            next_id += len(broad_findings)
            findings.extend(broad_findings)

        if "CI21_SILENT_EXCEPTION_RETURN" in active_signals:
            silent_findings = _scan_silent_exception_return(file_path, text, session.target_root, next_id)
            next_id += len(silent_findings)
            findings.extend(silent_findings)

        if "CI14_DYNAMIC_CODE_EXECUTION" in active_signals:
            eval_findings = _scan_eval_exec(file_path, text, session.target_root, next_id)
            next_id += len(eval_findings)
            findings.extend(eval_findings)

        if "CI14_SUBPROCESS_SHELL_TRUE" in active_signals:
            shell_findings = _scan_subprocess_shell_true(file_path, text, session.target_root, next_id)
            next_id += len(shell_findings)
            findings.extend(shell_findings)

        if "CI14_PLAINTEXT_SECRET" in active_signals:
            secret_findings = _scan_plaintext_secrets(file_path, text, session.target_root, next_id)
            next_id += len(secret_findings)
            findings.extend(secret_findings)

        if "CI14_INSECURE_HTTP" in active_signals:
            http_findings = _scan_insecure_http(file_path, text, session.target_root, next_id)
            next_id += len(http_findings)
            findings.extend(http_findings)

        if "CI22_RESOURCE_CLEANUP_GAP" in active_signals:
            ci22 = _scan_resource_lifecycle_leak(file_path, text, session.target_root, next_id)
            next_id += len(ci22)
            findings.extend(ci22)

        if "CI23_CONTRACT_FIELD_DRIFT" in active_signals:
            ci23 = _scan_contract_field_drift(file_path, text, session.target_root, next_id)
            next_id += len(ci23)
            findings.extend(ci23)

        if "CI25_ENVIRONMENT_DRIFT" in active_signals:
            ci25 = _scan_environment_drift(file_path, text, session.target_root, next_id)
            next_id += len(ci25)
            findings.extend(ci25)

        if "CI26_RACE_HAZARD" in active_signals:
            ci26 = _scan_race_hazard(file_path, text, session.target_root, next_id)
            next_id += len(ci26)
            findings.extend(ci26)

        if "CI02_SPAGHETTI_CODE" in active_signals:
            ci02 = _scan_spaghetti_code(file_path, text, session.target_root, next_id)
            next_id += len(ci02)
            findings.extend(ci02)

        if "CI02_LONG_FUNCTION" in active_signals:
            long_fn = _scan_long_functions(file_path, text, session.target_root, next_id)
            next_id += len(long_fn)
            findings.extend(long_fn)

        if "CI04_GOD_CLASS" in active_signals:
            god_class = _scan_god_class(file_path, text, session.target_root, next_id)
            next_id += len(god_class)
            findings.extend(god_class)

        if "CI12_POLTERGEIST" in active_signals:
            ci12 = _scan_poltergeist(file_path, text, session.target_root, next_id)
            next_id += len(ci12)
            findings.extend(ci12)

    # Cross-file detectors (run once over all collected files)
    if "CI18_PARAMETER_CLUSTER" in active_signals:
        ci18 = _scan_parameter_clusters(target_files, session.target_root, next_id)
        next_id += len(ci18)
        findings.extend(ci18)

    if "CI20_SCATTERED_CONSTANT" in active_signals:
        ci20 = _scan_scattered_constants(target_files, session.target_root, next_id)
        next_id += len(ci20)
        findings.extend(ci20)

    if "CI05_COPY_PASTE_CODE" in active_signals:
        ci05 = _scan_copy_paste_code(target_files, session.target_root, next_id)
        next_id += len(ci05)
        findings.extend(ci05)

    if "CI06_MAGIC_NUMBER" in active_signals:
        ci06 = _scan_magic_numbers(target_files, session.target_root, next_id)
        next_id += len(ci06)
        findings.extend(ci06)

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
