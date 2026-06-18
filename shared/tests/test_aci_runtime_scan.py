from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import aci.aci_analyzer_execution as execmod
from aci.aci_github_summary import build_github_summary_markdown
import aci.aci_scan as scanmod
from aci.aci_automation import validate_report_payload
from aci.aci_config import load_cli_config
from aci.aci_domain_contract import CORE_ONLY_DOMAIN_ID
from aci.aci_findings import build_finding, LANE_EXTERNAL_ANALYZER, VERIFICATION_EXECUTED
from aci.aci_profiles import PROFILE_QUICK_GATE
from aci.aci_sarif import build_sarif_report, validate_sarif_report
from aci.aci_scan import scan_target
from shared.tests._aci_test_helpers import (
    clean_startup_report,
    insecure_http_fixture_line,
    write_fixture as _write,
)


def test_scan_applies_operations_and_gate_controls(tmp_path: Path) -> None:
    _write(
        tmp_path / "sample.py",
        "# TODO: track this\ntry:\n    pass\nexcept Exception:\n    pass\n",
    )
    _write(
        tmp_path / "operations.toml",
        "\n".join(
            [
                "[baseline]",
                'entries = [{ ci_id = "CI-03", target_file = "sample.py", line = 1 }]',
                "",
                "[waiver]",
                'entries = [{ waiver_id = "W1", ci_id = "CI-21", target_file = "sample.py", line = 4 }]',
            ]
        ),
    )

    report = scan_target(
        tmp_path,
        "full",
        "core-only",
        tmp_path / "operations.toml",
        severity_threshold="critical",
        fail_on_new_findings=True,
        include_external_analyzers=False,
    )

    assert report["summary"]["existing_baseline_count"] == 1
    assert report["summary"]["waived_count"] == 1
    assert report["gate"]["decision"] == "pass"  # all new findings are waived; nothing unacknowledged remains


def test_scan_report_validates_when_empty(tmp_path: Path) -> None:
    _write(tmp_path / "clean.py", "print('ok')\n")
    report = scan_target(
        tmp_path,
        "startup",
        "core-only",
        include_external_analyzers=False,
    )

    result = validate_report_payload("report.json", report)
    assert result["ok"] is True


def test_scan_skipped_targets_are_reported(tmp_path: Path) -> None:
    _write(tmp_path / "large.txt", "A" * 1_000_001)
    _write(tmp_path / "artifact.bin", "placeholder")

    report = scan_target(
        tmp_path,
        "startup",
        "core-only",
        include_external_analyzers=False,
    )

    skipped = {item["path"]: item["reason"] for item in report["skipped_targets"]}
    assert skipped["large.txt"] == "max-file-size-exceeded"
    assert skipped["artifact.bin"] == "unsupported-suffix"


def test_gate_can_fail_on_analyzer_errors(tmp_path: Path, monkeypatch) -> None:
    # Force every analyzer to report not-installed so the scan deterministically
    # produces analyzer failures, regardless of which binaries the environment
    # has (CI installs them; local dev may not).
    import aci.aci_analyzer_execution as execmod

    monkeypatch.setattr(execmod, "_readiness_for", lambda analyzer_id: execmod.AnalyzerReadiness(
        analyzer_id=analyzer_id,
        executable_path=None,
        availability_state="not-installed",
        version_text=None,
        version_ok=False,
        minimum_version=None,
    ))
    _write(tmp_path / "clean.py", "print('ok')\n")
    report = scan_target(
        tmp_path,
        PROFILE_QUICK_GATE,
        CORE_ONLY_DOMAIN_ID,
        severity_threshold="critical",
        fail_on_analyzer_errors=True,
    )

    assert report["gate"]["decision"] == "fail"
    assert "analyzer-runtime-error" in report["gate"]["reasons"]


def test_sarif_emission_contains_results(tmp_path: Path) -> None:
    _write(tmp_path / "danger.py", "eval('1+1')\n")
    report = scan_target(
        tmp_path,
        "full",
        "core-only",
        include_external_analyzers=False,
    )

    sarif = build_sarif_report(report)
    results = sarif["runs"][0]["results"]
    assert sarif["version"] == "2.1.0"
    assert results
    assert results[0]["ruleId"] == "CI14_DYNAMIC_CODE_EXECUTION"
    validation = validate_sarif_report(sarif)
    assert validation["ok"] is True


