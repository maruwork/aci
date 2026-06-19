"""CI-22 Resource Lifecycle Leak detector."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re

try:
    from ..aci_findings import (
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from ._helpers import _relative_path, _line_excerpt, _build_parent_map, _cached_parse
except ImportError:  # pragma: no cover - direct script/module import path
    from aci_findings import (  # type: ignore[no-redef]
        AciFinding, build_finding, LANE_NATIVE_STATIC, VERIFICATION_EXECUTED,
        CONFIDENCE_MEDIUM,
    )
    from detectors._helpers import _relative_path, _line_excerpt, _build_parent_map, _cached_parse  # type: ignore[no-redef]

SIGNALS: frozenset[str] = frozenset({"CI22_RESOURCE_CLEANUP_GAP"})

_RESOURCE_OPENER_NAMES: frozenset[str] = frozenset({
    "open",
    "io.open",
    "codecs.open",
    "os.open",
    "Popen",
    "subprocess.Popen",
    "NamedTemporaryFile",
    "tempfile.NamedTemporaryFile",
    "TemporaryFile",
    "tempfile.TemporaryFile",
    "SpooledTemporaryFile",
    "tempfile.SpooledTemporaryFile",
})
_PATHLIKE_NAME_PATTERN = re.compile(r"(?:^|_)(?:path|paths|file|files|filename|filepath|dir|directory)(?:$|_)")
_PATHLIKE_CONSTRUCTORS: frozenset[str] = frozenset({
    "Path",
    "PurePath",
    "PurePosixPath",
    "PureWindowsPath",
    "pathlib.Path",
    "pathlib.PurePath",
    "pathlib.PurePosixPath",
    "pathlib.PureWindowsPath",
})
_EXIT_STACK_NAMES: frozenset[str] = frozenset({
    "ExitStack",
    "AsyncExitStack",
    "contextlib.ExitStack",
    "contextlib.AsyncExitStack",
})
_EXIT_STACK_ENTER_METHODS: frozenset[str] = frozenset({
    "enter_context",
    "enter_async_context",
})
_RESOURCE_WRAPPER_CONTEXT_NAMES: frozenset[str] = frozenset({
    "closing",
    "contextlib.closing",
})
_PARTIAL_CALL_NAMES: frozenset[str] = frozenset({
    "partial",
    "functools.partial",
})
_EXIT_STACK_CALLBACK_METHODS: frozenset[str] = frozenset({
    "callback",
    "push_async_callback",
})
_EXIT_STACK_PUSH_METHODS: frozenset[str] = frozenset({
    "push",
})


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


def _attribute_chain_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _attribute_chain_name(node.value)
        if base is None:
            return None
        return f"{base}.{node.attr}"
    return None


def _name_looks_pathlike(name: str) -> bool:
    return bool(_PATHLIKE_NAME_PATTERN.search(name.lower()))


def _expr_looks_pathlike(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return _name_looks_pathlike(node.id)
    if isinstance(node, ast.Attribute):
        return _name_looks_pathlike(node.attr) or _expr_looks_pathlike(node.value)
    if isinstance(node, ast.Call):
        call_name = _attribute_chain_name(node.func)
        return call_name in _PATHLIKE_CONSTRUCTORS
    if isinstance(node, ast.Subscript):
        return _expr_looks_pathlike(node.value)
    return False


def _is_close_call(node: ast.Call, varname: str) -> bool:
    if (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == varname
        and node.func.attr in {"close", "__exit__"}
    ):
        return True
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "close"
        and _attribute_chain_name(node.func.value) == "os"
        and node.args
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == varname
    ):
        return True
    if (
        isinstance(node.func, ast.Name)
        and node.func.id == "close"
        and node.args
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == varname
    ):
        return True
    return False


def _is_partial_close_callback(
    node: ast.AST,
    varname: str,
    callback_names: set[str] | None = None,
    callback_with_arg_names: set[str] | None = None,
) -> bool:
    callback_names = callback_names or set()
    callback_with_arg_names = callback_with_arg_names or set()
    if not isinstance(node, ast.Call):
        return False
    call_name = _attribute_chain_name(node.func)
    if call_name not in _PARTIAL_CALL_NAMES or not node.args:
        return False
    callback = node.args[0]
    if (
        isinstance(callback, ast.Attribute)
        and isinstance(callback.value, ast.Name)
        and callback.value.id == varname
        and callback.attr == "close"
    ):
        return True
    if (
        isinstance(callback, ast.Attribute)
        and _attribute_chain_name(callback.value) == "os"
        and callback.attr == "close"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Name)
        and node.args[1].id == varname
    ):
        return True
    if (
        isinstance(callback, ast.Name)
        and callback.id in callback_names
    ):
        return True
    if (
        isinstance(callback, ast.Name)
        and callback.id in callback_with_arg_names
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Name)
        and node.args[1].id == varname
    ):
        return True
    if (
        isinstance(callback, ast.Name)
        and callback.id == "close"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Name)
        and node.args[1].id == varname
    ):
        return True
    return False


def _lambda_default_aliases(node: ast.Lambda, varname: str) -> set[str]:
    aliases: set[str] = set()
    args = node.args.args
    defaults = node.args.defaults
    if not defaults:
        return aliases
    default_bound_args = args[-len(defaults):]
    for arg, default in zip(default_bound_args, defaults):
        if isinstance(default, ast.Name) and default.id == varname:
            aliases.add(arg.arg)
    return aliases


def _lambda_positional_param_names(node: ast.Lambda) -> list[str]:
    return [arg.arg for arg in [*node.args.posonlyargs, *node.args.args]]


def _lambda_closes_first_callback_arg(node: ast.Lambda) -> bool:
    body = node.body
    if not isinstance(body, ast.Call):
        return False
    param_names = _lambda_positional_param_names(node)
    if not param_names:
        return False
    return _is_close_call(body, param_names[0])


def _lambda_closes_name_or_default_alias(node: ast.Lambda, varname: str) -> bool:
    body = node.body
    if not isinstance(body, ast.Call):
        return False
    if _is_close_call(body, varname):
        return True
    return any(_is_close_call(body, alias) for alias in _lambda_default_aliases(node, varname))


def _function_single_expr_call(node: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.Call | None:
    if len(node.body) != 1:
        return None
    statement = node.body[0]
    if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
        return None
    return statement.value


def _function_default_aliases(node: ast.FunctionDef | ast.AsyncFunctionDef, varname: str) -> set[str]:
    aliases: set[str] = set()
    args = [*node.args.posonlyargs, *node.args.args]
    defaults = node.args.defaults
    if defaults:
        default_bound_args = args[-len(defaults):]
        for arg, default in zip(default_bound_args, defaults):
            if isinstance(default, ast.Name) and default.id == varname:
                aliases.add(arg.arg)
    return aliases


def _function_has_required_parameters(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    positional = [*node.args.posonlyargs, *node.args.args]
    required_positional = len(positional) - len(node.args.defaults)
    if required_positional > 0:
        return True
    if node.args.kwonlyargs:
        return True
    if node.args.vararg is not None or node.args.kwarg is not None:
        return True
    return False


def _function_positional_param_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    return [arg.arg for arg in [*node.args.posonlyargs, *node.args.args]]


def _function_closes_first_callback_arg(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    body = _function_single_expr_call(node)
    if body is None:
        return False
    param_names = _function_positional_param_names(node)
    if not param_names:
        return False
    return _is_close_call(body, param_names[0])


def _block_has_close(statements: list[ast.stmt], varname: str) -> bool:
    for stmt in statements:
        for child in ast.walk(stmt):
            if isinstance(child, ast.Call) and _is_close_call(child, varname):
                return True
    return False


def _has_exception_safe_close(func: ast.AST, varname: str) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.Try):
            continue
        if node.finalbody and _block_has_close(node.finalbody, varname):
            return True
        if (
            node.handlers
            and node.orelse
            and all(_block_has_close(handler.body, varname) for handler in node.handlers)
            and _block_has_close(node.orelse, varname)
        ):
            return True
    return False


def _managed_exit_stack_names(func: ast.AST) -> set[str]:
    names: set[str] = set()
    assigned_names: set[str] = set()
    context_names: set[str] = set()
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call_name = _attribute_chain_name(node.value.func)
            if call_name in _EXIT_STACK_NAMES:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigned_names.add(target.id)
        if isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Call):
            call_name = _attribute_chain_name(node.value.func)
            if call_name in _EXIT_STACK_NAMES and isinstance(node.target, ast.Name):
                assigned_names.add(node.target.id)
        if not isinstance(node, (ast.With, ast.AsyncWith)):
            continue
        for item in node.items:
            if isinstance(item.context_expr, ast.Name):
                context_names.add(item.context_expr.id)
            if not isinstance(item.context_expr, ast.Call):
                continue
            call_name = _attribute_chain_name(item.context_expr.func)
            if call_name not in _EXIT_STACK_NAMES:
                continue
            if isinstance(item.optional_vars, ast.Name):
                names.add(item.optional_vars.id)
    names.update(assigned_names & context_names)
    return names


def _managed_stack_method_alias_names(
    func: ast.AST,
    managed_stack_names: set[str],
    method_names: set[str],
) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        value: ast.expr | None = None
        target: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            value = node.value
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            target = node.target
        if not isinstance(target, ast.Name):
            continue
        if (
            isinstance(value, ast.Attribute)
            and isinstance(value.value, ast.Name)
            and value.value.id in managed_stack_names
            and value.attr in method_names
        ):
            names.add(target.id)
    return names


def _managed_resource_wrapper_names(func: ast.AST, varname: str) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        call: ast.Call | None = None
        target: ast.expr | None = None
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call = node.value
            if len(node.targets) == 1:
                target = node.targets[0]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Call):
            call = node.value
            target = node.target
        if call is None or not isinstance(target, ast.Name):
            continue
        call_name = _attribute_chain_name(call.func)
        if call_name not in _RESOURCE_WRAPPER_CONTEXT_NAMES or not call.args:
            continue
        wrapped = call.args[0]
        if isinstance(wrapped, ast.Name) and wrapped.id == varname:
            names.add(target.id)
    return names


def _managed_close_callback_names(func: ast.AST, varname: str) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        value: ast.expr | None = None
        target: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            value = node.value
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            target = node.target
        if not isinstance(target, ast.Name):
            continue
        if (
            isinstance(value, ast.Attribute)
            and isinstance(value.value, ast.Name)
            and value.value.id == varname
            and value.attr == "close"
        ):
            names.add(target.id)
    return names


def _managed_os_close_callback_names(func: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        value: ast.expr | None = None
        target: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            value = node.value
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            target = node.target
        if not isinstance(target, ast.Name):
            continue
        if (
            isinstance(value, ast.Attribute)
            and _attribute_chain_name(value.value) == "os"
                and value.attr == "close"
        ):
            names.add(target.id)
    return names


def _managed_generic_close_callback_with_arg_names(func: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        value: ast.expr | None = None
        target: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            value = node.value
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            target = node.target
        if not isinstance(target, ast.Name):
            continue
        if isinstance(value, ast.Name) and value.id == "close":
            names.add(target.id)
    return names


def _managed_lambda_callback_names(func: ast.AST, varname: str) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        value: ast.expr | None = None
        target: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            value = node.value
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            target = node.target
        if not isinstance(target, ast.Name) or not isinstance(value, ast.Lambda):
            continue
        body = value.body
        if not isinstance(body, ast.Call):
            continue
        if _is_close_call(body, varname):
            names.add(target.id)
            continue
        if any(_is_close_call(body, alias) for alias in _lambda_default_aliases(value, varname)):
            names.add(target.id)
    return names


def _managed_local_helper_callback_names(func: ast.AST, varname: str) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node is func:
            continue
        if _function_has_required_parameters(node):
            continue
        body = _function_single_expr_call(node)
        if body is not None and _is_close_call(body, varname):
            names.add(node.name)
            continue
        if body is not None and any(_is_close_call(body, alias) for alias in _function_default_aliases(node, varname)):
            names.add(node.name)
    return names


def _managed_local_helper_callback_with_arg_names(func: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node is func:
            continue
        if _function_closes_first_callback_arg(node):
            names.add(node.name)
    return names


def _managed_callback_name_aliases(
    func: ast.AST,
    callback_names: set[str],
    callback_with_arg_names: set[str],
) -> tuple[set[str], set[str]]:
    callback_aliases: set[str] = set()
    callback_with_arg_aliases: set[str] = set()
    for node in ast.walk(func):
        value: ast.expr | None = None
        target: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            value = node.value
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            target = node.target
        if not isinstance(target, ast.Name) or not isinstance(value, ast.Name):
            continue
        if value.id in callback_names:
            callback_aliases.add(target.id)
        if value.id in callback_with_arg_names:
            callback_with_arg_aliases.add(target.id)
    return callback_aliases, callback_with_arg_aliases


def _managed_partial_callback_names(
    func: ast.AST,
    varname: str,
    callback_names: set[str] | None = None,
    callback_with_arg_names: set[str] | None = None,
) -> set[str]:
    callback_names = callback_names or set()
    callback_with_arg_names = callback_with_arg_names or set()
    names: set[str] = set()
    for node in ast.walk(func):
        value: ast.expr | None = None
        target: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            value = node.value
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            target = node.target
        if not isinstance(target, ast.Name) or value is None:
            continue
        if _is_partial_close_callback(value, varname, callback_names, callback_with_arg_names):
            names.add(target.id)
    return names


def _managed_lambda_callback_with_arg_names(func: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        value: ast.expr | None = None
        target: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            value = node.value
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            target = node.target
        if not isinstance(target, ast.Name) or not isinstance(value, ast.Lambda):
            continue
        if _lambda_closes_first_callback_arg(value):
            names.add(target.id)
    return names


def _managed_wrapper_name_for_call(
    call_node: ast.Call,
    parent_map: dict[ast.AST, ast.AST],
) -> str | None:
    parent = parent_map.get(call_node)
    if not isinstance(parent, ast.Call):
        return None
    call_name = _attribute_chain_name(parent.func)
    if call_name not in _RESOURCE_WRAPPER_CONTEXT_NAMES or not parent.args:
        return None
    if parent.args[0] is not call_node:
        return None
    assignment = parent_map.get(parent)
    if isinstance(assignment, ast.Assign) and len(assignment.targets) == 1:
        target = assignment.targets[0]
        if isinstance(target, ast.Name):
            return target.id
    if isinstance(assignment, ast.AnnAssign) and isinstance(assignment.target, ast.Name):
        return assignment.target.id
    return None


def _enclosing_statement(node: ast.AST, parent_map: dict[ast.AST, ast.AST]) -> ast.stmt | None:
    cur: ast.AST | None = node
    while cur is not None and not isinstance(cur, ast.stmt):
        cur = parent_map.get(cur)
    return cur if isinstance(cur, ast.stmt) else None


def _statement_siblings(
    stmt: ast.stmt,
    parent_map: dict[ast.AST, ast.AST],
) -> tuple[list[ast.stmt], int] | None:
    parent = parent_map.get(stmt)
    if parent is None:
        return None
    for _, value in ast.iter_fields(parent):
        if (
            isinstance(value, list)
            and value
            and all(isinstance(item, ast.stmt) for item in value)
            and stmt in value
        ):
            return value, value.index(stmt)
    return None


def _simple_statement_has_close(stmt: ast.stmt, varname: str) -> bool:
    if not isinstance(stmt, (ast.Expr, ast.Assign, ast.AnnAssign)):
        return False
    stack: list[ast.AST] = [stmt]
    while stack:
        node = stack.pop()
        if node is not stmt and isinstance(node, ast.Lambda):
            continue
        if isinstance(node, ast.Call) and _is_close_call(node, varname):
            return True
        stack.extend(ast.iter_child_nodes(node))
    return False


def _close_aliases_assigned_in_statement(
    stmt: ast.stmt,
    varname: str,
) -> tuple[set[str], set[str], set[str], set[str], set[str]]:
    bound_aliases: set[str] = set()
    os_aliases: set[str] = set()
    close_name_aliases: set[str] = set()
    lambda_noarg_aliases: set[str] = set()
    lambda_with_arg_aliases: set[str] = set()
    value: ast.expr | None = None
    target: ast.expr | None = None
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
        value = stmt.value
        target = stmt.targets[0]
    elif isinstance(stmt, ast.AnnAssign):
        value = stmt.value
        target = stmt.target
    if not isinstance(target, ast.Name):
        return (
            bound_aliases,
            os_aliases,
            close_name_aliases,
            lambda_noarg_aliases,
            lambda_with_arg_aliases,
        )
    if isinstance(value, ast.Lambda):
        if _lambda_closes_name_or_default_alias(value, varname):
            lambda_noarg_aliases.add(target.id)
        if _lambda_closes_first_callback_arg(value):
            lambda_with_arg_aliases.add(target.id)
        return (
            bound_aliases,
            os_aliases,
            close_name_aliases,
            lambda_noarg_aliases,
            lambda_with_arg_aliases,
        )
    if isinstance(value, ast.Name) and value.id == "close":
        close_name_aliases.add(target.id)
        return (
            bound_aliases,
            os_aliases,
            close_name_aliases,
            lambda_noarg_aliases,
            lambda_with_arg_aliases,
        )
    if not isinstance(value, ast.Attribute):
        return (
            bound_aliases,
            os_aliases,
            close_name_aliases,
            lambda_noarg_aliases,
            lambda_with_arg_aliases,
        )
    if (
        isinstance(value.value, ast.Name)
        and value.value.id == varname
        and value.attr == "close"
    ):
        bound_aliases.add(target.id)
    if _attribute_chain_name(value.value) == "os" and value.attr == "close":
        os_aliases.add(target.id)
    return (
        bound_aliases,
        os_aliases,
        close_name_aliases,
        lambda_noarg_aliases,
        lambda_with_arg_aliases,
    )


def _statement_calls_close_alias(
    stmt: ast.stmt,
    varname: str,
    bound_aliases: set[str],
    os_aliases: set[str],
    close_name_aliases: set[str],
    lambda_noarg_aliases: set[str],
    lambda_with_arg_aliases: set[str],
) -> bool:
    for child in ast.walk(stmt):
        if not isinstance(child, ast.Call) or not isinstance(child.func, ast.Name):
            continue
        if child.func.id in bound_aliases and not child.args:
            return True
        if child.func.id in lambda_noarg_aliases and not child.args:
            return True
        if (
            child.func.id in close_name_aliases
            and child.args
            and isinstance(child.args[0], ast.Name)
            and child.args[0].id == varname
        ):
            return True
        if (
            child.func.id in lambda_with_arg_aliases
            and child.args
            and isinstance(child.args[0], ast.Name)
            and child.args[0].id == varname
        ):
            return True
        if (
            child.func.id in os_aliases
            and child.args
            and isinstance(child.args[0], ast.Name)
            and child.args[0].id == varname
        ):
            return True
    return False


def _has_linear_same_suite_close_after_call(
    call_node: ast.Call,
    parent_map: dict[ast.AST, ast.AST],
    varname: str,
) -> bool:
    stmt = _enclosing_statement(call_node, parent_map)
    if stmt is None:
        return False
    siblings = _statement_siblings(stmt, parent_map)
    if siblings is None:
        return False
    statements, index = siblings
    bound_close_aliases: set[str] = set()
    os_close_aliases: set[str] = set()
    close_name_aliases: set[str] = set()
    lambda_noarg_aliases: set[str] = set()
    lambda_with_arg_aliases: set[str] = set()
    for sibling in statements[index + 1:]:
        if _simple_statement_has_close(sibling, varname):
            return True
        if _statement_calls_close_alias(
            sibling,
            varname,
            bound_close_aliases,
            os_close_aliases,
            close_name_aliases,
            lambda_noarg_aliases,
            lambda_with_arg_aliases,
        ):
            return True
        (
            new_bound_aliases,
            new_os_aliases,
            new_close_name_aliases,
            new_lambda_noarg_aliases,
            new_lambda_with_arg_aliases,
        ) = _close_aliases_assigned_in_statement(
            sibling,
            varname,
        )
        bound_close_aliases.update(new_bound_aliases)
        os_close_aliases.update(new_os_aliases)
        close_name_aliases.update(new_close_name_aliases)
        lambda_noarg_aliases.update(new_lambda_noarg_aliases)
        lambda_with_arg_aliases.update(new_lambda_with_arg_aliases)
        if isinstance(sibling, (ast.Assign, ast.AnnAssign, ast.Expr, ast.Pass)):
            continue
        return False
    return False


def _is_managed_exit_stack_registration(
    node: ast.AST,
    managed_stack_names: set[str],
    varname: str | None = None,
    enter_registrar_names: set[str] | None = None,
) -> bool:
    enter_registrar_names = enter_registrar_names or set()
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Attribute):
        if node.func.attr not in _EXIT_STACK_ENTER_METHODS:
            return False
        if not isinstance(node.func.value, ast.Name) or node.func.value.id not in managed_stack_names:
            return False
    elif isinstance(node.func, ast.Name):
        if node.func.id not in enter_registrar_names:
            return False
    else:
        return False
    if not node.args:
        return False
    first_arg = node.args[0]
    if varname is None:
        return True
    if isinstance(first_arg, ast.Name) and first_arg.id == varname:
        return True
    if isinstance(first_arg, ast.Call):
        call_name = _attribute_chain_name(first_arg.func)
        if call_name in _RESOURCE_WRAPPER_CONTEXT_NAMES and first_arg.args:
            wrapped = first_arg.args[0]
            return isinstance(wrapped, ast.Name) and wrapped.id == varname
    return False


def _is_managed_exit_stack_wrapper_for_call(
    node: ast.AST,
    managed_stack_names: set[str],
    call_node: ast.Call,
    enter_registrar_names: set[str] | None = None,
) -> bool:
    enter_registrar_names = enter_registrar_names or set()
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Attribute):
        if node.func.attr not in _EXIT_STACK_ENTER_METHODS:
            return False
        if not isinstance(node.func.value, ast.Name) or node.func.value.id not in managed_stack_names:
            return False
    elif isinstance(node.func, ast.Name):
        if node.func.id not in enter_registrar_names:
            return False
    else:
        return False
    if not node.args:
        return False
    first_arg = node.args[0]
    if first_arg is call_node:
        return True
    if isinstance(first_arg, ast.Call):
        call_name = _attribute_chain_name(first_arg.func)
        if call_name in _RESOURCE_WRAPPER_CONTEXT_NAMES and first_arg.args:
            return first_arg.args[0] is call_node
    return False


def _is_managed_exit_stack_wrapper_name_registration(
    node: ast.AST,
    managed_stack_names: set[str],
    wrapper_names: set[str],
    enter_registrar_names: set[str] | None = None,
) -> bool:
    enter_registrar_names = enter_registrar_names or set()
    if not wrapper_names:
        return False
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Attribute):
        if node.func.attr not in _EXIT_STACK_ENTER_METHODS:
            return False
        if not isinstance(node.func.value, ast.Name) or node.func.value.id not in managed_stack_names:
            return False
    elif isinstance(node.func, ast.Name):
        if node.func.id not in enter_registrar_names:
            return False
    else:
        return False
    if not node.args:
        return False
    first_arg = node.args[0]
    return isinstance(first_arg, ast.Name) and first_arg.id in wrapper_names


def _is_close_callback_registration(
    node: ast.AST,
    managed_stack_names: set[str],
    varname: str,
    callback_names: set[str] | None = None,
    callback_with_arg_names: set[str] | None = None,
    partial_callback_names: set[str] | None = None,
    partial_callback_with_arg_names: set[str] | None = None,
    callback_registrar_names: set[str] | None = None,
) -> bool:
    callback_names = callback_names or set()
    callback_with_arg_names = callback_with_arg_names or set()
    partial_callback_names = partial_callback_names or callback_names
    partial_callback_with_arg_names = partial_callback_with_arg_names or callback_with_arg_names
    callback_registrar_names = callback_registrar_names or set()
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Attribute):
        if node.func.attr not in _EXIT_STACK_CALLBACK_METHODS:
            return False
        if not isinstance(node.func.value, ast.Name) or node.func.value.id not in managed_stack_names:
            return False
    elif isinstance(node.func, ast.Name):
        if node.func.id not in callback_registrar_names:
            return False
    else:
        return False
    if not node.args:
        return False
    callback = node.args[0]
    if (
        isinstance(callback, ast.Attribute)
        and isinstance(callback.value, ast.Name)
        and callback.value.id == varname
        and callback.attr == "close"
    ):
        return True
    if isinstance(callback, ast.Name) and callback.id in callback_names:
        return True
    if (
        isinstance(callback, ast.Name)
        and callback.id in callback_with_arg_names
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Name)
        and node.args[1].id == varname
    ):
        return True
    if (
        isinstance(callback, ast.Name)
        and callback.id == "close"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Name)
        and node.args[1].id == varname
    ):
        return True
    if (
        isinstance(callback, ast.Attribute)
        and _attribute_chain_name(callback.value) == "os"
        and callback.attr == "close"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Name)
        and node.args[1].id == varname
    ):
        return True
    if _is_partial_close_callback(
        callback,
        varname,
        partial_callback_names,
        partial_callback_with_arg_names,
    ):
        return True
    if isinstance(callback, ast.Lambda):
        body = callback.body
        if isinstance(body, ast.Call):
            if _is_close_call(body, varname):
                return True
            for alias in _lambda_default_aliases(callback, varname):
                if _is_close_call(body, alias):
                    return True
            if (
                len(node.args) >= 2
                and isinstance(node.args[1], ast.Name)
                and node.args[1].id == varname
                and _lambda_closes_first_callback_arg(callback)
            ):
                return True
    return False


def _is_exit_stack_push_registration(
    node: ast.AST,
    managed_stack_names: set[str],
    varname: str | None = None,
    push_registrar_names: set[str] | None = None,
) -> bool:
    push_registrar_names = push_registrar_names or set()
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Attribute):
        if node.func.attr not in _EXIT_STACK_PUSH_METHODS:
            return False
        if not isinstance(node.func.value, ast.Name) or node.func.value.id not in managed_stack_names:
            return False
    elif isinstance(node.func, ast.Name):
        if node.func.id not in push_registrar_names:
            return False
    else:
        return False
    if not node.args:
        return False
    first_arg = node.args[0]
    if varname is None:
        return True
    if isinstance(first_arg, ast.Name) and first_arg.id == varname:
        return True
    if isinstance(first_arg, ast.Call):
        call_name = _attribute_chain_name(first_arg.func)
        if call_name in _RESOURCE_WRAPPER_CONTEXT_NAMES and first_arg.args:
            wrapped = first_arg.args[0]
            return isinstance(wrapped, ast.Name) and wrapped.id == varname
    return False


def _is_exit_stack_push_wrapper_for_call(
    node: ast.AST,
    managed_stack_names: set[str],
    call_node: ast.Call,
    push_registrar_names: set[str] | None = None,
) -> bool:
    push_registrar_names = push_registrar_names or set()
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Attribute):
        if node.func.attr not in _EXIT_STACK_PUSH_METHODS:
            return False
        if not isinstance(node.func.value, ast.Name) or node.func.value.id not in managed_stack_names:
            return False
    elif isinstance(node.func, ast.Name):
        if node.func.id not in push_registrar_names:
            return False
    else:
        return False
    if not node.args:
        return False
    first_arg = node.args[0]
    if first_arg is call_node:
        return True
    if isinstance(first_arg, ast.Call):
        call_name = _attribute_chain_name(first_arg.func)
        if call_name in _RESOURCE_WRAPPER_CONTEXT_NAMES and first_arg.args:
            return first_arg.args[0] is call_node
    return False


def _is_exit_stack_push_wrapper_name_registration(
    node: ast.AST,
    managed_stack_names: set[str],
    wrapper_names: set[str],
    push_registrar_names: set[str] | None = None,
) -> bool:
    push_registrar_names = push_registrar_names or set()
    if not wrapper_names:
        return False
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Attribute):
        if node.func.attr not in _EXIT_STACK_PUSH_METHODS:
            return False
        if not isinstance(node.func.value, ast.Name) or node.func.value.id not in managed_stack_names:
            return False
    elif isinstance(node.func, ast.Name):
        if node.func.id not in push_registrar_names:
            return False
    else:
        return False
    if not node.args:
        return False
    first_arg = node.args[0]
    return isinstance(first_arg, ast.Name) and first_arg.id in wrapper_names


def _name_is_managed(func: ast.AST, varname: str) -> bool:
    """True when a handle bound to `varname` is returned, exception-safely
    closed, or transferred to an owning attribute."""
    managed_stack_names = _managed_exit_stack_names(func)
    wrapper_names = _managed_resource_wrapper_names(func, varname)
    enter_registrar_names = _managed_stack_method_alias_names(
        func,
        managed_stack_names,
        set(_EXIT_STACK_ENTER_METHODS),
    )
    base_callback_names = (
        _managed_close_callback_names(func, varname)
        | _managed_lambda_callback_names(func, varname)
        | _managed_local_helper_callback_names(func, varname)
    )
    callback_with_arg_names = (
        _managed_generic_close_callback_with_arg_names(func)
        |
        _managed_os_close_callback_names(func)
        | _managed_lambda_callback_with_arg_names(func)
        | _managed_local_helper_callback_with_arg_names(func)
    )
    partial_callback_alias_names, partial_callback_with_arg_alias_names = _managed_callback_name_aliases(
        func,
        base_callback_names,
        callback_with_arg_names,
    )
    partial_aware_callback_names = base_callback_names | partial_callback_alias_names
    partial_aware_callback_with_arg_names = callback_with_arg_names | partial_callback_with_arg_alias_names
    partial_callback_names = _managed_partial_callback_names(
        func,
        varname,
        partial_aware_callback_names,
        partial_aware_callback_with_arg_names,
    )
    callback_names = base_callback_names | partial_callback_names
    push_registrar_names = _managed_stack_method_alias_names(
        func,
        managed_stack_names,
        set(_EXIT_STACK_PUSH_METHODS),
    )
    callback_registrar_names = _managed_stack_method_alias_names(
        func,
        managed_stack_names,
        set(_EXIT_STACK_CALLBACK_METHODS),
    )
    for node in ast.walk(func):
        if isinstance(node, ast.Return):
            value = node.value
            if isinstance(value, ast.Name) and value.id == varname:
                return True
            if isinstance(value, (ast.Tuple, ast.List)):
                if any(isinstance(item, ast.Name) and item.id == varname for item in value.elts):
                    return True
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if isinstance(item.context_expr, ast.Name) and item.context_expr.id == varname:
                    return True
                if isinstance(item.context_expr, ast.Name) and item.context_expr.id in wrapper_names:
                    return True
                if (
                    isinstance(item.context_expr, ast.Call)
                    and any(
                        isinstance(child, ast.Name) and child.id == varname
                        for child in ast.walk(item.context_expr)
                    )
                ):
                    return True
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name) and node.value.id == varname:
            if any(isinstance(target, ast.Attribute) for target in node.targets):
                return True
        if _is_managed_exit_stack_registration(node, managed_stack_names, varname, enter_registrar_names):
            return True
        if _is_managed_exit_stack_wrapper_name_registration(
            node,
            managed_stack_names,
            wrapper_names,
            enter_registrar_names,
        ):
            return True
        if _is_exit_stack_push_registration(node, managed_stack_names, varname, push_registrar_names):
            return True
        if _is_exit_stack_push_wrapper_name_registration(
            node,
            managed_stack_names,
            wrapper_names,
            push_registrar_names,
        ):
            return True
        if _is_close_callback_registration(
            node,
            managed_stack_names,
            varname,
            callback_names,
            callback_with_arg_names,
            partial_aware_callback_names,
            partial_aware_callback_with_arg_names,
            callback_registrar_names,
        ):
            return True
    return _has_exception_safe_close(func, varname)


def _is_managed_open(call_node: ast.Call, parent_map: dict[ast.AST, ast.AST]) -> bool:
    """Approximate dataflow: is the opened handle's lifecycle managed?"""
    parent = parent_map.get(call_node)
    if isinstance(parent, (ast.Return, ast.withitem)):
        return True
    func = _enclosing_function(call_node, parent_map)
    if func is not None:
        managed_stack_names = _managed_exit_stack_names(func)
        enter_registrar_names = _managed_stack_method_alias_names(
            func,
            managed_stack_names,
            set(_EXIT_STACK_ENTER_METHODS),
        )
        push_registrar_names = _managed_stack_method_alias_names(
            func,
            managed_stack_names,
            set(_EXIT_STACK_PUSH_METHODS),
        )
        if _is_managed_exit_stack_registration(
            parent,
            managed_stack_names,
            enter_registrar_names=enter_registrar_names,
        ):
            return True
        if _is_exit_stack_push_registration(parent, managed_stack_names, push_registrar_names=push_registrar_names):
            return True
        grandparent = parent_map.get(parent) if parent is not None else None
        if _is_managed_exit_stack_wrapper_for_call(
            grandparent,
            managed_stack_names,
            call_node,
            enter_registrar_names,
        ):
            return True
        if _is_exit_stack_push_wrapper_for_call(
            grandparent,
            managed_stack_names,
            call_node,
            push_registrar_names,
        ):
            return True
        wrapper_name = _managed_wrapper_name_for_call(call_node, parent_map)
        if wrapper_name is not None and _name_is_managed(func, wrapper_name):
            return True
    if isinstance(parent, ast.Assign):
        targets = parent.targets
    elif isinstance(parent, ast.AnnAssign):
        targets = [parent.target]
    else:
        return False
    for target in targets:
        if isinstance(target, ast.Attribute):
            return True
        if isinstance(target, ast.Name):
            if _has_linear_same_suite_close_after_call(call_node, parent_map, target.id):
                return True
            if func is not None and _name_is_managed(func, target.id):
                return True
    return False


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


