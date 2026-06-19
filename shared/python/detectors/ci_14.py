"""CI-14 Security Neglect detectors (eval/exec, subprocess shell=True, plaintext secrets, insecure HTTP)."""
from __future__ import annotations

import ast
import re
from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.11+ in supported runtime
    tomllib = None  # type: ignore[assignment]

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        SEVERITY_CRITICAL, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
    )
    from ._helpers import _relative_path, _line_excerpt, _line_number_from_index, _cached_parse
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        SEVERITY_CRITICAL, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
    )
    from detectors._helpers import _relative_path, _line_excerpt, _line_number_from_index, _cached_parse  # type: ignore[no-redef]

SIGNALS_EVAL_EXEC: frozenset[str] = frozenset({"CI14_DYNAMIC_CODE_EXECUTION"})
SIGNALS_SUBPROCESS: frozenset[str] = frozenset({"CI14_SUBPROCESS_SHELL_TRUE"})
SIGNALS_SECRET: frozenset[str] = frozenset({"CI14_PLAINTEXT_SECRET"})
SIGNALS_HTTP: frozenset[str] = frozenset({"CI14_INSECURE_HTTP"})
SIGNALS_DESERIALIZATION: frozenset[str] = frozenset({"CI14_UNSAFE_DESERIALIZATION"})
SIGNALS_UNSAFE_YAML: frozenset[str] = frozenset({"CI14_UNSAFE_YAML_LOAD"})
SIGNALS_SUPPLY_CHAIN: frozenset[str] = frozenset({"CI14_SUPPLY_CHAIN_DRIFT"})

_SUBPROCESS_SHELL_TRUE_PATTERN = re.compile(
    r"\bsubprocess\.(run|Popen|call|check_call|check_output)\s*\([^)]*shell\s*=\s*True",
    re.DOTALL,
)
_SECRET_NAME_PATTERN = re.compile(r"(?i)(api[_-]?key|secret|token|password)")
_SECRET_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9_\-]{8,}$")
# Regex fallback for non-Python text/config files (.json/.yaml/.toml/...), which
# have no AST. Python files use the AST path below to avoid docstring/comment FPs.
_PLAINTEXT_SECRET_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][A-Za-z0-9_\-]{8,}['\"]"
)
_INSECURE_HTTP_PATTERN = re.compile(r"(?i)http://[A-Za-z0-9._:/\-]+")
_DOCKER_LATEST_PATTERN = re.compile(r"^\s*FROM\s+\S+:latest(?:\s|$)", re.IGNORECASE)
_GITHUB_ACTION_USES_PATTERN = re.compile(r"^\s*uses:\s*([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)@([^\s#]+)", re.IGNORECASE)
_EXACT_REQUIREMENT_PIN_PATTERN = re.compile(r"===?\s*[^=]")
_POETRY_FLOATING_SPEC_PATTERN = re.compile(r"^(?:\^|~|>=|<=|>|<|!=|\*)")

# Env-var / constant NAMES (UPPER_SNAKE with an underscore) assigned to a
# secret-named target are labels, not secret material: `SECRET_KEY =
# 'AWS_SECRET_ACCESS_KEY'`. A real credential is not shaped like a screaming-
# snake identifier, so excluding this shape kills the dominant secret FP
# without dropping mixed-case/opaque keys.
_ENV_VAR_NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$")

# http:// hosts that are identifiers, not live transport: XML/schema namespace
# URIs (xmlns=...) and reserved documentation/example domains. These are never
# fetched, so flagging them as insecure transport is noise.
_NON_ENDPOINT_HTTP_HOSTS: frozenset[str] = frozenset({
    "example.com", "example.org", "example.net", "example.edu",
    "localhost", "127.0.0.1", "0.0.0.0",
    "www.w3.org", "w3.org", "schemas.xmlsoap.org", "purl.org",
    "www.iana.org", "ns.adobe.com", "tempuri.org", "dublincore.org",
    "schemas.openxmlformats.org", "schemas.microsoft.com", "docbook.org",
})
_NON_ENDPOINT_HTTP_SUFFIXES: tuple[str, ...] = (
    ".w3.org", ".xmlsoap.org", ".local", ".test", ".invalid", ".example", ".localhost",
)


