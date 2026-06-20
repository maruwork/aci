"""CI-22 Resource Lifecycle Leak detector.

A handle (open/Popen/TemporaryFile/...) is "managed" when its lifecycle is
guaranteed. Instead of enumerating every cleanup spelling, one predicate is
resolved recursively — *does calling this expression close the handle?* —
through assignments, functools.partial, lambdas, local defs, and registrar
aliases. Every ExitStack callback / partial / lambda / helper form is an instance
of that predicate, so the matrix collapses into a few structural rules (with /
return / attribute-store / stack registration / linear close / exception-safe
close). Non-local helper ownership stays conservative (KL-ACI-CI22-NONLOCAL-LIFECYCLE).
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED, CONFIDENCE_MEDIUM, CONFIDENCE_LOW,
    )
    from ._helpers import _relative_path, _line_excerpt, _build_parent_map, _cached_parse
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED, CONFIDENCE_MEDIUM, CONFIDENCE_LOW,
    )
    from detectors._helpers import _relative_path, _line_excerpt, _build_parent_map, _cached_parse  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI22_RESOURCE_CLEANUP_GAP"})

_RESOURCE_OPENER_NAMES: frozenset[str] = frozenset({
    "open", "io.open", "codecs.open", "os.open",
    "Popen", "subprocess.Popen",
    "NamedTemporaryFile", "tempfile.NamedTemporaryFile",
    "TemporaryFile", "tempfile.TemporaryFile",
    "SpooledTemporaryFile", "tempfile.SpooledTemporaryFile",
})
_PATHLIKE_NAME_PATTERN = re.compile(r"(?:^|_)(?:path|paths|file|files|filename|filepath|dir|directory)(?:$|_)")
_PATHLIKE_CONSTRUCTORS: frozenset[str] = frozenset({
    "Path", "PurePath", "PurePosixPath", "PureWindowsPath",
    "pathlib.Path", "pathlib.PurePath", "pathlib.PurePosixPath", "pathlib.PureWindowsPath",
})
_EXIT_STACK_NAMES: frozenset[str] = frozenset({
    "ExitStack", "AsyncExitStack", "contextlib.ExitStack", "contextlib.AsyncExitStack",
})
_EXIT_STACK_ENTER_METHODS: frozenset[str] = frozenset({"enter_context", "enter_async_context"})
_EXIT_STACK_CALLBACK_METHODS: frozenset[str] = frozenset({"callback", "push_async_callback"})
_EXIT_STACK_PUSH_METHODS: frozenset[str] = frozenset({"push"})
_RESOURCE_WRAPPER_CONTEXT_NAMES: frozenset[str] = frozenset({"closing", "contextlib.closing"})
_PARTIAL_CALL_NAMES: frozenset[str] = frozenset({"partial", "functools.partial"})
_CLOSE_METHODS: frozenset[str] = frozenset({"close", "__exit__"})


@dataclass(frozen=True)
class _ResourceFindingContext:
    path: Path
    text: str
    target_root: Path
    next_id: int


def _enclosing_function(node: ast.AST, parent_map: dict[ast.AST, ast.AST]) -> ast.AST | None:
    cur = parent_map.get(node)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur
        cur = parent_map.get(cur)
    return None


def _attr_chain(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _attr_chain(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


def _expr_looks_pathlike(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return bool(_PATHLIKE_NAME_PATTERN.search(node.id.lower()))
    if isinstance(node, ast.Attribute):
        return bool(_PATHLIKE_NAME_PATTERN.search(node.attr.lower())) or _expr_looks_pathlike(node.value)
    if isinstance(node, ast.Call):
        return _attr_chain(node.func) in _PATHLIKE_CONSTRUCTORS
    if isinstance(node, ast.Subscript):
        return _expr_looks_pathlike(node.value)
    return False


# ── Generic "does this close the handle?" resolver ───────────────────────────

def _func_bindings(func: ast.AST) -> tuple[dict[str, list[ast.AST]], dict[str, ast.AST]]:
    assigns: dict[str, list[ast.AST]] = {}
    defs: dict[str, ast.AST] = {}
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            assigns.setdefault(node.targets[0].id, []).append(node.value)
        elif isinstance(node, ast.AnnAssign) and node.value is not None and isinstance(node.target, ast.Name):
            assigns.setdefault(node.target.id, []).append(node.value)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defs[node.name] = node
    return assigns, defs


def _params_aliased(arguments: ast.arguments, supplied: list[ast.AST], aliases: set[str]) -> set[str]:
    params = [*arguments.posonlyargs, *arguments.args]
    bound: set[str] = set()
    if arguments.defaults:
        for arg, default in zip(params[-len(arguments.defaults):], arguments.defaults):
            if isinstance(default, ast.Name) and default.id in aliases:
                bound.add(arg.arg)
    for arg, value in zip(params, supplied):
        if isinstance(value, ast.Name) and value.id in aliases:
            bound.add(arg.arg)
    return bound


def _callable_closes(
    callee: ast.AST, aliases: set[str], supplied: list[ast.AST],
    assigns: dict[str, list[ast.AST]], defs: dict[str, ast.AST], depth: int = 0,
) -> bool:
    """True if calling `callee` with `supplied` positional args closes an alias."""
    if depth > 8:
        return False
    # bound method: <alias>.close / <alias>.__exit__
    if (isinstance(callee, ast.Attribute) and isinstance(callee.value, ast.Name)
            and callee.value.id in aliases and callee.attr in _CLOSE_METHODS):
        return True
    chain = _attr_chain(callee)
    # os.close(<alias>) / close(<alias>) — alias supplied as first positional arg
    if (chain == "os.close" or (isinstance(callee, ast.Name) and callee.id == "close")):
        if supplied and isinstance(supplied[0], ast.Name) and supplied[0].id in aliases:
            return True
    # functools.partial(fn, *pre) — pre-bound args prepend to supplied
    if (isinstance(callee, ast.Call) and _attr_chain(callee.func) in _PARTIAL_CALL_NAMES and callee.args):
        return _callable_closes(callee.args[0], aliases, list(callee.args[1:]) + supplied, assigns, defs, depth + 1)
    # lambda: bind params to aliases via defaults/supplied, then inspect its body
    if isinstance(callee, ast.Lambda):
        inner = aliases | _params_aliased(callee.args, supplied, aliases)
        return isinstance(callee.body, ast.Call) and _call_closes(callee.body, inner, assigns, defs, depth + 1)
    if isinstance(callee, ast.Name):
        # local def whose body closes an (aliased) param/handle
        target = defs.get(callee.id)
        if isinstance(target, (ast.FunctionDef, ast.AsyncFunctionDef)):
            inner = aliases | _params_aliased(target.args, supplied, aliases)
            return any(
                isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)
                and _call_closes(s.value, inner, assigns, defs, depth + 1)
                for s in target.body
            )
        # variable alias: resolve through its assigned values
        for value in assigns.get(callee.id, []):
            if _callable_closes(value, aliases, supplied, assigns, defs, depth + 1):
                return True
    return False


def _call_closes(call: ast.Call, aliases: set[str], assigns: dict[str, list[ast.AST]],
                 defs: dict[str, ast.AST], depth: int = 0) -> bool:
    return _callable_closes(call.func, aliases, list(call.args), assigns, defs, depth)


# ── Structural managed-lifecycle rules ───────────────────────────────────────

def _block_has_close(statements: list[ast.stmt], var: str, assigns: dict[str, list[ast.AST]],
                     defs: dict[str, ast.AST]) -> bool:
    for stmt in statements:
        for child in ast.walk(stmt):
            if isinstance(child, ast.Call) and _call_closes(child, {var}, assigns, defs):
                return True
    return False


def _has_exception_safe_close(func: ast.AST, var: str, assigns: dict[str, list[ast.AST]],
                              defs: dict[str, ast.AST]) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.Try):
            continue
        if node.finalbody and _block_has_close(node.finalbody, var, assigns, defs):
            return True
        if (node.handlers and node.orelse
                and all(_block_has_close(h.body, var, assigns, defs) for h in node.handlers)
                and _block_has_close(node.orelse, var, assigns, defs)):
            return True
    return False


def _managed_exit_stack_names(func: ast.AST) -> set[str]:
    assigned: set[str] = set()
    context_names: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(func):
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Call):
            if _attr_chain(node.value.func) in _EXIT_STACK_NAMES:
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                assigned.update(t.id for t in targets if isinstance(t, ast.Name))
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if isinstance(item.context_expr, ast.Name):
                    context_names.add(item.context_expr.id)
                elif (isinstance(item.context_expr, ast.Call)
                      and _attr_chain(item.context_expr.func) in _EXIT_STACK_NAMES
                      and isinstance(item.optional_vars, ast.Name)):
                    names.add(item.optional_vars.id)
    return names | (assigned & context_names)


def _registrar_aliases(func: ast.AST, stacks: set[str], methods: frozenset[str]) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target, value = node.target, node.value
        else:
            continue
        if (isinstance(target, ast.Name) and isinstance(value, ast.Attribute)
                and isinstance(value.value, ast.Name) and value.value.id in stacks
                and value.attr in methods):
            names.add(target.id)
    return names


def _wrapper_names(func: ast.AST, var: str) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.value, ast.Call):
            target, call = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Call):
            target, call = node.target, node.value
        else:
            continue
        if (isinstance(target, ast.Name) and _attr_chain(call.func) in _RESOURCE_WRAPPER_CONTEXT_NAMES
                and call.args and isinstance(call.args[0], ast.Name) and call.args[0].id == var):
            names.add(target.id)
    return names


def _handle_in_expr(node: ast.AST, var: str, wrappers: set[str]) -> bool:
    """Handle referenced directly (var), as a wrapper name, or inside closing(var)."""
    if isinstance(node, ast.Name):
        return node.id == var or node.id in wrappers
    if isinstance(node, ast.Call):
        return any(isinstance(child, ast.Name) and child.id == var for child in ast.walk(node))
    return False


@dataclass(frozen=True)
class _Scope:
    assigns: dict[str, list[ast.AST]]
    defs: dict[str, ast.AST]
    stacks: set[str]
    enter_regs: set[str]
    push_regs: set[str]
    cb_regs: set[str]
    wrappers: set[str]


def _scope_for(func: ast.AST, var: str) -> _Scope:
    assigns, defs = _func_bindings(func)
    stacks = _managed_exit_stack_names(func)
    return _Scope(
        assigns=assigns, defs=defs, stacks=stacks,
        enter_regs=_registrar_aliases(func, stacks, _EXIT_STACK_ENTER_METHODS),
        push_regs=_registrar_aliases(func, stacks, _EXIT_STACK_PUSH_METHODS),
        cb_regs=_registrar_aliases(func, stacks, _EXIT_STACK_CALLBACK_METHODS),
        wrappers=_wrapper_names(func, var),
    )


def _registration_manages(call: ast.Call, var: str, scope: _Scope) -> bool:
    method: str | None = None
    if (isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name)
            and call.func.value.id in scope.stacks):
        method = call.func.attr
    elif isinstance(call.func, ast.Name):
        rid = call.func.id
        method = ("enter_context" if rid in scope.enter_regs
                  else "push" if rid in scope.push_regs
                  else "callback" if rid in scope.cb_regs else None)
    if method is None or not call.args:
        return False
    if method in _EXIT_STACK_ENTER_METHODS or method in _EXIT_STACK_PUSH_METHODS:
        return _handle_in_expr(call.args[0], var, scope.wrappers)
    if method in _EXIT_STACK_CALLBACK_METHODS:
        return _callable_closes(call.args[0], {var}, list(call.args[1:]), scope.assigns, scope.defs)
    return False


def _name_is_managed(func: ast.AST, var: str, scope: _Scope) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Return):
            value = node.value
            if isinstance(value, ast.Name) and value.id == var:
                return True
            if isinstance(value, (ast.Tuple, ast.List)) and any(
                    isinstance(e, ast.Name) and e.id == var for e in value.elts):
                return True
        if isinstance(node, (ast.With, ast.AsyncWith)):
            if any(_handle_in_expr(item.context_expr, var, scope.wrappers) for item in node.items):
                return True
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Name) and node.value.id == var
                and any(isinstance(t, ast.Attribute) for t in node.targets)):
            return True
        if isinstance(node, ast.Call) and _registration_manages(node, var, scope):
            return True
    return _has_exception_safe_close(func, var, scope.assigns, scope.defs)


def _enclosing_statement(node: ast.AST, parent_map: dict[ast.AST, ast.AST]) -> ast.stmt | None:
    cur: ast.AST | None = node
    while cur is not None and not isinstance(cur, ast.stmt):
        cur = parent_map.get(cur)
    return cur if isinstance(cur, ast.stmt) else None


def _statement_siblings(stmt: ast.stmt, parent_map: dict[ast.AST, ast.AST]) -> tuple[list[ast.stmt], int] | None:
    parent = parent_map.get(stmt)
    if parent is None:
        return None
    for _, value in ast.iter_fields(parent):
        if isinstance(value, list) and value and all(isinstance(i, ast.stmt) for i in value) and stmt in value:
            return value, value.index(stmt)
    return None


def _linear_close_after(call_node: ast.Call, parent_map: dict[ast.AST, ast.AST], var: str, scope: _Scope) -> bool:
    """A close of `var` in the same suite after the opener, before any control flow."""
    stmt = _enclosing_statement(call_node, parent_map)
    siblings = _statement_siblings(stmt, parent_map) if stmt is not None else None
    if siblings is None:
        return False
    statements, index = siblings
    for sibling in statements[index + 1:]:
        if isinstance(sibling, (ast.Expr, ast.Assign, ast.AnnAssign)):
            # Do not descend into lambda bodies: an assigned-but-uncalled
            # `cleanup = lambda: handle.close()` does not close anything.
            stack: list[ast.AST] = [sibling]
            while stack:
                child = stack.pop()
                if child is not sibling and isinstance(child, ast.Lambda):
                    continue
                if isinstance(child, ast.Call) and _call_closes(child, {var}, scope.assigns, scope.defs):
                    return True
                stack.extend(ast.iter_child_nodes(child))
        if isinstance(sibling, (ast.Assign, ast.AnnAssign, ast.Expr, ast.Pass)):
            continue
        return False
    return False


def _is_managed_open(call_node: ast.Call, parent_map: dict[ast.AST, ast.AST]) -> bool:
    parent = parent_map.get(call_node)
    if isinstance(parent, (ast.Return, ast.withitem)):
        return True
    func = _enclosing_function(call_node, parent_map)
    if func is not None:
        scope = _scope_for(func, "")  # var-independent scope (stacks/regs/bindings)
        # opener call is itself the registration argument: stack.enter_context(open(...)) etc.
        registration = parent.value if isinstance(parent, ast.keyword) else parent
        if isinstance(registration, ast.Call) and _registration_arg_is_call(registration, call_node, scope):
            return True
        # opener wrapped in closing(open(...)) that is registered/with-managed
        if isinstance(parent, ast.Call) and _attr_chain(parent.func) in _RESOURCE_WRAPPER_CONTEXT_NAMES:
            grand = parent_map.get(parent)
            if isinstance(grand, ast.withitem):
                return True
            if isinstance(grand, ast.Call) and _registration_arg_is_call(grand, parent, scope):
                return True
            # managed = closing(open(...)) — treat `managed` as the handle name
            if isinstance(grand, (ast.Assign, ast.AnnAssign)):
                parent = grand
    targets: list[ast.AST]
    if isinstance(parent, ast.Assign):
        targets = list(parent.targets)
    elif isinstance(parent, ast.AnnAssign):
        targets = [parent.target]
    else:
        return False
    for target in targets:
        if isinstance(target, ast.Attribute):
            return True
        if isinstance(target, ast.Name):
            if func is not None and _linear_close_after(call_node, parent_map, target.id, _scope_for(func, target.id)):
                return True
            if func is not None and _name_is_managed(func, target.id, _scope_for(func, target.id)):
                return True
    return False


def _registration_arg_is_call(registration: ast.Call, inner_call: ast.Call, scope: _Scope) -> bool:
    """The opener (or its closing()-wrapper) is the first arg of an enter/push registration."""
    method: str | None = None
    if (isinstance(registration.func, ast.Attribute) and isinstance(registration.func.value, ast.Name)
            and registration.func.value.id in scope.stacks):
        method = registration.func.attr
    elif isinstance(registration.func, ast.Name):
        rid = registration.func.id
        method = ("enter_context" if rid in scope.enter_regs
                  else "push" if rid in scope.push_regs else None)
    if method is None or method not in (_EXIT_STACK_ENTER_METHODS | _EXIT_STACK_PUSH_METHODS):
        return False
    if not registration.args:
        return False
    arg = registration.args[0]
    if arg is inner_call:
        return True
    # closing(open(...)) directly inside the registration
    return any(child is inner_call for child in ast.walk(arg))


# ── Opener / task recognition and emission ───────────────────────────────────

def _opened_resource_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id if node.func.id in _RESOURCE_OPENER_NAMES else None
    if isinstance(node.func, ast.Attribute):
        full = _attr_chain(node.func)
        if full in _RESOURCE_OPENER_NAMES:
            return full
        if node.func.attr == "open" and _expr_looks_pathlike(node.func.value):
            return "open"
    return None


def _is_fire_and_forget_task(node: ast.AST) -> bool:
    return (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "create_task")


def _with_wrapped_nodes(tree: ast.AST) -> set[int]:
    wrapped: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.With, ast.AsyncWith)):
            continue
        for item in node.items:
            wrapped.add(id(item.context_expr))
            if isinstance(item.context_expr, ast.Call):
                for arg in item.context_expr.args:
                    wrapped.add(id(arg))
    return wrapped


def _build_resource_finding(context: _ResourceFindingContext, index: int, line: int, fname: str) -> AciFinding:
    return build_finding(
        finding_id=f"F-SCAN-{context.next_id + index:04d}", ci_id="CI-22",
        signal="CI22_RESOURCE_CLEANUP_GAP", severity="medium",
        target_file=_relative_path(context.path, context.target_root), line=line,
        excerpt=_line_excerpt(context.text, line),
        reason=(f"'{fname}' opens a resource without a context manager; "
                "the lifecycle may not be closed on exception paths."),
        evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
        recommended_action="Wrap resource-opening calls in a 'with' statement to ensure deterministic cleanup.",
        # Confidence calibrated to measured field precision (~50% on real code:
        # FPs where the resource is handed to the caller or closed in finally).
        # See examples/aci-field-precision/. The fire-and-forget signal below is
        # unmeasured in that corpus and keeps its own confidence.
        confidence=CONFIDENCE_LOW, priority="P2", owner_lane=LANE_NATIVE_STATIC,
        verification_status=VERIFICATION_EXECUTED,
    )


def _build_task_finding(context: _ResourceFindingContext, index: int, line: int) -> AciFinding:
    return build_finding(
        finding_id=f"F-SCAN-{context.next_id + index:04d}", ci_id="CI-22",
        signal="CI22_FIRE_AND_FORGET_TASK", severity="medium",
        target_file=_relative_path(context.path, context.target_root), line=line,
        excerpt=_line_excerpt(context.text, line),
        reason="asyncio.create_task is launched without retaining or awaiting the task, so failures can escape the owning boundary.",
        evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
        recommended_action="Retain the task handle and await, cancel, or explicitly supervise it at the owning boundary.",
        confidence=CONFIDENCE_MEDIUM, priority="P2", owner_lane=LANE_NATIVE_STATIC,
        verification_status=VERIFICATION_EXECUTED,
    )


def scan(path: Path, text: str, target_root: Path, next_id: int) -> list[AciFinding]:
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = _cached_parse(text)
    except SyntaxError:
        return []
    parent_map = _build_parent_map(tree)
    with_wrapped = _with_wrapped_nodes(tree)
    context = _ResourceFindingContext(path=path, text=text, target_root=target_root, next_id=next_id)
    findings: list[AciFinding] = []
    for node in ast.walk(tree):
        if _is_fire_and_forget_task(node):
            findings.append(_build_task_finding(context, len(findings), getattr(node, "lineno", 1)))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or id(node) in with_wrapped:
            continue
        fname = _opened_resource_name(node)
        if fname is None:
            continue
        if _is_managed_open(node, parent_map):
            continue
        findings.append(_build_resource_finding(context, len(findings), node.lineno, fname))
    return findings
