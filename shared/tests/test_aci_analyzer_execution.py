from __future__ import annotations

from pathlib import Path
import json

from aci import aci_analyzer_execution as execmod
from aci.aci_profiles import PROFILE_QUICK_GATE


def test_pytest_no_tests_collected_is_treated_as_nonfatal(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(execmod, "_readiness_for", lambda analyzer_id: execmod.AnalyzerReadiness(
        analyzer_id=analyzer_id,
        executable_path=f"C:/fake/{analyzer_id}.exe",
        availability_state="ready",
        version_text="pytest 9.0.0",
        version_ok=True,
        minimum_version="7.0.0",
    ))

    class Completed:
        returncode = 5
        stdout = "\nno tests ran in 0.01s\n"
        stderr = ""

    monkeypatch.setattr(execmod.subprocess, "run", lambda *args, **kwargs: Completed())
    result = execmod.run_analyzer("pytest", tmp_path, 1)

    assert result.ok is True
    assert result.runtime_state == "no-tests-collected"
    assert result.findings == ()


def test_missing_analyzer_returns_not_installed(tmp_path: Path, monkeypatch) -> None:
    # Force not-installed readiness so the test is deterministic regardless of
    # whether the analyzer binary happens to be installed in the environment
    # (CI installs ruff/pyflakes/mypy/pytest; local dev envs may not).
    monkeypatch.setattr(execmod, "_readiness_for", lambda analyzer_id: execmod.AnalyzerReadiness(
        analyzer_id=analyzer_id,
        executable_path=None,
        availability_state="not-installed",
        version_text=None,
        version_ok=False,
        minimum_version=None,
    ))
    result = execmod.run_analyzer("pyflakes", tmp_path, 1)
    assert result.ok is False
    assert result.runtime_state == "not-installed"


def test_sarif_ready_readiness_summary_contains_known_states() -> None:
    rows = execmod.profile_execution_plan()
    quick_gate = next(row for row in rows if row["profile_id"] == PROFILE_QUICK_GATE)
    assert "ruff" in quick_gate["readiness_summary"]
    assert "pyflakes" in quick_gate["readiness_summary"]


def test_ruff_output_is_normalized_into_findings(tmp_path: Path) -> None:
    stdout = json.dumps(
        [
            {
                "code": "F401",
                "filename": str(tmp_path / "sample.py"),
                "location": {"row": 3},
                "message": "unused import",
            }
        ]
    )
    findings = execmod._ruff_findings(stdout, tmp_path, 10)

    assert len(findings) == 1
    assert findings[0].signal == "EXT_RUFF"
    assert findings[0].line == 3
    assert findings[0].target_file == "sample.py"


def test_mypy_output_is_normalized_into_findings(tmp_path: Path) -> None:
    stdout = f"{tmp_path / 'sample.py'}:5: error: Incompatible return value type\n"
    findings = execmod._mypy_findings(stdout, "", tmp_path, 20)

    assert len(findings) == 1
    assert findings[0].signal == "EXT_MYPY"
    assert findings[0].line == 5
    assert findings[0].severity == "high"
    assert findings[0].evidence_ref == "mypy"


def test_mypy_evidence_ref_includes_error_code(tmp_path: Path) -> None:
    stdout = f"{tmp_path / 'sample.py'}:3: error: Item 'None' of 'int | None' has no attribute 'bit_length'  [union-attr]\n"
    findings = execmod._mypy_findings(stdout, "", tmp_path, 0)

    assert len(findings) == 1
    assert findings[0].evidence_ref == "mypy:union-attr"


def test_ruff_pt_code_maps_to_ci09(tmp_path: Path) -> None:
    stdout = json.dumps([
        {
            "code": "PT001",
            "filename": str(tmp_path / "test_sample.py"),
            "location": {"row": 7},
            "message": "use a simple `assert` statement instead of `unittest`-style `assertEqual`",
        }
    ])
    findings = execmod._ruff_findings(stdout, tmp_path, 10)
    assert len(findings) == 1
    assert findings[0].ci_id == "CI-09"


def test_ruff_i_code_maps_to_ci13(tmp_path: Path) -> None:
    stdout = json.dumps([
        {
            "code": "I001",
            "filename": str(tmp_path / "sample.py"),
            "location": {"row": 2},
            "message": "Import block is un-sorted or un-formatted",
        }
    ])
    findings = execmod._ruff_findings(stdout, tmp_path, 10)
    assert len(findings) == 1
    assert findings[0].ci_id == "CI-13"


def test_eslint_output_is_normalized_into_findings(tmp_path: Path) -> None:
    stdout = json.dumps([
        {
            "filePath": str(tmp_path / "app.js"),
            "messages": [
                {
                    "ruleId": "no-unused-vars",
                    "severity": 2,
                    "message": "'x' is defined but never used.",
                    "line": 4,
                    "column": 7,
                },
            ],
        }
    ])
    findings = execmod._eslint_findings(stdout, tmp_path, 5)
    assert len(findings) == 1
    assert findings[0].signal == "EXT_ESLINT"
    assert findings[0].line == 4
    assert findings[0].target_file == "app.js"
    assert findings[0].severity == "high"


def test_eslint_typescript_rule_maps_to_ci23(tmp_path: Path) -> None:
    stdout = json.dumps([
        {
            "filePath": str(tmp_path / "widget.ts"),
            "messages": [
                {
                    "ruleId": "@typescript-eslint/no-explicit-any",
                    "severity": 1,
                    "message": "Unexpected any. Specify a different type.",
                    "line": 10,
                    "column": 15,
                },
            ],
        }
    ])
    findings = execmod._eslint_findings(stdout, tmp_path, 1)
    assert findings[0].ci_id == "CI-23"
    assert findings[0].severity == "medium"


def test_eslint_import_rule_maps_to_ci13(tmp_path: Path) -> None:
    stdout = json.dumps([
        {
            "filePath": str(tmp_path / "index.js"),
            "messages": [
                {
                    "ruleId": "import/no-cycle",
                    "severity": 2,
                    "message": "Dependency cycle detected",
                    "line": 1,
                    "column": 1,
                },
            ],
        }
    ])
    findings = execmod._eslint_findings(stdout, tmp_path, 1)
    assert findings[0].ci_id == "CI-13"


def test_eslint_no_messages_produces_no_findings(tmp_path: Path) -> None:
    stdout = json.dumps([{"filePath": str(tmp_path / "clean.js"), "messages": []}])
    findings = execmod._eslint_findings(stdout, tmp_path, 1)
    assert findings == []


def test_tsc_output_is_normalized_into_findings(tmp_path: Path) -> None:
    ts_file = str(tmp_path / "widget.ts")
    stdout = f"{ts_file}(12,5): error TS2339: Property 'foo' does not exist on type 'Bar'.\n"
    findings = execmod._tsc_findings(stdout, "", tmp_path, 20)
    assert len(findings) == 1
    assert findings[0].signal == "EXT_TSC"
    assert findings[0].ci_id == "CI-23"
    assert findings[0].line == 12
    assert findings[0].severity == "high"
    assert "TS2339" in findings[0].evidence_ref


def test_tsc_non_matching_lines_are_ignored(tmp_path: Path) -> None:
    stdout = "Found 1 error in 1 file.\n"
    findings = execmod._tsc_findings(stdout, "", tmp_path, 1)
    assert findings == []


def test_shellcheck_output_is_normalized_into_findings(tmp_path: Path) -> None:
    sh_file = str(tmp_path / "deploy.sh")
    stdout = json.dumps([
        {
            "file": sh_file,
            "line": 7,
            "column": 3,
            "level": "warning",
            "code": 2086,
            "message": "Double quote to prevent globbing and word splitting.",
        }
    ])
    findings = execmod._shellcheck_findings(stdout, tmp_path, 10)
    assert len(findings) == 1
    assert findings[0].signal == "EXT_SHELLCHECK"
    assert findings[0].line == 7
    assert findings[0].target_file == "deploy.sh"
    assert findings[0].ci_id == "CI-21"
    assert "SC2086" in findings[0].evidence_ref


def test_shellcheck_error_level_maps_to_high_severity(tmp_path: Path) -> None:
    sh_file = str(tmp_path / "run.sh")
    stdout = json.dumps([
        {"file": sh_file, "line": 3, "column": 1, "level": "error", "code": 2148, "message": "Tips depend on target shell."}
    ])
    findings = execmod._shellcheck_findings(stdout, tmp_path, 1)
    assert findings[0].severity == "high"
    assert findings[0].ci_id == "CI-21"


def test_shellcheck_style_level_maps_to_ci02(tmp_path: Path) -> None:
    sh_file = str(tmp_path / "run.sh")
    stdout = json.dumps([
        {"file": sh_file, "line": 5, "column": 1, "level": "style", "code": 2034, "message": "Use the same test syntax throughout."}
    ])
    findings = execmod._shellcheck_findings(stdout, tmp_path, 1)
    assert findings[0].ci_id == "CI-02"
    assert findings[0].severity == "medium"


def test_sqlfluff_output_is_normalized_into_findings(tmp_path: Path) -> None:
    sql_file = str(tmp_path / "query.sql")
    stdout = json.dumps([
        {
            "filepath": sql_file,
            "violations": [
                {
                    "code": "LT01",
                    "description": "Unnecessary trailing whitespace.",
                    "name": "trailing_whitespace",
                    "line_no": 3,
                    "line_pos": 10,
                    "warning": False,
                }
            ],
        }
    ])
    findings = execmod._sqlfluff_findings(stdout, tmp_path, 30)
    assert len(findings) == 1
    assert findings[0].signal == "EXT_SQLFLUFF"
    assert findings[0].ci_id == "CI-02"
    assert findings[0].line == 3
    assert findings[0].target_file == "query.sql"
    assert "LT01" in findings[0].evidence_ref


def test_ruff_parse_failure_has_distinct_runtime_state(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(execmod, "_readiness_for", lambda analyzer_id: execmod.AnalyzerReadiness(
        analyzer_id=analyzer_id,
        executable_path=f"C:/fake/{analyzer_id}.exe",
        availability_state="ready",
        version_text="ruff 0.5.0",
        version_ok=True,
        minimum_version="0.1.0",
    ))

    class Completed:
        returncode = 0
        stdout = "this is not json"
        stderr = ""

    monkeypatch.setattr(execmod.subprocess, "run", lambda *args, **kwargs: Completed())
    result = execmod.run_analyzer("ruff", tmp_path, 1)

    assert result.ok is False
    assert result.runtime_state == "parse-failure"


def test_ruff_bad_exit_code_is_runtime_failure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(execmod, "_readiness_for", lambda analyzer_id: execmod.AnalyzerReadiness(
        analyzer_id=analyzer_id,
        executable_path=f"C:/fake/{analyzer_id}.exe",
        availability_state="ready",
        version_text="ruff 0.5.0",
        version_ok=True,
        minimum_version="0.1.0",
    ))

    class Completed:
        returncode = 2
        stdout = "[]"
        stderr = "fatal error"

    monkeypatch.setattr(execmod.subprocess, "run", lambda *args, **kwargs: Completed())
    result = execmod.run_analyzer("ruff", tmp_path, 1)

    assert result.ok is False
    assert result.runtime_state == "runtime-failure"


def test_shellcheck_records_skipped_source_count_when_capped(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(execmod, "_readiness_for", lambda analyzer_id: execmod.AnalyzerReadiness(
        analyzer_id=analyzer_id,
        executable_path=f"C:/fake/{analyzer_id}.exe",
        availability_state="ready",
        version_text="ShellCheck 0.9.0",
        version_ok=True,
        minimum_version="0.7.0",
    ))
    monkeypatch.setattr(execmod, "_find_shell_files", lambda root: [f"/fake/script_{i}.sh" for i in range(250)])

    class Completed:
        returncode = 0
        stdout = "[]"
        stderr = ""

    monkeypatch.setattr(execmod.subprocess, "run", lambda *args, **kwargs: Completed())
    result = execmod.run_analyzer("shellcheck", tmp_path, 1)

    assert result.ok is True
    assert result.skipped_source_file_count == 50


def test_shellcheck_returns_no_applicable_source_when_no_sh_files(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(execmod, "_readiness_for", lambda analyzer_id: execmod.AnalyzerReadiness(
        analyzer_id=analyzer_id,
        executable_path=f"C:/fake/{analyzer_id}.exe",
        availability_state="ready",
        version_text="ShellCheck 0.9.0",
        version_ok=True,
        minimum_version="0.7.0",
    ))
    result = execmod.run_analyzer("shellcheck", tmp_path, 1)
    assert result.ok is False
    assert result.runtime_state == "no-applicable-source"


def test_tsc_returns_no_applicable_source_when_no_tsconfig(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(execmod, "_readiness_for", lambda analyzer_id: execmod.AnalyzerReadiness(
        analyzer_id=analyzer_id,
        executable_path=f"C:/fake/{analyzer_id}.exe",
        availability_state="ready",
        version_text="Version 5.0.0",
        version_ok=True,
        minimum_version=None,
    ))
    result = execmod.run_analyzer("tsc", tmp_path, 1)
    assert result.ok is False
    assert result.runtime_state == "no-applicable-source"


def test_sqlfluff_warning_violation_maps_to_low_severity(tmp_path: Path) -> None:
    sql_file = str(tmp_path / "query.sql")
    stdout = json.dumps([
        {
            "filepath": sql_file,
            "violations": [
                {"code": "LT02", "description": "Expected only single space.", "line_no": 1, "line_pos": 1, "warning": True}
            ],
        }
    ])
    findings = execmod._sqlfluff_findings(stdout, tmp_path, 1)
    assert findings[0].severity == "low"