def test_ignore_file_excludes_targets(tmp_path: Path) -> None:
    _write(tmp_path / ".aciignore", "danger.py\n")
    _write(tmp_path / "danger.py", "eval('1+1')\n")
    _write(tmp_path / "sample.py", "print('ok')\n")

    report = scan_target(
        tmp_path,
        "startup",
        "core-only",
        include_external_analyzers=False,
    )

    target_files = [item["target_file"] for item in report["findings"]]
    assert "danger.py" not in target_files
    assert report["scope_rules"]["ignore_patterns"] == ["danger.py"]


def test_secrets_and_http_detectors_emit_findings(tmp_path: Path) -> None:
    _write(
        tmp_path / "secrets.py",
        'API_KEY = "SECRET12345"\n' + insecure_http_fixture_line(),
    )

    report = scan_target(
        tmp_path,
        "full",
        "core-only",
        include_external_analyzers=False,
    )

    signals = {item["signal"] for item in report["findings"]}
    assert "CI14_PLAINTEXT_SECRET" in signals
    assert "CI14_INSECURE_HTTP" in signals


def test_blockers_and_residuals_are_materialized(tmp_path: Path) -> None:
    _write(
        tmp_path / "sample.py",
        "# TODO: tracked work\ntry:\n    pass\nexcept Exception:\n    pass\n",
    )
    _write(
        tmp_path / "operations.toml",
        "\n".join(
            [
                "[waiver]",
                'entries = [{ waiver_id = "W1", ci_id = "CI-21", target_file = "sample.py", line = 4 }]',
            ]
        ),
    )
    _write(tmp_path / "secrets.py", 'API_KEY = "SECRET12345"\n')

    report = scan_target(
        tmp_path,
        "full",
        "core-only",
        tmp_path / "operations.toml",
        severity_threshold="critical",
        include_external_analyzers=False,
    )

    assert report["blockers"]
    assert report["blockers"][0]["signal"] == "CI14_PLAINTEXT_SECRET"
    assert report["residuals"]
    assert report["residuals"][0]["classification"] == "accepted-risk"


def test_generated_paths_are_skipped(tmp_path: Path) -> None:
    _write(tmp_path / ".pytest_cache" / "README.md", "generated cache\n")
    _write(tmp_path / "sample.py", "print('ok')\n")

    report = scan_target(
        tmp_path,
        "startup",
        "core-only",
        include_external_analyzers=False,
    )

    skipped = {item["path"]: item["reason"] for item in report["skipped_targets"]}
    assert skipped[".pytest_cache/README.md"] == "generated-path-skipped"
    assert report["scope_rules"]["skip_generated_paths"] is True


def test_source_only_scope_excludes_docs_examples_and_tests(tmp_path: Path) -> None:
    _write(tmp_path / "src" / "main.py", "# TODO: runtime\n")
    _write(tmp_path / "docs" / "note.py", "# TODO: docs\n")
    _write(tmp_path / "examples" / "fixture.py", "# TODO: fixture\n")
    _write(tmp_path / "tests" / "test_sample.py", "# TODO: test\n")

    report = scan_target(
        tmp_path,
        "full",
        "core-only",
        include_external_analyzers=False,
        scope_mode="source-only",
    )

    target_files = {item["target_file"] for item in report["findings"]}
    assert "src/main.py" in target_files
    assert "docs/note.py" not in target_files
    assert "examples/fixture.py" not in target_files
    assert "tests/test_sample.py" not in target_files
    assert report["scope_rules"]["scope_mode"] == "source-only"
    assert report["scope_rules"]["gate_scope_classes"] == ["runtime-source"]


def test_full_repo_reports_fixture_findings_without_blocking_gate(tmp_path: Path) -> None:
    _write(tmp_path / "examples" / "danger.py", 'API_KEY = "SECRET12345"\n')

    report = scan_target(
        tmp_path,
        "full",
        "core-only",
        severity_threshold="critical",
        include_external_analyzers=False,
        scope_mode="full-repo",
    )

    fixtures = [f for f in report["findings"] if f["target_file"] == "examples/danger.py"]
    assert fixtures
    assert all(f["scope_class"] == "fixtures" for f in fixtures)
    assert report["gate"]["decision"] == "pass"
    assert report["blockers"] == []
    assert report["summary"]["blocker_count"] == 0


