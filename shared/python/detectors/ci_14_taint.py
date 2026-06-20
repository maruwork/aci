"""CI-14 tainted-flow detector (bounded intra-procedural source->sink taint).

This is ACI's first real dataflow check: it reports when clearly-untrusted input
reaches a clearly-dangerous sink within the same function. It is intentionally
conservative on both ends so it does not become a false-positive generator (the
failure mode this project's own audit calls out):

- Sources (untrusted): input(), os.environ / os.getenv, sys.argv, and web
  request objects (request.args/form/json/... including flask.request).
- Sinks (dangerous): eval / exec, os.system / os.popen, subprocess.* with
  shell=True, and cursor.execute(...) (SQL).
- Propagation: intra-procedural only, through assignments, f-strings, +/%
  concatenation, str()/.format()/.join() and taint-preserving string methods.
  No inter-procedural reasoning, no aliasing through containers.

A finding means a tainted value flows into a sink; the surrounding native CI-14
checks still fire independently (e.g. "eval is used at all").
"""
from __future__ import annotations

import ast
from pathlib import Path

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED, CONFIDENCE_HIGH,
    )
    from ._helpers import _relative_path, _line_excerpt, _cached_parse, ImportResolver
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED, CONFIDENCE_HIGH,
    )
    from detectors._helpers import _relative_path, _line_excerpt, _cached_parse, ImportResolver  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI14_TAINTED_FLOW"})

# Web request attribute roots that carry untrusted data (flask/django/FastAPI).
_REQUEST_TAINT_ATTRS: frozenset[str] = frozenset({
    "args", "form", "values", "json", "data", "files", "cookies", "headers",
    "get", "GET", "POST", "query_params", "path_params", "body",
})
# String methods that preserve taint (return a string derived from the receiver).
_STR_TAINT_METHODS: frozenset[str] = frozenset({
    "strip", "lstrip", "rstrip", "lower", "upper", "title", "capitalize",
    "replace", "format", "join", "encode", "decode", "format_map", "removeprefix",
    "removesuffix", "expandtabs", "swapcase", "casefold", "zfill",
})
# Subprocess methods whose command is injectable when shell=True.
_SUBPROCESS_METHODS: frozenset[str] = frozenset({
    "run", "Popen", "call", "check_call", "check_output",
})


