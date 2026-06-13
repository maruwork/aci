"""Detector fixture tests for native CI-pattern detectors.

Each test verifies that a specific detector:
- triggers on a minimal fixture that matches the pattern
- does NOT trigger on a clean fixture that avoids the pattern

Security note: eval(), exec(), and subprocess shell=True appear in fixture strings
written to temporary files. They are NOT executed by this process — they are test
inputs designed to trigger ACI's pattern detectors (CI-14). This is intentional.
"""
from __future__ import annotations

from pathlib import Path

from aci.aci_scan import scan_target


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _signals(report: dict) -> set[str]:
    return {item["signal"] for item in report["findings"]}


def _scan(tmp_path: Path) -> dict:
    return scan_target(tmp_path, "full", "core-only", include_external_analyzers=False)


# ── CI-02 (Spaghetti Code) ─────────────────────────────────────────────────

def test_ci02_triggers_on_deep_nesting(tmp_path: Path) -> None:
    _write(
        tmp_path / "spaghetti.py",
        "\n".join([
            "def f(a):",
            "    if a:",
            "        if a > 1:",
            "            if a > 2:",
            "                if a > 3:",
            "                    if a > 4:",
            "                        return a",
        ]),
    )
    assert "CI02_SPAGHETTI_CODE" in _signals(_scan(tmp_path))


def test_ci02_clean_on_shallow_nesting(tmp_path: Path) -> None:
    _write(
        tmp_path / "clean.py",
        "\n".join([
            "def f(a):",
            "    if a:",
            "        return a",
            "    return 0",
        ]),
    )
    assert "CI02_SPAGHETTI_CODE" not in _signals(_scan(tmp_path))


# ── CI-02 (Long Function) ─────────────────────────────────────────────────

def test_ci02_long_function_triggers(tmp_path: Path) -> None:
    lines = ["def process():"] + ["    x = 1" for _ in range(51)]
    _write(tmp_path / "long.py", "\n".join(lines))
    assert "CI02_LONG_FUNCTION" in _signals(_scan(tmp_path))


def test_ci02_long_function_clean_on_short_function(tmp_path: Path) -> None:
    _write(tmp_path / "short.py", "def process():\n    return 1\n")
    assert "CI02_LONG_FUNCTION" not in _signals(_scan(tmp_path))


# ── CI-04 (God Class) ─────────────────────────────────────────────────────

def test_ci04_god_class_triggers_on_many_methods(tmp_path: Path) -> None:
    methods = "\n".join(f"    def method_{i}(self): pass" for i in range(21))
    _write(tmp_path / "god.py", f"class Mega:\n{methods}\n")
    assert "CI04_GOD_CLASS" in _signals(_scan(tmp_path))


def test_ci04_god_class_triggers_on_many_attributes(tmp_path: Path) -> None:
    attrs = "\n".join(f"        self.attr_{i} = {i}" for i in range(16))
    _write(tmp_path / "god.py", f"class Big:\n    def __init__(self):\n{attrs}\n")
    assert "CI04_GOD_CLASS" in _signals(_scan(tmp_path))


def test_ci04_god_class_clean_on_small_class(tmp_path: Path) -> None:
    _write(
        tmp_path / "small.py",
        "class Small:\n    def method_a(self): pass\n    def method_b(self): pass\n",
    )
    assert "CI04_GOD_CLASS" not in _signals(_scan(tmp_path))


# ── CI-03 (TODO/HACK markers) ──────────────────────────────────────────────

def test_ci03_triggers_on_todo_comment(tmp_path: Path) -> None:
    _write(tmp_path / "markers.py", "# TODO: remove this\nx = 1\n")
    assert "CI03_TODO_HACK" in _signals(_scan(tmp_path))


def test_ci03_clean_on_no_markers(tmp_path: Path) -> None:
    _write(tmp_path / "clean.py", "x = 1\n")
    assert "CI03_TODO_HACK" not in _signals(_scan(tmp_path))


# ── CI-05 (Copy-Paste Code) ────────────────────────────────────────────────

