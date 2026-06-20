from __future__ import annotations

from pathlib import Path
import json

from aci import aci_analyzer_execution as execmod
from aci import _analyzer_commands as cmdmod
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


def test_pytest_command_disables_cacheprovider_writes(tmp_path: Path) -> None:
    command = cmdmod._pytest_command(tmp_path)
    assert command == [cmdmod.sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(tmp_path)]


def test_pytest_command_uses_workspace_scratch_when_available(tmp_path: Path) -> None:
    (tmp_path / "workspace").mkdir()
    command = cmdmod._pytest_command(tmp_path)
    assert command == [
        cmdmod.sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "--ignore",
        str(tmp_path / "workspace"),
        "--basetemp",
        str(tmp_path / "workspace" / ".aci-pytest-tmp"),
        str(tmp_path),
    ]


def test_pytest_command_prefers_conventional_test_shelves(tmp_path: Path) -> None:
    (tmp_path / "shared" / "tests").mkdir(parents=True)
    command = cmdmod._pytest_command(tmp_path)

    assert command == [
        cmdmod.sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        str(tmp_path / "shared" / "tests"),
    ]


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


def test_codeql_reports_not_installed_when_absent(monkeypatch) -> None:
    monkeypatch.setattr(execmod, "which", lambda analyzer_id: None)
    readiness = execmod._readiness_for("codeql")

    assert readiness.availability_state == "not-installed"
    # codeql now has an execution adapter (database build + analyze), so it is
    # execution-ready; it stays opt-in (not run by default) because it is heavy.
    assert readiness.execution_support_level == "execution-ready"
    assert readiness.default_policy == "opt-in"


def test_codeql_is_ready_when_installed_and_version_ok(monkeypatch) -> None:
    monkeypatch.setattr(execmod, "which", lambda analyzer_id: f"C:/fake/{analyzer_id}.exe")
    monkeypatch.setattr(execmod, "_probe_version", lambda analyzer_id, executable_path: ("CodeQL 2.25.6", True))

    readiness = execmod._readiness_for("codeql")

    assert readiness.availability_state == "ready"
    assert readiness.execution_support_level == "execution-ready"


def test_sarif_ready_readiness_summary_contains_known_states() -> None:
    rows = execmod.profile_execution_plan()
    quick_gate = next(row for row in rows if row["profile_id"] == PROFILE_QUICK_GATE)
    assert "ruff" in quick_gate["readiness_summary"]
    assert "pyflakes" in quick_gate["readiness_summary"]


def test_full_profile_readiness_summary_includes_semgrep() -> None:
    rows = execmod.profile_execution_plan()
    full = next(row for row in rows if row["profile_id"] == "full")
    assert "semgrep" in full["readiness_summary"]
    assert "codeql" in full["optional_opt_in_analyzers"]


def test_optional_security_analyzers_are_cataloged() -> None:
    from aci.aci_analyzers import analyzer_catalog

    catalog = {entry["analyzer_id"]: entry for entry in analyzer_catalog()}
    ids = set(catalog)
    assert {"gitleaks", "osv-scanner", "trivy"} <= ids
    assert catalog["codeql"]["support_level"] == "opt-in"
    assert catalog["codeql"]["referenced_by_profiles"] == ()


def test_analyzer_availability_exposes_setup_and_version_policy(monkeypatch) -> None:
    monkeypatch.setattr(execmod, "which", lambda analyzer_id: None)

    rows = {entry["analyzer_id"]: entry for entry in execmod.analyzer_availability()}

    assert rows["ruff"]["setup_hint"]
    assert rows["ruff"]["version_policy"] == "aci-maintained-pin"
    assert rows["ruff"]["install_spec"] == "ruff==0.4.8"
    assert rows["codeql"]["execution_support_level"] == "execution-ready"
    assert rows["codeql"]["support_level"] == "opt-in"


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


def test_deep_security_analyzers_are_execution_ready() -> None:
    rows = {entry["analyzer_id"]: entry for entry in execmod.analyzer_availability()}
    assert rows["osv-scanner"]["execution_support_level"] == "execution-ready"
    assert rows["trivy"]["execution_support_level"] == "execution-ready"
    assert rows["gitleaks"]["execution_support_level"] == "execution-ready"
    assert rows["codeql"]["execution_support_level"] == "execution-ready"


def test_codeql_sarif_is_normalized_into_findings(tmp_path: Path) -> None:
    sarif = json.dumps({
        "runs": [{
            "tool": {"driver": {"rules": [
                {"id": "py/code-injection", "properties": {"tags": ["security", "external/cwe/cwe-094"]}},
            ]}},
            "results": [{
                "ruleId": "py/code-injection",
                "message": {"text": "This code execution depends on a user-provided value."},
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": "app.py"}, "region": {"startLine": 7}}}],
            }],
        }]
    })
    findings = execmod._codeql_findings(sarif, tmp_path, 0)
    assert len(findings) == 1
    assert findings[0].signal == "EXT_CODEQL"
    assert findings[0].ci_id == "CI-14"
    assert findings[0].target_file == "app.py"
    assert findings[0].line == 7
    assert findings[0].evidence_ref == "codeql:py/code-injection"


def test_codeql_empty_sarif_is_safe(tmp_path: Path) -> None:
    assert execmod._codeql_findings("", tmp_path, 0) == []
    assert execmod._codeql_findings("{}", tmp_path, 0) == []