def test_insecure_http_support_noise_is_suppressed_outside_runtime_and_fixtures(tmp_path: Path) -> None:
    _write(tmp_path / "shared" / "python" / "runtime.py", 'URL = "http://api.acme-corp.com/v1"\n')
    _write(tmp_path / "docs" / "roadmap" / "evidence.md", "See `http://api.acme-corp.com/v1`\n")
    _write(tmp_path / "shared" / "tests" / "test_fixture.py", 'URL = "http://api.acme-corp.com/v1"\n')
    _write(tmp_path / "shared" / "tools" / "aci_recall_probe.py", 'URL = "http://api.acme-corp.com/v1"\n')
    _write(tmp_path / "examples" / "fixture.py", 'URL = "http://api.acme-corp.com/v1"\n')

    report = scan_target(
        tmp_path,
        "full",
        "core-only",
        include_external_analyzers=False,
        scope_mode="full-repo",
    )

    http_targets = {
        item["target_file"]
        for item in report["findings"]
        if item["signal"] == "CI14_INSECURE_HTTP"
    }
    assert "shared/python/runtime.py" in http_targets
    assert "examples/fixture.py" in http_targets
    assert "docs/roadmap/evidence.md" not in http_targets
    assert "shared/tests/test_fixture.py" not in http_targets
    assert "shared/tools/aci_recall_probe.py" not in http_targets


def test_full_repo_external_lane_ignores_fixture_only_findings(tmp_path: Path, monkeypatch) -> None:
    _write(tmp_path / "src" / "main.py", "x = 1\n")
    _write(tmp_path / "examples" / "fixture.py", "y = 2\n")

    def _fake_run_analyzer(analyzer_id: str, target_root: Path, next_id: int) -> execmod.AnalyzerRunResult:
        runtime = build_finding(
            finding_id=f"F-EXT-{next_id:04d}",
            ci_id="CI-07",
            signal="EXT_RUFF",
            severity="medium",
            target_file="src/main.py",
            reason="runtime finding",
            evidence_ref="ruff",
            line=1,
            owner_lane=LANE_EXTERNAL_ANALYZER,
            verification_status=VERIFICATION_EXECUTED,
        )
        fixture = build_finding(
            finding_id=f"F-EXT-{next_id + 1:04d}",
            ci_id="CI-07",
            signal="EXT_RUFF",
            severity="medium",
            target_file="examples/fixture.py",
            reason="fixture finding",
            evidence_ref="ruff",
            line=1,
            owner_lane=LANE_EXTERNAL_ANALYZER,
            verification_status=VERIFICATION_EXECUTED,
        )
        return execmod.AnalyzerRunResult(
            analyzer_id=analyzer_id,
            ok=True,
            exit_code=0,
            runtime_state="executed",
            stdout="",
            stderr="",
            findings=(runtime, fixture),
        )

    monkeypatch.setattr(scanmod, "run_analyzer", _fake_run_analyzer)

    report = scan_target(
        tmp_path,
        "quick-gate",
        "core-only",
        include_external_analyzers=True,
        scope_mode="full-repo",
    )

    findings = {(item["target_file"], item["owner_lane"]) for item in report["findings"]}
    assert ("src/main.py", LANE_EXTERNAL_ANALYZER) in findings
    assert ("examples/fixture.py", LANE_EXTERNAL_ANALYZER) not in findings


def test_dogfood_scope_focuses_common_source_and_tests(tmp_path: Path) -> None:
    _write(tmp_path / "shared" / "python" / "tool.py", "# TODO: runtime\n")
    _write(tmp_path / "shared" / "tests" / "test_tool.py", "# TODO: test\n")
    _write(tmp_path / "docs" / "proof.py", "# TODO: docs\n")
    _write(tmp_path / "examples" / "fixture.py", "# TODO: fixture\n")

    report = scan_target(
        tmp_path,
        "full",
        "core-only",
        include_external_analyzers=False,
        scope_mode="dogfood",
    )

    target_files = {item["target_file"] for item in report["findings"]}
    assert "shared/python/tool.py" in target_files
    assert "shared/tests/test_tool.py" in target_files
    assert "docs/proof.py" not in target_files
    assert "examples/fixture.py" not in target_files