def test_ci05_triggers_on_duplicate_function_across_files(tmp_path: Path) -> None:
    body = "\n".join([
        "def compute(x, y):",
        "    result = x * y",
        "    result += x",
        "    result -= y",
        "    return result",
        "",
    ])
    _write(tmp_path / "module_a.py", body)
    _write(tmp_path / "module_b.py", body)
    assert "CI05_COPY_PASTE_CODE" in _signals(_scan(tmp_path))


def test_ci05_clean_on_unique_function_bodies(tmp_path: Path) -> None:
    _write(tmp_path / "module_a.py", "def add(x, y):\n    return x + y\n")
    _write(tmp_path / "module_b.py", "def mul(x, y):\n    return x * y\n")
    assert "CI05_COPY_PASTE_CODE" not in _signals(_scan(tmp_path))


# ── CI-06 (Magic Number) ─────────────────────────────────────────────────
# CI-06 requires the same non-trivial literal in 3+ distinct files.

def test_ci06_triggers_on_same_literal_across_three_files(tmp_path: Path) -> None:
    literal_line = "result = x * 7777\n"
    for name in ("a.py", "b.py", "c.py"):
        _write(tmp_path / name, f"def f(x):\n    {literal_line.strip()}\n    return result\n")
    assert "CI06_MAGIC_NUMBER" in _signals(_scan(tmp_path))


def test_ci06_clean_when_literal_in_fewer_than_three_files(tmp_path: Path) -> None:
    literal_line = "result = x * 7777\n"
    for name in ("a.py", "b.py"):
        _write(tmp_path / name, f"def f(x):\n    {literal_line.strip()}\n    return result\n")
    assert "CI06_MAGIC_NUMBER" not in _signals(_scan(tmp_path))


def test_ci06_clean_on_named_constant_definition(tmp_path: Path) -> None:
    for name in ("a.py", "b.py", "c.py"):
        _write(tmp_path / name, "LIMIT = 7777\n")
    assert "CI06_MAGIC_NUMBER" not in _signals(_scan(tmp_path))


# ── CI-12 (Poltergeist) ───────────────────────────────────────────────────

def test_ci12_triggers_on_pure_delegation_class(tmp_path: Path) -> None:
    _write(
        tmp_path / "poltergeist.py",
        "\n".join([
            "class Wrapper:",
            "    def __init__(self, inner):",
            "        self.inner = inner",
            "    def process(self, x):",
            "        return self.inner.process(x)",
        ]),
    )
    assert "CI12_POLTERGEIST" in _signals(_scan(tmp_path))


def test_ci12_clean_on_class_with_real_logic(tmp_path: Path) -> None:
    _write(
        tmp_path / "real_class.py",
        "\n".join([
            "class Processor:",
            "    def __init__(self, value):",
            "        self.value = value",
            "    def compute(self):",
            "        return self.value * 2 + 1",
        ]),
    )
    assert "CI12_POLTERGEIST" not in _signals(_scan(tmp_path))


# ── CI-14 (Dynamic Code Execution) ────────────────────────────────────────

def test_ci14_dynamic_code_triggers_on_eval(tmp_path: Path) -> None:
    _write(tmp_path / "danger.py", "result = eval('1 + 1')\n")
    assert "CI14_DYNAMIC_CODE_EXECUTION" in _signals(_scan(tmp_path))


def test_ci14_dynamic_code_clean_on_no_eval(tmp_path: Path) -> None:
    _write(tmp_path / "clean.py", "result = 1 + 1\n")
    assert "CI14_DYNAMIC_CODE_EXECUTION" not in _signals(_scan(tmp_path))


# ── CI-14 (Subprocess shell=True) ─────────────────────────────────────────

def test_ci14_subprocess_triggers_on_shell_true(tmp_path: Path) -> None:
    _write(
        tmp_path / "shell.py",
        "import subprocess\nsubprocess.run('ls', shell=True)\n",
    )
    assert "CI14_SUBPROCESS_SHELL_TRUE" in _signals(_scan(tmp_path))


def test_ci14_subprocess_clean_on_shell_false(tmp_path: Path) -> None:
    _write(
        tmp_path / "clean.py",
        "import subprocess\nsubprocess.run(['ls'])\n",
    )
    assert "CI14_SUBPROCESS_SHELL_TRUE" not in _signals(_scan(tmp_path))


