"""Report schema regression and gate behavior regression tests (T40).

report schema: scan output must always validate against the bounded contract.
gate regression: specific scenarios must produce stable, predictable gate decisions.

Security note: eval() appears in fixture strings written to temporary files.
It is NOT executed by this process — it is test input for ACI's CI-14 detector.
"""
from __future__ import annotations

from pathlib import Path

from aci.aci_automation import validate_report_payload, REQUIRED_SAMPLE_TOP_LEVEL_FIELDS
from aci.aci_findings import LANE_HUMAN_JUDGMENT
from aci.aci_scan import scan_target


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ── Report schema regression ───────────────────────────────────────────────


def test_schema_clean_scan_validates(tmp_path: Path) -> None:
    _write(tmp_path / "clean.py", "print('ok')\n")
    report = scan_target(tmp_path, "startup", "core-only", include_external_analyzers=False)
    result = validate_report_payload("report.json", report)
    assert result["ok"] is True, result


def test_schema_findings_scan_validates(tmp_path: Path) -> None:
    _write(tmp_path / "danger.py", "eval('1+1')\n")
    report = scan_target(tmp_path, "full", "core-only", include_external_analyzers=False)
    assert report["findings"]
    result = validate_report_payload("report.json", report)
    assert result["ok"] is True, result


def test_schema_operations_scan_validates(tmp_path: Path) -> None:
    _write(tmp_path / "sample.py", "# TODO: remove\n")
    _write(
        tmp_path / "ops.toml",
        "[baseline]\nentries = [{ci_id = \"CI-03\", target_file = \"sample.py\", line = 1}]\n",
    )
    report = scan_target(
        tmp_path, "full", "core-only", tmp_path / "ops.toml", include_external_analyzers=False
    )
    result = validate_report_payload("report.json", report)
    assert result["ok"] is True, result


def test_schema_all_top_level_fields_present(tmp_path: Path) -> None:
    _write(tmp_path / "clean.py", "x = 1\n")
    report = scan_target(tmp_path, "startup", "core-only", include_external_analyzers=False)
    for field in REQUIRED_SAMPLE_TOP_LEVEL_FIELDS:
        assert field in report, f"required field missing from scan output: {field}"


def test_schema_report_format_version_stable(tmp_path: Path) -> None:
    _write(tmp_path / "clean.py", "x = 1\n")
    report = scan_target(tmp_path, "startup", "core-only", include_external_analyzers=False)
    assert report["report_format_version"] == "1.0.0"


def test_schema_finding_rows_have_required_fields(tmp_path: Path) -> None:
    _write(tmp_path / "danger.py", "eval('1+1')\n")
    report = scan_target(tmp_path, "full", "core-only", include_external_analyzers=False)
    required = {
        "finding_id", "ci_id", "signal", "severity", "target_file",
        "fingerprint", "reason", "owner_lane", "verification_status",
    }
    for finding in report["findings"]:
        missing = required - finding.keys()
        assert not missing, f"finding {finding.get('finding_id')} missing fields: {missing}"


def test_schema_gate_fields_always_present(tmp_path: Path) -> None:
    _write(tmp_path / "clean.py", "x = 1\n")
    report = scan_target(tmp_path, "startup", "core-only", include_external_analyzers=False)
    gate = report["gate"]
    for field in ("decision", "blocking_severities", "blocking_count", "reasons", "reason_details"):
        assert field in gate, f"gate missing field: {field}"


def test_schema_summary_count_fields_are_non_negative(tmp_path: Path) -> None:
    _write(tmp_path / "sample.py", "# TODO: x\ntry:\n    pass\nexcept Exception:\n    pass\n")
    report = scan_target(tmp_path, "full", "core-only", include_external_analyzers=False)
    summary = report["summary"]
    for field in ("total_findings", "new_count", "existing_baseline_count", "waived_count", "suppressed_count"):
        assert isinstance(summary[field], int) and summary[field] >= 0, (
            f"summary.{field} must be a non-negative int, got {summary[field]!r}"
        )


# ── Gate regression ────────────────────────────────────────────────────────


