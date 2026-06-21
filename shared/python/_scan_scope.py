#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan scope resolution and file traversal.

One concern: decide which files are in scope (scope modes, scope-class
classification, include/exclude filters, generated/binary skipping, git-diff
narrowing) and deterministically iterate the target tree. Owns the scope
vocabulary constants. Pure/read-only; never executes or imports scanned files.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath
import re
import subprocess

try:
    from .detectors._helpers import _relative_path
    from .aci_profiles import default_external_analyzers
except ImportError:  # pragma: no cover - direct script/module import path
    from detectors._helpers import _relative_path  # type: ignore[no-redef]
    from aci_profiles import default_external_analyzers  # type: ignore[no-redef]


TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".cs",
    ".kt",
    ".kts",
    ".sh",
    ".bash",
    ".sql",
    ".tf",
    ".hcl",
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
    "bower_components",
    # Vendored third-party code: bundled into the project but not its own source,
    # so findings there are noise the maintainer cannot act on (e.g. pip/_vendor,
    # setuptools/_vendor). Common conventions across ecosystems.
    "_vendor",
    "vendor",
    "vendored",
    "third_party",
    "third-party",
    "site-packages",
    # Local tool state and session scratch space (non-canonical; never in distributed packages)
    ".claude",
    "workspace",
}

SCOPE_MODE_FULL_REPO = "full-repo"

SCOPE_MODE_SOURCE_ONLY = "source-only"

SCOPE_MODE_DOGFOOD = "dogfood"

SCOPE_MODE_SELF_AUDIT = "self-audit"

SUPPORTED_SCOPE_MODES = (
    SCOPE_MODE_SOURCE_ONLY,
    SCOPE_MODE_FULL_REPO,
    SCOPE_MODE_DOGFOOD,
    SCOPE_MODE_SELF_AUDIT,
)

SCOPE_CLASS_RUNTIME_SOURCE = "runtime-source"

SCOPE_CLASS_TESTS = "tests"

SCOPE_CLASS_FIXTURES = "fixtures"

SCOPE_CLASS_DOCS_EVIDENCE = "docs-evidence"

SCOPE_CLASS_ROADMAP_EVIDENCE = "roadmap-evidence"

SCOPE_CLASS_MAINTAINER_PROBES = "maintainer-probes"

SCOPE_CLASS_SUPPORT = "support"

SCOPE_CLASS_GENERATED = "generated"

_NON_RUNTIME_PATH_CANDIDATES = (
    ".github",
    ".claude",
    "archive",
    "build",
    "common",
    "dist",
    "docs",
    "example",
    "examples",
    "fixture",
    "fixtures",
    "sample",
    "samples",
    "shared/report/examples",
    "workspace",
)

_SOURCE_ONLY_EXCLUDE_CANDIDATES = _NON_RUNTIME_PATH_CANDIDATES + (
    "shared/tools",
    "test",
    "tests",
    "shared/tests",
)

_DOGFOOD_INCLUDE_CANDIDATES = (
    "src",
    "app",
    "lib",
    "shared/python",
    "domains",
    "tests",
    "shared/tests",
)

_SELF_AUDIT_INCLUDE_CANDIDATES = (
    "shared/python",
    "domains",
    "tests",
    "shared/tests",
    "shared/tools",
    "docs/roadmap",
)

_SUPPORT_ONLY_HTTP_SCOPE_CLASSES: frozenset[str] = frozenset({
    SCOPE_CLASS_DOCS_EVIDENCE,
    SCOPE_CLASS_ROADMAP_EVIDENCE,
    SCOPE_CLASS_TESTS,
    SCOPE_CLASS_MAINTAINER_PROBES,
    SCOPE_CLASS_SUPPORT,
})

@dataclass(frozen=True)
class SkippedTarget:
    path: str
    reason: str

def _is_supported_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in {"Dockerfile", "Containerfile"}

def _has_suffix(paths: list[Path], *suffixes: str) -> bool:
    wanted = {suffix.lower() for suffix in suffixes}
    return any(path.suffix.lower() in wanted for path in paths)

def _existing_scope_paths(target_root: Path, candidates: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        candidate.replace("\\", "/").strip("/")
        for candidate in candidates
        if (target_root / candidate).exists()
    )