def test_cli_config_loads_scan_gate_defaults(tmp_path: Path) -> None:
    _write(
        tmp_path / "aci.toml",
        "\n".join(
            [
                "[aci]",
                'severity_threshold = "critical"',
                "fail_on_new_findings = true",
                "fail_on_analyzer_errors = true",
            ]
        ),
    )

    cfg = load_cli_config(tmp_path / "aci.toml")
    assert cfg.severity_threshold == "critical"
    assert cfg.fail_on_new_findings is True
    assert cfg.fail_on_analyzer_errors is True


def test_gate_reason_details_list_triggering_findings(tmp_path: Path) -> None:
    _write(tmp_path / "secrets.py", 'API_KEY = "SECRET12345"\n')

    report = scan_target(
        tmp_path,
        "full",
        "core-only",
        severity_threshold="critical",
        fail_on_new_findings=True,
        include_external_analyzers=False,
    )

    reason_details = {item["reason"]: item for item in report["gate"]["reason_details"]}
    assert "severity-threshold" in reason_details
    assert "new-findings-present" in reason_details
    assert reason_details["severity-threshold"]["finding_ids"]


def test_report_contains_tool_version(tmp_path: Path) -> None:
    report = clean_startup_report(tmp_path)

    assert report["tool_version"] == "0.1.7"


def test_report_includes_review_brief_and_github_summary(tmp_path: Path) -> None:
    _write(tmp_path / "danger.py", "eval('1+1')\n")
    report = scan_target(tmp_path, "full", "core-only", include_external_analyzers=False)
    brief = report["review_brief"]
    assert brief["gate_decision"] == report["gate"]["decision"]
    assert brief["top_files"]
    summary = build_github_summary_markdown(report)
    assert "ACI Review Summary" in summary
    assert "Hottest Files" in summary


def test_full_profile_runs_applicable_polyglot_analyzers(tmp_path: Path, monkeypatch) -> None:
    _write(tmp_path / "index.js", "var x = 1;\n")
    _write(tmp_path / "types.ts", "const y: any = 1;\n")
    _write(tmp_path / "tsconfig.json", '{"compilerOptions": {"noEmit": true}}\n')
    _write(tmp_path / "run.sh", 'echo "$HOME"\n')
    _write(tmp_path / "query.sql", "select  *  from t;\n")
    _write(tmp_path / "Dockerfile", "FROM python:3.12\nRUN chmod 777 /tmp\n")
    _write(tmp_path / "main.tf", 'resource "null_resource" "x" {}\n')

    calls: list[str] = []

    def _fake_run_analyzer(analyzer_id: str, target_root: Path, next_id: int) -> execmod.AnalyzerRunResult:
        calls.append(analyzer_id)
        return execmod.AnalyzerRunResult(
            analyzer_id=analyzer_id,
            ok=True,
            exit_code=0,
            runtime_state="executed",
            stdout="",
            stderr="",
            findings=(),
        )

    monkeypatch.setattr(scanmod, "run_analyzer", _fake_run_analyzer)

    report = scan_target(
        tmp_path,
        "full",
        "core-only",
        include_external_analyzers=True,
    )

    assert calls == ["semgrep", "eslint", "tsc", "shellcheck", "sqlfluff"]
    skipped = {item["path"]: item["reason"] for item in report["skipped_targets"]}
    assert "index.js" not in skipped
    assert "types.ts" not in skipped
    assert "run.sh" not in skipped
    assert "query.sql" not in skipped
    assert "Dockerfile" not in skipped
    assert "main.tf" not in skipped


def test_self_audit_profile_runs_its_default_python_analyzers(tmp_path: Path, monkeypatch) -> None:
    _write(tmp_path / "shared" / "python" / "main.py", "print('ok')\n")
    _write(tmp_path / "shared" / "tests" / "test_main.py", "def test_ok():\n    assert True\n")

    calls: list[str] = []

    def _fake_run_analyzer(analyzer_id: str, target_root: Path, next_id: int) -> execmod.AnalyzerRunResult:
        calls.append(analyzer_id)
        return execmod.AnalyzerRunResult(
            analyzer_id=analyzer_id,
            ok=True,
            exit_code=0,
            runtime_state="executed",
            stdout="",
            stderr="",
            findings=(),
        )

    monkeypatch.setattr(scanmod, "run_analyzer", _fake_run_analyzer)

    scan_target(
        tmp_path,
        "self-audit",
        "core-only",
        include_external_analyzers=True,
        scope_mode="self-audit",
    )

    assert calls == ["ruff", "pyflakes", "mypy", "pytest", "semgrep"]


