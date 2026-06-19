"""End-to-end proof that the external-analyzer lane runs real tools (P0-1).

The unit tests in test_aci_analyzer_execution.py mock subprocess and verify the
parsing/normalization logic. This file complements them by running the *real*
analyzer binary against a fixture and asserting a normalized finding is produced.

CI-07/CI-09/CI-13/CI-15 have no native detector — they depend entirely on this
lane — so a real end-to-end check guards against silent breakage of the lane
wiring (analyzer invocation -> output parse -> normalized finding).

Each test skips gracefully when the underlying analyzer binary is not installed,
so the suite stays green on minimal environments while still exercising the lane
in CI (where ruff is installed).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from aci.aci_scan import scan_target


def _scan_with_external(pack: Path) -> dict:
    return scan_target(pack, "full", "core-only", include_external_analyzers=True)


@pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff not installed")
def test_ruff_lane_produces_normalized_external_finding(tmp_path: Path) -> None:
    # Two unused imports -> ruff F401 -> CI-07 (Lava Flow), external-analyzer lane.
    (tmp_path / "bad.py").write_text(
        "import os\nimport sys\n\n\ndef f():\n    return 1\n", encoding="utf-8"
    )

    report = _scan_with_external(tmp_path)

    external = [f for f in report["findings"] if f.get("owner_lane") == "external-analyzer"]
    ci07 = [f for f in external if f.get("ci_id") == "CI-07"]
    assert ci07, f"expected a CI-07 external finding from ruff; got {external!r}"

    # Findings must carry the normalized contract fields, not raw tool output.
    sample = ci07[0]
    assert sample["target_file"].endswith("bad.py")
    assert isinstance(sample.get("line"), int) and sample["line"] >= 1
    assert sample.get("signal", "").startswith("EXT_")


@pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff not installed")
def test_external_lane_records_per_analyzer_runtime_state(tmp_path: Path) -> None:
    (tmp_path / "clean.py").write_text("def f():\n    return 1\n", encoding="utf-8")

    report = _scan_with_external(tmp_path)
    runs = {r["analyzer_id"]: r for r in report.get("external_analyzer_runs", [])}

    # ruff is wired into the lane (its actual execution + normalization is
    # asserted by test_ruff_lane_produces_normalized_external_finding).
    assert "ruff" in runs

    # Every analyzer run records a recognized runtime_state (never empty/garbage)
    # and never crashes the scan. This is the full valid set from
    # aci_analyzer_execution, including the transient failure states that can
    # legitimately occur under load (e.g. a flaky external tool invocation).
    valid_states = {
        "executed",
        "not-installed",
        "no-tests-collected",
        "no-applicable-source",
        "downstream-setup-required",
        "runtime-failure",
        "parse-failure",
        "spawn-failure",
        "timeout",
        "version-or-runtime-problem",
    }
    for run in runs.values():
        assert run["runtime_state"] in valid_states, run


def test_external_lane_off_yields_no_external_findings(tmp_path: Path) -> None:
    (tmp_path / "bad.py").write_text("import os\n\n\ndef f():\n    return 1\n", encoding="utf-8")

    report = scan_target(tmp_path, "full", "core-only", include_external_analyzers=False)
    external = [f for f in report["findings"] if f.get("owner_lane") == "external-analyzer"]
    assert external == [], f"external lane must be silent when disabled; got {external!r}"


@pytest.mark.skipif(shutil.which("semgrep") is None, reason="semgrep not installed")
def test_semgrep_lane_produces_multi_language_findings(tmp_path: Path) -> None:
    # The core general-purpose claim: a non-Python file is actually scanned and
    # normalized. semgrep's bundled baseline rules flag eval() in JavaScript.
    (tmp_path / "app.js").write_text("function run(code){\n  return eval(code);\n}\n", encoding="utf-8")
    (tmp_path / "svc.py").write_text("import pickle\n\n\ndef load(b):\n    return pickle.loads(b)\n", encoding="utf-8")

    report = _scan_with_external(tmp_path)

    runs = {r["analyzer_id"]: r for r in report.get("external_analyzer_runs", [])}
    assert runs.get("semgrep", {}).get("runtime_state") == "executed", f"semgrep did not run: {runs.get('semgrep')!r}"

    semgrep_findings = [f for f in report["findings"] if f.get("signal") == "EXT_SEMGREP"]
    js_findings = [f for f in semgrep_findings if f["target_file"].endswith("app.js")]
    assert js_findings, f"expected a semgrep finding in app.js (JavaScript); got {semgrep_findings!r}"
    assert js_findings[0].get("owner_lane") == "external-analyzer"
    assert js_findings[0].get("ci_id", "").startswith("CI-")


@pytest.mark.skipif(shutil.which("sqlfluff") is None, reason="sqlfluff not installed")
def test_sqlfluff_lane_runs_and_normalizes_sql_findings(tmp_path: Path) -> None:
    (tmp_path / "query.sql").write_text("SELECT a,b FROM mytable WHERE x=1\n", encoding="utf-8")

    report = _scan_with_external(tmp_path)

    runs = {r["analyzer_id"]: r for r in report.get("external_analyzer_runs", [])}
    # Regression guard: sqlfluff needs an explicit --dialect or it exits with a
    # user error (runtime-failure) instead of linting.
    assert runs.get("sqlfluff", {}).get("runtime_state") == "executed", f"sqlfluff did not run: {runs.get('sqlfluff')!r}"

    sql_findings = [f for f in report["findings"] if f.get("signal") == "EXT_SQLFLUFF"]
    assert sql_findings, "expected sqlfluff findings on query.sql"
    assert all(f.get("owner_lane") == "external-analyzer" for f in sql_findings)


@pytest.mark.skipif(shutil.which("gitleaks") is None, reason="gitleaks not installed")
def test_gitleaks_lane_detects_and_normalizes_secret(tmp_path: Path) -> None:
    # gitleaks is opt-in, so run the lane directly to prove the file-report
    # adapter works: command -> execute -> read JSON report -> normalized finding.
    from aci.aci_analyzer_execution import run_analyzer

    (tmp_path / "settings.py").write_text(
        'github_pat = "ghp_16C7e42F292c6912E7710c838347Ae178B4a"\n', encoding="utf-8"
    )
    result = run_analyzer("gitleaks", tmp_path, 0)

    assert result.runtime_state == "executed", f"gitleaks did not run cleanly: {result.stderr!r}"
    secrets = [f for f in result.findings if f.signal == "EXT_GITLEAKS"]
    assert secrets, "expected gitleaks to flag the committed GitHub token"
    assert secrets[0].ci_id == "CI-14"
    assert secrets[0].target_file.endswith("settings.py")


@pytest.mark.skipif(shutil.which("shellcheck") is None, reason="shellcheck not installed")
def test_shellcheck_lane_runs_and_normalizes_shell_findings(tmp_path: Path) -> None:
    from aci.aci_analyzer_execution import run_analyzer

    (tmp_path / "x.sh").write_text('#!/bin/sh\nfoo=1\necho "$bar"\nif [ $foo = 1 ]; then echo hi; fi\n', encoding="utf-8")
    result = run_analyzer("shellcheck", tmp_path, 0)

    assert result.runtime_state == "executed", f"shellcheck did not run: {result.stderr!r}"
    sh = [f for f in result.findings if f.signal == "EXT_SHELLCHECK"]
    assert sh, "expected shellcheck findings on x.sh"


@pytest.mark.skipif(shutil.which("trivy") is None, reason="trivy not installed")
def test_trivy_lane_runs_and_normalizes_dependency_findings(tmp_path: Path) -> None:
    from aci.aci_analyzer_execution import run_analyzer

    (tmp_path / "requirements.txt").write_text("requests==2.19.0\n", encoding="utf-8")
    result = run_analyzer("trivy", tmp_path, 0)

    assert result.runtime_state == "executed", f"trivy did not run: {result.stderr!r}"
    vulns = [f for f in result.findings if f.signal == "EXT_TRIVY"]
    assert vulns, "expected trivy to flag a known-vulnerable dependency"
    assert vulns[0].ci_id == "CI-14"


@pytest.mark.skipif(shutil.which("eslint") is None, reason="eslint not installed")
def test_eslint_lane_runs_with_bundled_config(tmp_path: Path) -> None:
    # eslint is profile-default; run the lane directly to prove it lints JS with
    # ACI's bundled flat config (eslint v9+ refuses a bare directory path).
    from aci.aci_analyzer_execution import run_analyzer

    (tmp_path / "app.js").write_text("var x = 1\nfunction f(){ return eval('1') }\n", encoding="utf-8")
    result = run_analyzer("eslint", tmp_path, 0)

    assert result.runtime_state == "executed", f"eslint did not run: {result.stderr!r}"
    js = [f for f in result.findings if f.signal == "EXT_ESLINT"]
    assert js, "expected eslint findings in app.js"
    assert any(f.ci_id == "CI-14" for f in js), "expected the no-eval finding mapped to CI-14"


@pytest.mark.skipif(shutil.which("tsc") is None, reason="tsc not installed")
def test_tsc_lane_treats_type_errors_as_findings(tmp_path: Path) -> None:
    from aci.aci_analyzer_execution import run_analyzer

    (tmp_path / "tsconfig.json").write_text('{"compilerOptions":{"strict":true,"noEmit":true}}\n', encoding="utf-8")
    (tmp_path / "a.ts").write_text("const x: number = 'str';\n", encoding="utf-8")
    result = run_analyzer("tsc", tmp_path, 0)

    # tsc exits 2 on type errors; the adapter must treat that as executed-with-findings.
    assert result.runtime_state == "executed", f"tsc did not run cleanly: exit={result.exit_code} {result.stderr!r}"
    ts = [f for f in result.findings if f.signal == "EXT_TSC"]
    assert ts, "expected tsc to report the type error as a finding"