def _resolve_scope_filters(
    target_root: Path,
    scope_mode: str,
    include_paths: tuple[str, ...],
    exclude_paths: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    normalized_include = tuple(item.replace("\\", "/").strip("/") for item in include_paths if item)
    normalized_exclude = tuple(item.replace("\\", "/").strip("/") for item in exclude_paths if item)

    if scope_mode == SCOPE_MODE_FULL_REPO:
        return normalized_include, normalized_exclude

    if scope_mode == SCOPE_MODE_SOURCE_ONLY:
        preset_exclude = _existing_scope_paths(target_root, _SOURCE_ONLY_EXCLUDE_CANDIDATES)
        return normalized_include, tuple(sorted(set(normalized_exclude) | set(preset_exclude)))

    if scope_mode == SCOPE_MODE_DOGFOOD:
        preset_include = _existing_scope_paths(target_root, _DOGFOOD_INCLUDE_CANDIDATES)
        preset_exclude = _existing_scope_paths(target_root, _NON_RUNTIME_PATH_CANDIDATES)
        merged_include = normalized_include or preset_include
        merged_exclude = tuple(sorted(set(normalized_exclude) | set(preset_exclude)))
        if merged_include:
            return merged_include, merged_exclude
        return _resolve_scope_filters(target_root, SCOPE_MODE_SOURCE_ONLY, normalized_include, normalized_exclude)

    if scope_mode == SCOPE_MODE_SELF_AUDIT:
        preset_include = _existing_scope_paths(target_root, _SELF_AUDIT_INCLUDE_CANDIDATES)
        merged_include = normalized_include or preset_include
        return merged_include, normalized_exclude

    raise ValueError(f"Unsupported scope_mode: {scope_mode}")

def _classify_relative_path(relative_path: str) -> str:
    posix = relative_path.replace("\\", "/").strip("/")
    pure = PurePosixPath(posix)
    parts = set(pure.parts)
    name = pure.name

    if parts & DEFAULT_GENERATED_PATH_SEGMENTS:
        return SCOPE_CLASS_GENERATED
    if pure.parts[:2] == ("shared", "tools"):
        return SCOPE_CLASS_MAINTAINER_PROBES
    if pure.parts[:2] == ("docs", "roadmap"):
        return SCOPE_CLASS_ROADMAP_EVIDENCE
    if parts & {"example", "examples", "fixture", "fixtures", "sample", "samples"}:
        return SCOPE_CLASS_FIXTURES
    if parts & {"docs", "doc", ".github"}:
        return SCOPE_CLASS_DOCS_EVIDENCE
    if "tests" in parts or name.startswith("test_") or pure.stem.endswith("_test"):
        return SCOPE_CLASS_TESTS
    if pure.name in {"Dockerfile", "Containerfile"} or pure.suffix.lower() in {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".cs", ".kt", ".kts",
        ".sh", ".bash", ".sql", ".tf", ".hcl", ".yaml", ".yml", ".toml", ".json",
    }:
        return SCOPE_CLASS_RUNTIME_SOURCE
    return SCOPE_CLASS_SUPPORT

def _gate_scope_classes(scope_mode: str) -> tuple[str, ...]:
    if scope_mode in SUPPORTED_SCOPE_MODES:
        return (SCOPE_CLASS_RUNTIME_SOURCE,)
    raise ValueError(f"Unsupported scope_mode: {scope_mode}")

def _select_external_analyzers(
    profile_id: str,
    target_files: list[Path],
    target_root: Path,
) -> tuple[str, ...]:
    has_runtime_source = any(
        _classify_relative_path(_relative_path(path, target_root)) == SCOPE_CLASS_RUNTIME_SOURCE
        for path in target_files
    )
    available_suffixes = {
        ".py": _has_suffix(target_files, ".py"),
        ".js-ts": _has_suffix(target_files, ".js", ".jsx", ".ts", ".tsx"),
        ".ts": _has_suffix(target_files, ".ts", ".tsx"),
        ".sh": _has_suffix(target_files, ".sh", ".bash"),
        ".sql": _has_suffix(target_files, ".sql"),
    }

    def _is_applicable(analyzer_id: str) -> bool:
        if analyzer_id in {"ruff", "pyflakes", "mypy", "pytest"}:
            return available_suffixes[".py"]
        if analyzer_id == "semgrep":
            return has_runtime_source
        if analyzer_id == "eslint":
            return available_suffixes[".js-ts"]
        if analyzer_id == "tsc":
            return available_suffixes[".ts"] and (target_root / "tsconfig.json").is_file()
        if analyzer_id == "shellcheck":
            return available_suffixes[".sh"]
        if analyzer_id == "sqlfluff":
            return available_suffixes[".sql"]
        return False

    return tuple(
        analyzer_id
        for analyzer_id in default_external_analyzers(profile_id)
        if _is_applicable(analyzer_id)
    )

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

def _git_changed_files(target_root: Path, ref: str) -> frozenset[str]:
    """Return target-root-relative POSIX paths of files changed since *ref*.

    Runs ``git diff --name-only <ref> --`` from *target_root* and normalizes
    the output (git-root-relative) to be relative to *target_root*.  Files
    outside *target_root* are silently skipped.  Raises ValueError when git is
    not available, the repository is not found, or the ref is invalid.
    """
    try:
        diff_result = subprocess.run(
            ["git", "diff", "--name-only", ref, "--"],
            cwd=target_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        toplevel_result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=target_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError as exc:
        raise ValueError("git is not available on PATH; --diff-from requires a git installation") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"git diff timed out for ref {ref!r} in {target_root}") from exc
    if diff_result.returncode != 0:
        detail = diff_result.stderr.strip() or "no stderr"
        raise ValueError(f"git diff --name-only {ref!r} failed in {target_root}: {detail}")
    git_root = (
        Path(toplevel_result.stdout.strip()).resolve()
        if toplevel_result.returncode == 0
        else target_root.resolve()
    )
    target_abs = target_root.resolve()
    changed: set[str] = set()
    for line in diff_result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        abs_path = git_root / line
        try:
            changed.add(abs_path.relative_to(target_abs).as_posix())
        except ValueError:
            pass  # changed file is outside target_root; skip
    return frozenset(changed)


_DIFF_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def _git_changed_lines(target_root: Path, ref: str) -> dict[str, set[int]]:
    """Return target-root-relative POSIX path -> set of changed (added) line numbers.

    Runs ``git diff --unified=0 <ref> --`` and parses each hunk header, so a
    finding can be scoped to the lines a change actually touched rather than to
    the whole changed file. Same git-root normalization and error handling as
    ``_git_changed_files``; raises ValueError on git/ref problems.
    """
    try:
        diff_result = subprocess.run(
            ["git", "diff", "--unified=0", ref, "--"],
            cwd=target_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        toplevel_result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=target_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError as exc:
        raise ValueError("git is not available on PATH; --diff-from requires a git installation") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"git diff timed out for ref {ref!r} in {target_root}") from exc
    if diff_result.returncode != 0:
        detail = diff_result.stderr.strip() or "no stderr"
        raise ValueError(f"git diff --unified=0 {ref!r} failed in {target_root}: {detail}")
    git_root = (
        Path(toplevel_result.stdout.strip()).resolve()
        if toplevel_result.returncode == 0
        else target_root.resolve()
    )
    target_abs = target_root.resolve()
    changed: dict[str, set[int]] = {}
    current_rel: str | None = None
    for line in diff_result.stdout.splitlines():
        if line.startswith("+++ "):
            raw = line[4:].strip()
            if raw == "/dev/null":
                current_rel = None
                continue
            if raw.startswith("b/"):
                raw = raw[2:]
            abs_path = git_root / raw
            try:
                current_rel = abs_path.relative_to(target_abs).as_posix()
            except ValueError:
                current_rel = None
            continue
        if current_rel is None:
            continue
        match = _DIFF_HUNK_RE.match(line)
        if match:
            start = int(match.group(1))
            count = int(match.group(2) or "1")
            if count == 0:
                # a pure deletion hunk; attribute to the surrounding line
                changed.setdefault(current_rel, set()).add(start)
            else:
                changed.setdefault(current_rel, set()).update(range(start, start + count))
    return changed

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