def test_ruff_ready_suppresses_overlapping_native_signals(tmp_path: Path, monkeypatch) -> None:
    _write(tmp_path / "todo.py", "# TODO: remove this\n")
    _write(tmp_path / "params.py", "def process(name, value, kind, source, target, limit):\n    return None\n")
    _write(
        tmp_path / "exceptions.py",
        "try:\n    pass\nexcept Exception:\n    pass\n",
    )
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
    long_lines = ["def process(n):"]
    for i in range(15):
        long_lines.append(f"    if n == {i}:")
        long_lines.append(f"        x = {i}")
    long_lines += ["    y = 1" for _ in range(55)]
    _write(tmp_path / "long.py", "\n".join(long_lines))

    monkeypatch.setattr(scanmod, "_readiness_for", lambda analyzer_id: execmod.AnalyzerReadiness(
        analyzer_id=analyzer_id,
        executable_path="C:/fake/ruff.exe",
        availability_state="ready",
        version_text="ruff 0.4.8",
        version_ok=True,
        minimum_version="0.4.8",
    ))
    monkeypatch.setattr(scanmod, "run_analyzer", lambda analyzer_id, target_root, next_id: execmod.AnalyzerRunResult(
        analyzer_id=analyzer_id,
        ok=True,
        exit_code=0,
        runtime_state="executed",
        stdout="",
        stderr="",
        findings=(),
    ))

    report = scan_target(
        tmp_path,
        PROFILE_QUICK_GATE,
        CORE_ONLY_DOMAIN_ID,
        include_external_analyzers=True,
    )

    signals = {item["signal"] for item in report["findings"]}
    assert "CI03_TODO_HACK" not in signals
    assert "CI18_PARAMETER_CLUSTER" not in signals
    assert "CI21_BROAD_EXCEPTION_SWALLOW" not in signals
    assert "CI26_RACE_HAZARD" not in signals
    assert "CI02_LONG_FUNCTION" not in signals


def test_ruff_unavailable_keeps_overlapping_native_signals(tmp_path: Path, monkeypatch) -> None:
    _write(tmp_path / "todo.py", "# TODO: remove this\n")
    _write(tmp_path / "params.py", "def process(name, value, kind, source, target, limit):\n    return None\n")
    _write(
        tmp_path / "exceptions.py",
        "try:\n    pass\nexcept Exception:\n    pass\n",
    )
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
    long_lines = ["def process(n):"]
    for i in range(15):
        long_lines.append(f"    if n == {i}:")
        long_lines.append(f"        x = {i}")
    long_lines += ["    y = 1" for _ in range(55)]
    _write(tmp_path / "long.py", "\n".join(long_lines))

    monkeypatch.setattr(scanmod, "_readiness_for", lambda analyzer_id: execmod.AnalyzerReadiness(
        analyzer_id=analyzer_id,
        executable_path=None,
        availability_state="not-installed",
        version_text=None,
        version_ok=False,
        minimum_version="0.4.8",
    ))
    monkeypatch.setattr(scanmod, "run_analyzer", lambda analyzer_id, target_root, next_id: execmod.AnalyzerRunResult(
        analyzer_id=analyzer_id,
        ok=False,
        exit_code=127,
        runtime_state="not-installed",
        stdout="",
        stderr="missing",
        findings=(),
    ))

    report = scan_target(
        tmp_path,
        PROFILE_QUICK_GATE,
        CORE_ONLY_DOMAIN_ID,
        include_external_analyzers=True,
    )

    signals = {item["signal"] for item in report["findings"]}
    assert "CI03_TODO_HACK" in signals
    assert "CI18_PARAMETER_CLUSTER" in signals
    assert "CI21_BROAD_EXCEPTION_SWALLOW" in signals
    assert "CI26_RACE_HAZARD" in signals
    assert "CI02_LONG_FUNCTION" in signals


# ── diff-from tests ────────────────────────────────────────────────────────