def _http_host_is_non_endpoint(url: str) -> bool:
    rest = url[len("http://"):]
    host = re.split(r"[/:?#]", rest, maxsplit=1)[0].lower()
    return host in _NON_ENDPOINT_HTTP_HOSTS or host.endswith(_NON_ENDPOINT_HTTP_SUFFIXES)


def _is_secret_string_value(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(_SECRET_VALUE_PATTERN.match(value))
        and not _ENV_VAR_NAME_PATTERN.match(value)
    )


def _ast_secret_lines(tree: ast.AST) -> list[int]:
    """Lines where a secret-named target/keyword is assigned a token-like string
    literal in real code (assignments and call keywords). Docstrings and comments
    are not assignments, so they never match."""
    lines: list[int] = []

    def _name_is_secret(name: str) -> bool:
        return bool(_SECRET_NAME_PATTERN.search(name))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and _is_secret_string_value(node.value.value):
            for target in node.targets:
                name = target.id if isinstance(target, ast.Name) else target.attr if isinstance(target, ast.Attribute) else ""
                if name and _name_is_secret(name):
                    lines.append(node.lineno)
                    break
        elif isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Constant) and _is_secret_string_value(node.value.value):
            target = node.target
            name = target.id if isinstance(target, ast.Name) else target.attr if isinstance(target, ast.Attribute) else ""
            if name and _name_is_secret(name):
                lines.append(node.lineno)
        elif isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg and _name_is_secret(kw.arg) and isinstance(kw.value, ast.Constant) and _is_secret_string_value(kw.value.value):
                    lines.append(kw.value.lineno)
    return lines


