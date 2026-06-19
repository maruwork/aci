"""External-analyzer command builders and source discovery.

One concern: given a target tree, decide each analyzer's argv and which source
files / configs apply. No finding normalization (that is _analyzer_parsers) and
no execution (that is aci_analyzer_execution).
"""
from __future__ import annotations

from pathlib import Path
import sys


def _ruff_command(target_root: Path) -> list[str]:
    return ["ruff", "check", str(target_root), "--output-format", "json"]


def _pyflakes_command(target_root: Path) -> list[str]:
    return ["pyflakes", str(target_root)]


_PYTHON_ANALYZER_SKIP_SEGMENTS: frozenset[str] = frozenset({
    ".git", "__pycache__", ".venv", "venv", "env", "node_modules", "dist", ".tox",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "aci.egg-info",
    ".claude", "archive", "common", "workspace",
})


_PYTEST_CANDIDATE_PATHS: tuple[str, ...] = ("shared/tests", "tests", "test", "spec", "specs")


def _relative_parts(path: Path, target_root: Path) -> tuple[str, ...]:
    try:
        return path.relative_to(target_root).parts
    except ValueError:
        return path.parts


def _find_python_files(target_root: Path) -> list[str]:
    return sorted(
        str(p)
        for p in target_root.rglob("*.py")
        if p.is_file() and not any(seg in _PYTHON_ANALYZER_SKIP_SEGMENTS for seg in _relative_parts(p, target_root))
    )


def _mypy_command(target_root: Path, python_files: list[str]) -> list[str]:
    command = [
        "mypy",
        "--namespace-packages",
        "--explicit-package-bases",
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


def _pytest_targets(target_root: Path) -> list[str]:
    targets = [str(target_root / candidate) for candidate in _PYTEST_CANDIDATE_PATHS if (target_root / candidate).exists()]
    return targets or [str(target_root)]


def _pytest_command(target_root: Path) -> list[str]:
    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    workspace_dir = target_root / "workspace"
    if workspace_dir.is_dir():
        command.extend(["--ignore", str(workspace_dir)])
        command.extend(["--basetemp", str(workspace_dir / ".aci-pytest-tmp")])
    command.extend(_pytest_targets(target_root))
    return command


_SEMGREP_SUPPORTED_SUFFIXES: frozenset[str] = frozenset({
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".cs", ".kt", ".kts",
    ".sh", ".bash", ".yaml", ".yml", ".json", ".toml", ".tf", ".hcl",
})


_SEMGREP_SUPPORTED_NAMES: frozenset[str] = frozenset({"Dockerfile", "Containerfile"})


_SEMGREP_SKIP_SEGMENTS: frozenset[str] = frozenset({
    ".git", "__pycache__", ".venv", "venv", "env", "node_modules", "dist", ".tox",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "aci.egg-info",
    ".claude", "archive", "common", "workspace",
})


def _eslint_command(target_root: Path) -> list[str]:
    return ["eslint", "--format", "json", str(target_root)]


def _semgrep_rule_path() -> Path:
    return Path(__file__).resolve().parent / "package_assets" / "analyzers" / "aci-semgrep-rules.yml"


def _has_semgrep_source(target_root: Path, ignored_paths: tuple[Path, ...] = ()) -> bool:
    ignored = {path.resolve() for path in ignored_paths}
    return any(
        path.is_file()
        and path.resolve() not in ignored
        and path.name not in {".semgrepignore"}
        and not any(seg in _SEMGREP_SKIP_SEGMENTS for seg in _relative_parts(path, target_root))
        and (path.suffix.lower() in _SEMGREP_SUPPORTED_SUFFIXES or path.name in _SEMGREP_SUPPORTED_NAMES)
        for path in target_root.rglob("*")
    )


def _semgrep_command(target_root: Path) -> list[str] | None:
    rule_path = _semgrep_rule_path()
    if not rule_path.is_file() or not _has_semgrep_source(target_root, ignored_paths=(rule_path,)):
        return None
    return [
        "semgrep",
        "scan",
        "--config",
        str(rule_path),
        "--json",
        "--quiet",
        "--disable-version-check",
        str(target_root),
    ]


def _find_tsconfig(target_root: Path) -> Path | None:
    tsconfig = target_root / "tsconfig.json"
    return tsconfig if tsconfig.is_file() else None


def _tsc_command(tsconfig_path: Path) -> list[str]:
    return ["tsc", "--noEmit", "--pretty", "false", "-p", str(tsconfig_path)]


_SHELLCHECK_SKIP_SEGMENTS: frozenset[str] = frozenset({
    ".git", "__pycache__", ".venv", "venv", "env", "node_modules", "dist", ".tox",
})


def _find_shell_files(target_root: Path) -> list[str]:
    return sorted(
        str(p)
        for p in target_root.rglob("*")
        if p.suffix in (".sh", ".bash")
        and p.is_file()
        and not any(seg in _SHELLCHECK_SKIP_SEGMENTS for seg in _relative_parts(p, target_root))
    )


def _shellcheck_command(shell_files: list[str]) -> list[str]:
    return ["shellcheck", "--format", "json"] + shell_files[:200]


def _sqlfluff_command(target_root: Path) -> list[str]:
    return ["sqlfluff", "lint", "--format", "json", str(target_root)]


def _osv_scanner_command(target_root: Path) -> list[str]:
    # osv-scanner writes its JSON report to stdout with --format json.
    return ["osv-scanner", "--format", "json", "-r", str(target_root)]


def _trivy_command(target_root: Path) -> list[str]:
    # trivy fs scans a directory tree for vulnerable dependencies; --quiet keeps
    # the progress UI off stdout so only the JSON report remains.
    return ["trivy", "fs", "--quiet", "--format", "json", str(target_root)]


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
    if analyzer_id == "semgrep":
        return _semgrep_command(target_root)
    if analyzer_id == "eslint":
        return _eslint_command(target_root)
    if analyzer_id == "sqlfluff":
        return _sqlfluff_command(target_root)
    if analyzer_id == "osv-scanner":
        return _osv_scanner_command(target_root)
    if analyzer_id == "trivy":
        return _trivy_command(target_root)
    return None


def _gitleaks_command(target_root: Path, report_path: Path) -> list[str]:
    # gitleaks writes its JSON report to a file (not stdout), so the runner gives
    # it an explicit report path and reads it back. --exit-code 0 keeps a leak
    # finding from being reported as a process failure.
    return [
        "gitleaks", "detect",
        "--source", str(target_root),
        "--no-banner",
        "--report-format", "json",
        "--report-path", str(report_path),
        "--exit-code", "0",
    ]