def _attr_root_chain(node: ast.AST) -> str | None:
    """Dotted name for a plain Name/Attribute chain (no calls/subscripts)."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _attr_root_chain(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


def _is_source_expr(node: ast.AST) -> bool:
    """True if the expression is a direct untrusted-input source."""
    # input(...)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input":
        return True
    if isinstance(node, ast.Call):
        chain = _attr_root_chain(node.func)
        if chain in ("os.getenv", "os.environ.get"):
            return True
        # request.args.get(...) / request.headers.get(...) etc.
        if chain and (chain.startswith("request.") or chain.startswith("flask.request.")):
            return True
    # Attribute/subscript chains: os.environ, sys.argv, request.args, request.form[...]
    chain = _attr_root_chain(node.value if isinstance(node, ast.Subscript) else node)
    if chain in ("os.environ", "sys.argv"):
        return True
    if chain and (chain.startswith("request.") or chain.startswith("flask.request.")):
        parts = chain.split(".")
        # request.<attr> where <attr> is an untrusted member
        if "request" in parts:
            idx = parts.index("request")
            if idx + 1 < len(parts) and parts[idx + 1] in _REQUEST_TAINT_ATTRS:
                return True
    return False


def _expr_is_tainted(node: ast.AST | None, tainted: set[str]) -> bool:
    if node is None:
        return False
    if _is_source_expr(node):
        return True
    if isinstance(node, ast.Name):
        return node.id in tainted
    if isinstance(node, ast.Subscript):
        return _expr_is_tainted(node.value, tainted)
    if isinstance(node, ast.Attribute):
        return _expr_is_tainted(node.value, tainted)
    if isinstance(node, ast.JoinedStr):  # f-string
        return any(
            isinstance(v, ast.FormattedValue) and _expr_is_tainted(v.value, tainted)
            for v in node.values
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        return _expr_is_tainted(node.left, tainted) or _expr_is_tainted(node.right, tainted)
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "str":
            return any(_expr_is_tainted(a, tainted) for a in node.args)
        if isinstance(node.func, ast.Attribute) and node.func.attr in _STR_TAINT_METHODS:
            if _expr_is_tainted(node.func.value, tainted):
                return True
            return any(_expr_is_tainted(a, tainted) for a in node.args)
    return False


def _assignment_targets(target: ast.AST) -> list[str]:
    names: list[str] = []
    if isinstance(target, ast.Name):
        names.append(target.id)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for element in target.elts:
            names.extend(_assignment_targets(element))
    return names


def _collect_tainted_names(func: ast.AST) -> set[str]:
    """Forward fixpoint over assignments: taint only grows, so iterate to closure."""
    tainted: set[str] = set()
    changed = True
    while changed:
        changed = False
        for node in ast.walk(func):
            value: ast.AST | None = None
            targets: list[str] = []
            if isinstance(node, ast.Assign):
                value = node.value
                for tgt in node.targets:
                    targets.extend(_assignment_targets(tgt))
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                value = node.value
                targets = _assignment_targets(node.target)
            elif isinstance(node, (ast.AugAssign,)):
                value = node.value
                targets = _assignment_targets(node.target)
            else:
                continue
            if value is not None and _expr_is_tainted(value, tainted):
                for name in targets:
                    if name not in tainted:
                        tainted.add(name)
                        changed = True
    return tainted


def _sink_command_args(node: ast.Call, resolver: ImportResolver) -> list[ast.AST] | None:
    """Return the sink's command/query argument nodes to taint-check, or None."""
    qn = resolver.call_qualname(node)
    if qn in ("eval", "exec"):
        return list(node.args)
    if qn in ("os.system", "os.popen"):
        return list(node.args[:1])
    if qn:
        parts = qn.split(".")
        if parts[0] == "subprocess" and parts[-1] in _SUBPROCESS_METHODS:
            shell_true = any(
                kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
                for kw in node.keywords
            )
            return list(node.args[:1]) if shell_true else None
    # cursor.execute(<query>, params?) — SQL injection sink (query is arg 0)
    if isinstance(node.func, ast.Attribute) and node.func.attr in ("execute", "executescript"):
        return list(node.args[:1])
    return None


def _sink_label(node: ast.Call, resolver: ImportResolver) -> str:
    qn = resolver.call_qualname(node)
    if qn in ("eval", "exec", "os.system", "os.popen"):
        return qn
    if qn and qn.split(".")[0] == "subprocess":
        return f"{qn}(shell=True)"
    if isinstance(node.func, ast.Attribute):
        return f"{node.func.attr}()"
    return qn or "sink"


def scan(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    findings: list[AciFinding] = []
    if path.suffix.lower() != ".py":
        return findings
    try:
        tree = _cached_parse(text)
    except SyntaxError:
        return findings
    resolver = ImportResolver(tree)
    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        tainted = _collect_tainted_names(func)
        if not tainted and not any(_is_source_expr(n) for n in ast.walk(func)):
            continue
        for node in ast.walk(func):
            if not isinstance(node, ast.Call):
                continue
            command_args = _sink_command_args(node, resolver)
            if not command_args:
                continue
            if not any(_expr_is_tainted(arg, tainted) for arg in command_args):
                continue
            line = node.lineno
            sink = _sink_label(node, resolver)
            findings.append(
                build_finding(
                    finding_id=f"F-SCAN-{next_id + len(findings):04d}",
                    ci_id="CI-14",
                    signal="CI14_TAINTED_FLOW",
                    severity="high",
                    target_file=_relative_path(path, target_root),
                    line=line,
                    excerpt=_line_excerpt(text, line),
                    reason=(
                        f"Untrusted input flows into {sink}; an attacker-controlled value "
                        "reaching this sink enables injection or code execution."
                    ),
                    evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
                    recommended_action=(
                        "Validate or parameterize the input before the sink: use parameterized "
                        "queries, argument arrays without shell=True, or a strict allowlist."
                    ),
                    confidence=CONFIDENCE_HIGH,
                    priority="P1",
                    owner_lane=LANE_NATIVE_STATIC,
                    verification_status=VERIFICATION_EXECUTED,
                )
            )
    return findings