def scan_eval_exec(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() != ".py":
        return findings
    try:
        tree = _cached_parse(text)
    except SyntaxError:
        return findings
    # AST-based: only a real call to bare `eval(...)` / `exec(...)` counts.
    # This excludes the regex false positives — the words in comments and
    # docstrings, and attribute calls like `node.eval(...)`.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id not in ("eval", "exec"):
            continue
        line = node.lineno
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
    if path.suffix.lower() == ".py":
        # AST path: only real assignments/keywords with a secret-named target and
        # a token-like string value. Skips docstring examples and comments.
        try:
            tree = _cached_parse(text)
        except SyntaxError:
            return findings
        secret_lines = _ast_secret_lines(tree)
    else:
        # Non-Python config/text files: regex fallback (no AST available).
        secret_lines = [_line_number_from_index(text, m.start()) for m in _PLAINTEXT_SECRET_PATTERN.finditer(text)]

    for line in secret_lines:
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


def _attribute_call_name(node: ast.Call) -> tuple[str | None, str | None]:
    if not isinstance(node.func, ast.Attribute):
        return None, None
    owner = node.func.value.id if isinstance(node.func.value, ast.Name) else None
    return owner, node.func.attr


def scan_unsafe_deserialization(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() != ".py":
        return findings
    try:
        tree = _cached_parse(text)
    except SyntaxError:
        return findings
    dangerous_owners = {"pickle", "dill", "marshal", "shelve"}
    dangerous_methods = {"load", "loads", "open"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        owner, attr = _attribute_call_name(node)
        if owner not in dangerous_owners or attr not in dangerous_methods:
            continue
        line = node.lineno
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-14",
                signal="CI14_UNSAFE_DESERIALIZATION",
                severity="high",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason=(
                    f"{owner}.{attr} can deserialize attacker-controlled data and trigger unsafe code paths."
                ),
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Prefer schema-checked formats such as JSON, or strictly bound trusted deserialization inputs.",
                confidence=CONFIDENCE_HIGH,
                priority="P1",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _is_safe_yaml_loader(node: ast.AST) -> bool:
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "yaml":
        return node.attr in {"SafeLoader", "CSafeLoader"}
    return False


def scan_unsafe_yaml_load(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() != ".py":
        return findings
    try:
        tree = _cached_parse(text)
    except SyntaxError:
        return findings
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        owner, attr = _attribute_call_name(node)
        if owner != "yaml" or attr != "load":
            continue
        loader_kw = next((kw.value for kw in node.keywords if kw.arg == "Loader"), None)
        if loader_kw is not None and _is_safe_yaml_loader(loader_kw):
            continue
        line = node.lineno
        findings.append(
            build_finding(
                finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                ci_id="CI-14",
                signal="CI14_UNSAFE_YAML_LOAD",
                severity="high",
                target_file=_relative_path(path, target_root),
                line=line,
                excerpt=_line_excerpt(text, line),
                reason="yaml.load without SafeLoader can construct unsafe objects from untrusted input.",
                evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                recommended_action="Use yaml.safe_load or pass yaml.SafeLoader explicitly for untrusted YAML.",
                confidence=CONFIDENCE_HIGH,
                priority="P1",
                owner_lane=LANE_NATIVE_STATIC,
                verification_status=VERIFICATION_EXECUTED,
            )
        )
    return findings


def _http_match_is_noise(line_text: str, col: int) -> bool:
    """Skip http:// occurrences that are not live transport: in a comment, or
    in a doctest example line (>>> / ...)."""
    before = line_text[:col]
    if "#" in before:
        return True
    stripped = line_text.lstrip()
    return stripped.startswith(">>>") or stripped.startswith("...")


def _docstring_line_set(tree: ast.AST) -> set[int]:
    """Line numbers covered by module/class/function docstrings. URLs in
    docstrings (markdown links, usage examples) are documentation, not live
    plaintext transport — the dominant insecure-HTTP false positive."""
    covered: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            start = first.value.lineno
            end = getattr(first.value, "end_lineno", start) or start
            covered.update(range(start, end + 1))
    return covered


def _build_security_finding(
    *,
    finding_id: str,
    signal: str,
    severity: str,
    path: Path,
    target_root: Path,
    line: int,
    excerpt_text: str,
    reason: str,
    recommended_action: str,
) -> AciFinding:
    return build_finding(
        finding_id=finding_id,
        ci_id="CI-14",
        signal=signal,
        severity=severity,
        target_file=_relative_path(path, target_root),
        line=line,
        excerpt=excerpt_text,
        reason=reason,
        evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
        recommended_action=recommended_action,
        confidence=CONFIDENCE_MEDIUM if severity == "medium" else CONFIDENCE_HIGH,
        priority="P2" if severity == "medium" else "P1",
        owner_lane=LANE_NATIVE_STATIC,
        verification_status=VERIFICATION_EXECUTED,
    )


def _package_json_supply_chain_findings(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    try:
        import json as _json
        payload = _json.loads(text)
    except _json.JSONDecodeError:
        return findings
    if not isinstance(payload, dict):
        return findings
    lines = text.splitlines()
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        deps = payload.get(section)
        if not isinstance(deps, dict):
            continue
        for name, spec in deps.items():
            if not isinstance(name, str) or not isinstance(spec, str):
                continue
            if not spec.startswith(("^", "~", "*", ">", "<")):
                continue
            line = next((i for i, raw in enumerate(lines, start=1) if f'"{name}"' in raw), 1)
            findings.append(
                _build_security_finding(
                    finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                    signal="CI14_SUPPLY_CHAIN_DRIFT",
                    severity="medium",
                    path=path,
                    target_root=target_root,
                    line=line,
                    excerpt_text=_line_excerpt(text, line),
                    reason=f"Dependency '{name}' is not pinned to an exact version, which widens supply-chain drift.",
                    recommended_action="Pin dependencies to reviewed versions and update them through an explicit upgrade path.",
                )
            )
    return findings


def _requirement_spec_is_exact_pin(spec: str) -> bool:
    stripped = spec.strip()
    if not stripped:
        return False
    if stripped.startswith(("-e ", "--editable ")):
        return True
    if " @" in stripped or stripped.startswith(("git+", "http://", "https://")):
        return True
    return bool(_EXACT_REQUIREMENT_PIN_PATTERN.search(stripped))


def _find_dependency_line(lines: list[str], needle: str) -> int:
    for index, raw in enumerate(lines, start=1):
        if needle in raw:
            return index
    return 1


def _append_supply_chain_finding(
    findings: list[AciFinding],
    *,
    next_id: int,
    path: Path,
    target_root: Path,
    line: int,
    excerpt_text: str,
    reason: str,
    recommended_action: str,
) -> None:
    findings.append(
        _build_security_finding(
            finding_id=f"F-SCAN-{next_id + len(findings):04d}",
            signal="CI14_SUPPLY_CHAIN_DRIFT",
            severity="medium",
            path=path,
            target_root=target_root,
            line=line,
            excerpt_text=excerpt_text,
            reason=reason,
            recommended_action=recommended_action,
        )
    )


def _iter_pep621_dependency_specs(payload: dict[str, object]) -> list[tuple[str, str]]:
    specs: list[tuple[str, str]] = []
    project = payload.get("project")
    if isinstance(project, dict):
        dependencies = project.get("dependencies")
        if isinstance(dependencies, list):
            for item in dependencies:
                if isinstance(item, str):
                    specs.append(("project.dependencies", item))
        optional = project.get("optional-dependencies")
        if isinstance(optional, dict):
            for group_name, group_items in optional.items():
                if not isinstance(group_name, str) or not isinstance(group_items, list):
                    continue
                for item in group_items:
                    if isinstance(item, str):
                        specs.append((f"project.optional-dependencies.{group_name}", item))
    dependency_groups = payload.get("dependency-groups")
    if isinstance(dependency_groups, dict):
        for group_name, group_items in dependency_groups.items():
            if not isinstance(group_name, str) or not isinstance(group_items, list):
                continue
            for item in group_items:
                if isinstance(item, str):
                    specs.append((f"dependency-groups.{group_name}", item))
    return specs


def _is_poetry_exact_pin(spec: str) -> bool:
    stripped = spec.strip()
    if not stripped:
        return False
    if stripped in {"*", "latest"}:
        return False
    if stripped.startswith(("path = ", "file = ", "git = ", "url = ")):
        return True
    return not _POETRY_FLOATING_SPEC_PATTERN.match(stripped)


def _iter_poetry_dependency_specs(payload: dict[str, object]) -> list[tuple[str, str, str]]:
    specs: list[tuple[str, str, str]] = []
    tool = payload.get("tool")
    if not isinstance(tool, dict):
        return specs
    poetry = tool.get("poetry")
    if not isinstance(poetry, dict):
        return specs

    def _consume_table(section_name: str, table: object) -> None:
        if not isinstance(table, dict):
            return
        for dep_name, dep_spec in table.items():
            if not isinstance(dep_name, str) or dep_name == "python":
                continue
            if isinstance(dep_spec, str):
                specs.append((section_name, dep_name, dep_spec))
                continue
            if isinstance(dep_spec, dict):
                version = dep_spec.get("version")
                if isinstance(version, str):
                    specs.append((section_name, dep_name, version))

    _consume_table("tool.poetry.dependencies", poetry.get("dependencies"))
    _consume_table("tool.poetry.dev-dependencies", poetry.get("dev-dependencies"))
    groups = poetry.get("group")
    if isinstance(groups, dict):
        for group_name, group_table in groups.items():
            if not isinstance(group_name, str) or not isinstance(group_table, dict):
                continue
            _consume_table(
                f"tool.poetry.group.{group_name}.dependencies",
                group_table.get("dependencies"),
            )
    return specs


def _pyproject_supply_chain_findings(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if tomllib is None:
        return findings
    try:
        payload = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return findings
    if not isinstance(payload, dict):
        return findings
    lines = text.splitlines()

    for section_name, raw_spec in _iter_pep621_dependency_specs(payload):
        if _requirement_spec_is_exact_pin(raw_spec):
            continue
        line = _find_dependency_line(lines, raw_spec)
        _append_supply_chain_finding(
            findings,
            next_id=next_id,
            path=path,
            target_root=target_root,
            line=line,
            excerpt_text=_line_excerpt(text, line),
            reason=(
                f"Dependency spec '{raw_spec}' in {section_name} is not pinned to an exact version, "
                "which widens supply-chain drift."
            ),
            recommended_action="Pin pyproject dependencies to reviewed exact versions or isolate floating ranges behind an explicitly reviewed policy.",
        )

    for section_name, dep_name, raw_spec in _iter_poetry_dependency_specs(payload):
        if _is_poetry_exact_pin(raw_spec):
            continue
        line = _find_dependency_line(lines, f"{dep_name} =")
        _append_supply_chain_finding(
            findings,
            next_id=next_id,
            path=path,
            target_root=target_root,
            line=line,
            excerpt_text=_line_excerpt(text, line),
            reason=(
                f"Dependency '{dep_name}' in {section_name} uses a floating version spec, "
                "which widens supply-chain drift."
            ),
            recommended_action="Pin Poetry-managed dependencies to reviewed exact versions or document the floating range as an intentional exception.",
        )
    return findings


def scan_supply_chain_drift(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    suffix = path.suffix.lower()
    name = path.name
    lines = text.splitlines()
    if name == "package.json":
        return _package_json_supply_chain_findings(path, text, target_root, next_id)
    if name == "pyproject.toml":
        return _pyproject_supply_chain_findings(path, text, target_root, next_id)
    if name.startswith("requirements") and suffix == ".txt":
        for lineno, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if not stripped or stripped.startswith(("#", "-r", "--", "-e", "git+", "http://", "https://")):
                continue
            if not _requirement_spec_is_exact_pin(stripped):
                _append_supply_chain_finding(
                    findings,
                    next_id=next_id,
                    path=path,
                    target_root=target_root,
                    line=lineno,
                    excerpt_text=raw.strip(),
                    reason="A Python requirement is not pinned to an exact version, which weakens reproducibility and review boundaries.",
                    recommended_action="Pin third-party requirements with exact versions or route intentionally floating dependencies through a reviewed exceptions file.",
                )
        return findings
    if name in {"Dockerfile", "Containerfile"}:
        for lineno, raw in enumerate(lines, start=1):
            if _DOCKER_LATEST_PATTERN.match(raw):
                findings.append(
                    _build_security_finding(
                        finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                        signal="CI14_SUPPLY_CHAIN_DRIFT",
                        severity="medium",
                        path=path,
                        target_root=target_root,
                        line=lineno,
                        excerpt_text=raw.strip(),
                        reason="Container base image uses the floating ':latest' tag, which makes rebuilds drift silently.",
                        recommended_action="Pin the base image to a reviewed immutable tag or digest.",
                    )
                )
        return findings
    normalized = path.as_posix().replace("\\", "/")
    if normalized.endswith(".github/workflows/ci.yml") or "/.github/workflows/" in normalized:
        for lineno, raw in enumerate(lines, start=1):
            match = _GITHUB_ACTION_USES_PATTERN.match(raw)
            if not match:
                continue
            ref = match.group(2)
            if re.fullmatch(r"[0-9a-fA-F]{40}", ref):
                continue
            findings.append(
                _build_security_finding(
                    finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                    signal="CI14_SUPPLY_CHAIN_DRIFT",
                    severity="medium",
                    path=path,
                    target_root=target_root,
                    line=lineno,
                    excerpt_text=raw.strip(),
                    reason="GitHub Action is referenced by a mutable tag instead of a commit SHA, which widens supply-chain drift.",
                    recommended_action="Pin GitHub Actions to immutable commit SHAs and rotate them through reviewed updates.",
                )
            )
    return findings


def scan_insecure_http(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() not in {".py", ".json", ".yml", ".yaml", ".toml", ".txt", ".md"}:
        return findings
    docstring_lines: set[int] = set()
    if path.suffix.lower() == ".py":
        try:
            docstring_lines = _docstring_line_set(_cached_parse(text))
        except SyntaxError:
            docstring_lines = set()
    lines = text.splitlines()
    for match in _INSECURE_HTTP_PATTERN.finditer(text):
        line = _line_number_from_index(text, match.start())
        if line in docstring_lines:
            continue
        line_text = lines[line - 1] if 0 <= line - 1 < len(lines) else ""
        col = match.start() - (text.rfind("\n", 0, match.start()) + 1)
        if _http_match_is_noise(line_text, col):
            continue
        if _http_host_is_non_endpoint(match.group(0)):
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