def test_gitleaks_report_is_normalized_into_findings(tmp_path: Path) -> None:
    report = json.dumps([
        {"RuleID": "generic-api-key", "Description": "API key", "File": str(tmp_path / "config.py"),
         "StartLine": 7, "Secret": "AKIA...", "Match": "key = 'AKIA...'"},
    ])
    findings = execmod._gitleaks_findings(report, tmp_path, 0)
    assert len(findings) == 1
    assert findings[0].signal == "EXT_GITLEAKS"
    assert findings[0].ci_id == "CI-14"
    assert findings[0].target_file == "config.py"
    assert findings[0].line == 7
    assert findings[0].evidence_ref == "gitleaks:generic-api-key"


def test_gitleaks_empty_report_is_safe(tmp_path: Path) -> None:
    assert execmod._gitleaks_findings("", tmp_path, 0) == []
    assert execmod._gitleaks_findings("[]", tmp_path, 0) == []


def test_osv_scanner_output_is_normalized_into_findings(tmp_path: Path) -> None:
    stdout = json.dumps({
        "results": [{
            "source": {"path": str(tmp_path / "requirements.txt"), "type": "lockfile"},
            "packages": [{
                "package": {"name": "requests", "version": "2.19.0", "ecosystem": "PyPI"},
                "vulnerabilities": [{"id": "GHSA-x4qr-2fvf-3mr5", "summary": "CRLF injection"}],
            }],
        }]
    })
    findings = execmod._osv_scanner_findings(stdout, tmp_path, 0)
    assert len(findings) == 1
    assert findings[0].signal == "EXT_OSV_SCANNER"
    assert findings[0].ci_id == "CI-14"
    assert findings[0].target_file == "requirements.txt"
    assert findings[0].evidence_ref == "osv-scanner:GHSA-x4qr-2fvf-3mr5"


def test_trivy_output_is_normalized_into_findings(tmp_path: Path) -> None:
    stdout = json.dumps({
        "Results": [{
            "Target": str(tmp_path / "package-lock.json"),
            "Vulnerabilities": [{
                "VulnerabilityID": "CVE-2021-44228",
                "PkgName": "log4j", "InstalledVersion": "2.14.0",
                "Severity": "CRITICAL", "Title": "Remote code execution",
            }],
        }]
    })
    findings = execmod._trivy_findings(stdout, tmp_path, 0)
    assert len(findings) == 1
    assert findings[0].signal == "EXT_TRIVY"
    assert findings[0].severity == "high"
    assert findings[0].evidence_ref == "trivy:CVE-2021-44228"


def test_osv_scanner_empty_output_is_safe(tmp_path: Path) -> None:
    assert execmod._osv_scanner_findings("", tmp_path, 0) == []
    assert execmod._trivy_findings("{}", tmp_path, 0) == []


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


def test_mypy_command_uses_workspace_cache_and_python_sources(tmp_path: Path) -> None:
    (tmp_path / "workspace").mkdir()
    alpha = tmp_path / "alpha.py"
    beta = tmp_path / "pkg" / "beta.py"
    beta.parent.mkdir()
    command = execmod._mypy_command(tmp_path, [str(alpha), str(beta)])
    assert command == [
        "mypy",
        "--namespace-packages",
        "--explicit-package-bases",
        "--hide-error-context",
        "--no-color-output",
        "--show-column-numbers",
        "--no-error-summary",
        "--cache-dir",
        str(tmp_path / "workspace" / ".aci-mypy-cache"),
        str(alpha),
        str(beta),
    ]


def test_mypy_returns_no_applicable_source_when_no_py_files(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(execmod, "_readiness_for", lambda analyzer_id: execmod.AnalyzerReadiness(
        analyzer_id=analyzer_id,
        executable_path=f"C:/fake/{analyzer_id}.exe",
        availability_state="ready",
        version_text="mypy 1.0.0",
        version_ok=True,
        minimum_version="1.0.0",
    ))
    result = execmod.run_analyzer("mypy", tmp_path, 1)
    assert result.ok is False
    assert result.runtime_state == "no-applicable-source"


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


def test_semgrep_output_is_normalized_into_findings(tmp_path: Path) -> None:
    stdout = json.dumps(
        {
            "results": [
                {
                    "check_id": "aci.ci14.unsafe-yaml-load",
                    "path": str(tmp_path / "config.py"),
                    "start": {"line": 8},
                    "extra": {"message": "yaml.load without SafeLoader", "severity": "ERROR"},
                }
            ]
        }
    )
    findings = execmod._semgrep_findings(stdout, tmp_path, 40)
    assert len(findings) == 1
    assert findings[0].signal == "EXT_SEMGREP"
    assert findings[0].ci_id == "CI-14"
    assert findings[0].line == 8
    assert findings[0].severity == "high"
    assert findings[0].evidence_ref == "semgrep:aci.ci14.unsafe-yaml-load"


def test_semgrep_command_requires_supported_source_and_rules(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(cmdmod, "_semgrep_rule_path", lambda: tmp_path / "aci-semgrep-rules.yml")
    (tmp_path / "aci-semgrep-rules.yml").write_text("rules: []\n", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    command = cmdmod._semgrep_command(tmp_path)
    assert command == [
        "semgrep",
        "scan",
        "--config",
        str(tmp_path / "aci-semgrep-rules.yml"),
        "--json",
        "--quiet",
        "--disable-version-check",
        str(tmp_path),
    ]


def test_semgrep_command_returns_none_without_applicable_source(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(cmdmod, "_semgrep_rule_path", lambda: tmp_path / "aci-semgrep-rules.yml")
    (tmp_path / "aci-semgrep-rules.yml").write_text("rules: []\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("docs only\n", encoding="utf-8")
    assert cmdmod._semgrep_command(tmp_path) is None


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