# ── CI-14 (Plaintext Secret) ──────────────────────────────────────────────

def test_ci14_secret_triggers_on_api_key_literal(tmp_path: Path) -> None:
    _write(tmp_path / "secrets.py", 'API_KEY = "SECRET12345"\n')
    assert "CI14_PLAINTEXT_SECRET" in _signals(_scan(tmp_path))


def test_ci14_secret_clean_on_env_var_reference(tmp_path: Path) -> None:
    _write(tmp_path / "clean.py", 'import os\nAPI_KEY = os.environ["API_KEY"]\n')
    assert "CI14_PLAINTEXT_SECRET" not in _signals(_scan(tmp_path))


# ── CI-14 (Insecure HTTP) ─────────────────────────────────────────────────

def test_ci14_http_triggers_on_plain_http_url(tmp_path: Path) -> None:
    _write(
        tmp_path / "http.py",
        'ENDPOINT = "http://internal.example.local/api"\n',
    )
    assert "CI14_INSECURE_HTTP" in _signals(_scan(tmp_path))


def test_ci14_http_clean_on_https_url(tmp_path: Path) -> None:
    _write(
        tmp_path / "clean.py",
        'ENDPOINT = "https://internal.example.local/api"\n',
    )
    assert "CI14_INSECURE_HTTP" not in _signals(_scan(tmp_path))


# ── CI-18 (Parameter Cluster) ─────────────────────────────────────────────

def test_ci18_triggers_on_many_positional_params(tmp_path: Path) -> None:
    _write(
        tmp_path / "cluster.py",
        "def process(name, value, kind, source, target, limit):\n    pass\n",
    )
    assert "CI18_PARAMETER_CLUSTER" in _signals(_scan(tmp_path))


def test_ci18_clean_on_few_params(tmp_path: Path) -> None:
    _write(tmp_path / "clean.py", "def process(name, value):\n    pass\n")
    assert "CI18_PARAMETER_CLUSTER" not in _signals(_scan(tmp_path))


# ── CI-21 (Broad Exception Swallow) ───────────────────────────────────────

def test_ci21_triggers_on_bare_except_exception(tmp_path: Path) -> None:
    _write(
        tmp_path / "handler.py",
        "try:\n    pass\nexcept Exception:\n    pass\n",
    )
    assert "CI21_BROAD_EXCEPTION_SWALLOW" in _signals(_scan(tmp_path))


def test_ci21_clean_on_named_exception(tmp_path: Path) -> None:
    _write(
        tmp_path / "clean.py",
        "try:\n    pass\nexcept ValueError:\n    pass\n",
    )
    assert "CI21_BROAD_EXCEPTION_SWALLOW" not in _signals(_scan(tmp_path))


def test_ci21_clean_on_bounded_retry_continue(tmp_path: Path) -> None:
    _write(
        tmp_path / "retry.py",
        "\n".join([
            "for i in range(3):",
            "    try:",
            "        pass",
            "    except Exception:",
            "        continue",
        ]),
    )
    assert "CI21_BROAD_EXCEPTION_SWALLOW" not in _signals(_scan(tmp_path))


# ── CI-21 (Silent Exception Return) ──────────────────────────────────────

def test_ci21_silent_exception_return_triggers(tmp_path: Path) -> None:
    _write(
        tmp_path / "fetch.py",
        "\n".join([
            "def fetch(url):",
            "    try:",
            "        return do_request(url)",
            "    except Exception:",
            "        return None",
        ]),
    )
    assert "CI21_SILENT_EXCEPTION_RETURN" in _signals(_scan(tmp_path))


def test_ci21_silent_exception_return_clean_on_specific_exception(tmp_path: Path) -> None:
    _write(
        tmp_path / "parse.py",
        "\n".join([
            "def parse(text):",
            "    try:",
            "        return int(text)",
            "    except ValueError:",
            "        return None",
        ]),
    )
    assert "CI21_SILENT_EXCEPTION_RETURN" not in _signals(_scan(tmp_path))


