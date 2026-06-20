"""CI-14 tainted-flow detector fixtures (Phase 3 source->sink taint).

Recall cases: untrusted input reaching a dangerous sink in one function MUST be
flagged. Precision cases: constant sinks, parameterized queries, non-source
parameters, and safe argument arrays MUST NOT be flagged — taint detection earns
its keep only if it does not become a false-positive generator.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from aci.aci_scan import scan_target

_SIGNAL = "CI14_TAINTED_FLOW"


def _signals(source: str) -> set[str]:
    scratch = Path(tempfile.mkdtemp())
    (scratch / "m.py").write_text(source, encoding="utf-8")
    report = scan_target(scratch, "full", "core-only", include_external_analyzers=False)
    return {item["signal"] for item in report["findings"]}


# ── recall: tainted flow MUST be detected ────────────────────────────────────

def test_taint_input_into_eval() -> None:
    assert _SIGNAL in _signals("def h():\n    cmd = input()\n    return eval(cmd)\n")


def test_taint_environ_into_os_system_fstring() -> None:
    src = "import os\ndef h():\n    user = os.environ['U']\n    os.system(f'echo {user}')\n"
    assert _SIGNAL in _signals(src)


def test_taint_input_into_subprocess_shell_true() -> None:
    src = "import subprocess\ndef h():\n    c = input()\n    subprocess.run(c, shell=True)\n"
    assert _SIGNAL in _signals(src)


def test_taint_input_into_sql_execute_concat() -> None:
    src = "def h(db):\n    name = input()\n    db.execute('select * from t where n=' + name)\n"
    assert _SIGNAL in _signals(src)


def test_taint_request_arg_into_eval() -> None:
    src = "from flask import request\ndef h():\n    x = request.args.get('q')\n    return eval(x)\n"
    assert _SIGNAL in _signals(src)


def test_taint_argv_into_os_system() -> None:
    src = "import sys, os\ndef h():\n    a = sys.argv[1]\n    os.system(a)\n"
    assert _SIGNAL in _signals(src)


def test_taint_propagates_through_intermediate_assignments() -> None:
    src = "def h():\n    a = input()\n    b = a.strip()\n    c = b\n    return eval(c)\n"
    assert _SIGNAL in _signals(src)


# ── precision: safe forms MUST NOT be flagged ────────────────────────────────

def test_clean_constant_eval_is_not_taint() -> None:
    assert _SIGNAL not in _signals("def h():\n    return eval('1 + 1')\n")


def test_clean_parameterized_query_is_not_taint() -> None:
    src = "def h(db):\n    name = input()\n    db.execute('select * from t where n=?', (name,))\n"
    assert _SIGNAL not in _signals(src)


def test_clean_subprocess_list_without_shell_is_not_taint() -> None:
    src = "import subprocess\ndef h():\n    c = input()\n    subprocess.run([c])\n"
    assert _SIGNAL not in _signals(src)


def test_clean_constant_os_system_is_not_taint() -> None:
    assert _SIGNAL not in _signals("import os\ndef h():\n    os.system('ls')\n")


def test_clean_plain_parameter_is_not_a_source() -> None:
    # A bare function parameter is not treated as untrusted by this bounded pass.
    src = "import os\ndef h(x):\n    os.system('echo ' + str(x))\n"
    assert _SIGNAL not in _signals(src)