def _opened_resource_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id if node.func.id in _RESOURCE_OPENER_NAMES else None
    if isinstance(node.func, ast.Attribute):
        full_name = _attribute_chain_name(node.func)
        if full_name in _RESOURCE_OPENER_NAMES:
            return full_name
        if node.func.attr == "open" and _expr_looks_pathlike(node.func.value):
            return "open"
    return None


def _is_fire_and_forget_task(node: ast.AST) -> bool:
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return False
    call = node.value
    if isinstance(call.func, ast.Attribute):
        if call.func.attr != "create_task":
            return False
        if isinstance(call.func.value, ast.Name) and call.func.value.id == "asyncio":
            return True
        return True
    return False


def _build_resource_finding(
    context: _ResourceFindingContext,
    finding_index: int,
    line: int,
    fname: str,
) -> AciFinding:
    return build_finding(
        finding_id=f"F-SCAN-{context.next_id + finding_index:04d}",
        ci_id="CI-22",
        signal="CI22_RESOURCE_CLEANUP_GAP",
        severity="medium",
        target_file=_relative_path(context.path, context.target_root),
        line=line,
        excerpt=_line_excerpt(context.text, line),
        reason=(
            f"'{fname}' opens a resource without a context manager; "
            "the lifecycle may not be closed on exception paths."
        ),
        evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
        recommended_action=(
            "Wrap resource-opening calls in a 'with' statement to ensure "
            "deterministic cleanup."
        ),
        confidence=CONFIDENCE_MEDIUM,
        priority="P2",
        owner_lane=LANE_NATIVE_STATIC,
        verification_status=VERIFICATION_EXECUTED,
    )


def _build_task_finding(context: _ResourceFindingContext, finding_index: int, line: int) -> AciFinding:
    return build_finding(
        finding_id=f"F-SCAN-{context.next_id + finding_index:04d}",
        ci_id="CI-22",
        signal="CI22_FIRE_AND_FORGET_TASK",
        severity="medium",
        target_file=_relative_path(context.path, context.target_root),
        line=line,
        excerpt=_line_excerpt(context.text, line),
        reason="asyncio.create_task is launched without retaining or awaiting the task, so failures can escape the owning boundary.",
        evidence_ref="shared/core/aci-code-inspection-execution-spec.md",
        recommended_action="Retain the task handle and await, cancel, or explicitly supervise it at the owning boundary.",
        confidence=CONFIDENCE_MEDIUM,
        priority="P2",
        owner_lane=LANE_NATIVE_STATIC,
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
        if not isinstance(node, ast.Call):
            continue
        if id(node) in with_wrapped:
            continue
        fname = _opened_resource_name(node)
        if fname is None or fname not in _RESOURCE_OPENER_NAMES:
            continue
        if _is_managed_open(node, parent_map):
            continue
        findings.append(_build_resource_finding(context, len(findings), node.lineno, fname))
    return findings