def test_ci21_silent_exception_return_clean_on_handler_with_multiple_statements(tmp_path: Path) -> None:
    _write(
        tmp_path / "logged.py",
        "\n".join([
            "def fetch(url):",
            "    try:",
            "        return do_request(url)",
            "    except Exception:",
            '        log("error")',
            "        return None",
        ]),
    )
    assert "CI21_SILENT_EXCEPTION_RETURN" not in _signals(_scan(tmp_path))


# ── CI-22 (Resource Lifecycle Leak) ───────────────────────────────────────

def test_ci22_triggers_on_open_without_with(tmp_path: Path) -> None:
    _write(tmp_path / "leak.py", 'f = open("data.txt")\n')
    assert "CI22_RESOURCE_CLEANUP_GAP" in _signals(_scan(tmp_path))


def test_ci22_clean_on_open_with_context_manager(tmp_path: Path) -> None:
    _write(
        tmp_path / "clean.py",
        'with open("data.txt") as f:\n    data = f.read()\n',
    )
    assert "CI22_RESOURCE_CLEANUP_GAP" not in _signals(_scan(tmp_path))


# ── CI-23 (Contract Field Drift) ──────────────────────────────────────────

def test_ci23_triggers_on_kwargs_with_multiple_field_accesses(tmp_path: Path) -> None:
    _write(
        tmp_path / "drift.py",
        "\n".join([
            "def process(**kwargs):",
            '    name = kwargs["name"]',
            '    value = kwargs["value"]',
            "    return name, value",
        ]),
    )
    assert "CI23_CONTRACT_FIELD_DRIFT" in _signals(_scan(tmp_path))


def test_ci23_clean_on_explicit_params(tmp_path: Path) -> None:
    _write(
        tmp_path / "clean.py",
        "def process(name, value):\n    return name, value\n",
    )
    assert "CI23_CONTRACT_FIELD_DRIFT" not in _signals(_scan(tmp_path))


# ── CI-25 (Environment Drift) ─────────────────────────────────────────────

def test_ci25_triggers_on_datetime_now_without_tz(tmp_path: Path) -> None:
    _write(
        tmp_path / "drift.py",
        "from datetime import datetime\nts = datetime.now()\n",
    )
    assert "CI25_ENVIRONMENT_DRIFT" in _signals(_scan(tmp_path))


def test_ci25_clean_on_datetime_now_with_utc(tmp_path: Path) -> None:
    _write(
        tmp_path / "clean.py",
        "from datetime import datetime, UTC\nts = datetime.now(UTC)\n",
    )
    assert "CI25_ENVIRONMENT_DRIFT" not in _signals(_scan(tmp_path))


# ── CI-26 (Race Hazard) ───────────────────────────────────────────────────

def test_ci26_triggers_on_global_mutation(tmp_path: Path) -> None:
    _write(
        tmp_path / "race.py",
        "\n".join([
            "_counter = 0",
            "",
            "def increment():",
            "    global _counter",
            "    _counter += 1",
        ]),
    )
    assert "CI26_RACE_HAZARD" in _signals(_scan(tmp_path))


def test_ci26_clean_on_no_global_mutation(tmp_path: Path) -> None:
    _write(
        tmp_path / "clean.py",
        "\n".join([
            "def increment(counter):",
            "    return counter + 1",
        ]),
    )
    assert "CI26_RACE_HAZARD" not in _signals(_scan(tmp_path))


# ── T20: Resolved baseline entries ────────────────────────────────────────

def test_resolved_baseline_entries_reported_when_finding_disappears(tmp_path: Path) -> None:
    _write(tmp_path / "clean.py", "print('ok')\n")
    _write(
        tmp_path / "operations.toml",
        "\n".join([
            "[baseline]",
            'entries = [{ ci_id = "CI-03", target_file = "clean.py", line = 1 }]',
        ]),
    )

    report = scan_target(
        tmp_path,
        "full",
        "core-only",
        tmp_path / "operations.toml",
        include_external_analyzers=False,
    )

    assert report["summary"]["resolved_baseline_count"] == 1
    resolved = report["resolved_baseline_entries"]
    assert len(resolved) == 1
    assert resolved[0]["ci_id"] == "CI-03"
    assert resolved[0]["lifecycle_state"] == "resolved"