def test_gate_passes_when_no_findings(tmp_path: Path) -> None:
    _write(tmp_path / "clean.py", "x = 1\n")
    report = scan_target(
        tmp_path, "startup", "core-only",
        severity_threshold="low",
        include_external_analyzers=False,
    )
    assert report["gate"]["decision"] == "pass"
    assert report["gate"]["reasons"] == []


def test_gate_fails_on_severity_threshold(tmp_path: Path) -> None:
    _write(tmp_path / "secrets.py", 'API_KEY = "SECRET12345"\n')
    report = scan_target(
        tmp_path, "full", "core-only",
        severity_threshold="critical",
        include_external_analyzers=False,
    )
    assert report["gate"]["decision"] == "fail"
    assert "severity-threshold" in report["gate"]["reasons"]


def test_gate_fails_on_new_findings_flag(tmp_path: Path) -> None:
    _write(tmp_path / "sample.py", "# TODO: track\n")
    report = scan_target(
        tmp_path, "full", "core-only",
        severity_threshold="critical",
        fail_on_new_findings=True,
        include_external_analyzers=False,
    )
    assert report["gate"]["decision"] == "fail"
    assert "new-findings-present" in report["gate"]["reasons"]


def test_gate_fails_on_unreviewed_review_required(tmp_path: Path) -> None:
    _write(tmp_path / "sample.py", "# TODO: review\n")
    report = scan_target(
        tmp_path, "full", "core-only",
        severity_threshold="critical",
        fail_on_unreviewed_review_required=True,
        include_external_analyzers=False,
    )
    # CI-03 (TODO marker) is always owner_lane=LANE_HUMAN_JUDGMENT; the fixture guarantees a hit
    human_judgment_findings = [
        f for f in report["findings"] if f["owner_lane"] == LANE_HUMAN_JUDGMENT
    ]
    assert human_judgment_findings, "CI-03 TODO fixture must produce at least one human-judgment finding"
    assert report["gate"]["decision"] == "fail"
    assert "unreviewed-review-required" in report["gate"]["reasons"]


def test_gate_passes_when_all_findings_waived(tmp_path: Path) -> None:
    _write(tmp_path / "sample.py", "# TODO: tracked\n")
    _write(
        tmp_path / "ops.toml",
        "\n".join([
            "[waiver]",
            'entries = [{waiver_id = "W1", ci_id = "CI-03", target_file = "sample.py", line = 1}]',
        ]),
    )
    report = scan_target(
        tmp_path, "full", "core-only",
        tmp_path / "ops.toml",
        severity_threshold="critical",
        fail_on_new_findings=True,
        include_external_analyzers=False,
    )
    assert report["gate"]["decision"] == "pass"


def test_gate_reason_details_include_finding_ids(tmp_path: Path) -> None:
    _write(tmp_path / "secrets.py", 'API_KEY = "SECRET12345"\n')
    report = scan_target(
        tmp_path, "full", "core-only",
        severity_threshold="critical",
        include_external_analyzers=False,
    )
    detail_map = {d["reason"]: d for d in report["gate"]["reason_details"]}
    assert "severity-threshold" in detail_map
    assert detail_map["severity-threshold"]["finding_ids"]


def test_gate_unreviewed_count_in_output(tmp_path: Path) -> None:
    _write(tmp_path / "clean.py", "x = 1\n")
    report = scan_target(tmp_path, "startup", "core-only", include_external_analyzers=False)
    assert "unreviewed_review_required_count" in report["gate"]
    assert isinstance(report["gate"]["unreviewed_review_required_count"], int)


def test_gate_resolved_baseline_count_in_summary(tmp_path: Path) -> None:
    _write(tmp_path / "clean.py", "x = 1\n")
    _write(
        tmp_path / "ops.toml",
        "[baseline]\nentries = [{ci_id = \"CI-03\", target_file = \"clean.py\", line = 1}]\n",
    )
    report = scan_target(
        tmp_path, "full", "core-only", tmp_path / "ops.toml", include_external_analyzers=False
    )
    assert report["summary"]["resolved_baseline_count"] == 1
    assert len(report["resolved_baseline_entries"]) == 1
    assert report["resolved_baseline_entries"][0]["lifecycle_state"] == "resolved"