def test_diff_from_limits_scan_to_changed_files(tmp_path: Path) -> None:
    # changed.py triggers CI-21; unchanged.py would too, but should be filtered out
    _write(tmp_path / "changed.py", "def f():\n    try:\n        pass\n    except Exception:\n        pass\n")
    _write(tmp_path / "unchanged.py", "def g():\n    try:\n        pass\n    except Exception:\n        pass\n")

    with patch("aci.aci_scan._git_changed_files", return_value=frozenset(["changed.py"])) as mock_git:
        report = scan_target(
            tmp_path, "full", "core-only",
            include_external_analyzers=False,
            diff_from="HEAD~1",
        )
        mock_git.assert_called_once_with(tmp_path.resolve(), "HEAD~1")

    file_targets = {item["target_file"] for item in report["findings"]}
    assert all("changed" in t for t in file_targets), f"unexpected targets: {file_targets}"
    assert not any("unchanged" in t for t in file_targets), "unchanged.py leaked into findings"


def test_diff_from_recorded_in_scope_rules(tmp_path: Path) -> None:
    _write(tmp_path / "a.py", "x = 1\n")

    with patch("aci.aci_scan._git_changed_files", return_value=frozenset(["a.py"])):
        report = scan_target(
            tmp_path, "full", "core-only",
            include_external_analyzers=False,
            diff_from="origin/main",
        )

    assert report["scope_rules"]["diff_from"] == "origin/main"


def test_diff_from_none_scope_rules_is_null(tmp_path: Path) -> None:
    _write(tmp_path / "a.py", "x = 1\n")
    report = scan_target(
        tmp_path, "full", "core-only",
        include_external_analyzers=False,
    )
    assert report["scope_rules"]["diff_from"] is None


def test_diff_from_invalid_ref_raises_value_error(tmp_path: Path) -> None:
    _write(tmp_path / "a.py", "x = 1\n")
    mock_result = subprocess.CompletedProcess(
        args=["git", "diff", "--name-only", "no-such-ref", "--"],
        returncode=128,
        stdout="",
        stderr="fatal: bad revision 'no-such-ref'",
    )
    with patch("aci.aci_scan.subprocess.run", return_value=mock_result):
        try:
            scan_target(
                tmp_path, "full", "core-only",
                include_external_analyzers=False,
                diff_from="no-such-ref",
            )
            assert False, "expected ValueError"
        except ValueError as exc:
            assert "no-such-ref" in str(exc)


# ── suppression tests ──────────────────────────────────────────────────────

def test_suppression_by_signal_removes_finding(tmp_path: Path) -> None:
    _write(tmp_path / "sample.py", "# TODO: known tech debt\n")
    _write(
        tmp_path / "operations.toml",
        "\n".join([
            "[suppression]",
            'entries = [{ suppression_id = "S1", match = "CI03_TODO_HACK", reason = "intentional tech debt" }]',
        ]),
    )

    report = scan_target(
        tmp_path, "full", "core-only",
        tmp_path / "operations.toml",
        include_external_analyzers=False,
    )

    signals = {f["signal"] for f in report["findings"]}
    assert "CI03_TODO_HACK" not in signals
    assert report["summary"]["suppressed_count"] >= 1


def test_suppression_by_target_file_removes_finding(tmp_path: Path) -> None:
    _write(tmp_path / "noise.py", "# TODO: generated file marker\n")
    _write(tmp_path / "real.py", "# TODO: track this\n")
    _write(
        tmp_path / "operations.toml",
        "\n".join([
            "[suppression]",
            'entries = [{ suppression_id = "S1", match = "noise.py", reason = "generated file" }]',
        ]),
    )

    report = scan_target(
        tmp_path, "full", "core-only",
        tmp_path / "operations.toml",
        include_external_analyzers=False,
    )

    target_files = {f["target_file"] for f in report["findings"]}
    assert "noise.py" not in target_files
    assert "real.py" in target_files
    assert report["summary"]["suppressed_count"] >= 1


def test_suppression_count_in_summary(tmp_path: Path) -> None:
    _write(tmp_path / "a.py", "# TODO: first\n")
    _write(tmp_path / "b.py", "# TODO: second\n")
    _write(
        tmp_path / "operations.toml",
        "\n".join([
            "[suppression]",
            'entries = [{ suppression_id = "S1", match = "CI03_TODO_HACK" }]',
        ]),
    )

    report = scan_target(
        tmp_path, "full", "core-only",
        tmp_path / "operations.toml",
        include_external_analyzers=False,
    )

    assert report["summary"]["suppressed_count"] >= 2
    signals = {f["signal"] for f in report["findings"]}
    assert "CI03_TODO_HACK" not in signals
