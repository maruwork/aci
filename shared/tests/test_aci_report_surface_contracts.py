from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from aci.aci_cli import _handle_report_command
from aci.aci_github_summary import build_github_summary_markdown


def _sample_report() -> dict[str, object]:
    return {
        "command": "scan",
        "gate": {"decision": "fail"},
        "summary": {"total_findings": 3, "blocker_count": 1, "by_scope_policy": {"gated": 1, "advisory": 2}},
        "review_brief": {
            "scope_mode": "self-audit",
            "blocker_headline": "1 blocking finding needs owner action.",
            "advisory_headline": "2 advisory-only findings sit outside the gate in docs-evidence, fixtures.",
            "top_files": [{"name": "src/app.py", "count": 2}],
            "top_signals": [{"name": "CI21_BROAD_EXCEPTION_SWALLOW", "count": 1}],
            "advisory_scope_classes": [{"name": "docs-evidence", "count": 1}, {"name": "fixtures", "count": 1}],
            "analyzer_failures": [{"analyzer_id": "ruff", "runtime_state": "runtime-failure"}],
            "analyzer_availability_notes": [{"analyzer_id": "codeql", "runtime_state": "downstream-setup-required"}],
        },
        "findings": [
            {
                "ci_id": "CI-21",
                "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
                "severity": "high",
                "confidence": "medium",
                "target_file": "src/app.py",
                "line": 7,
                "reason": "broad except, tighten error routing",
                "fingerprint": "fp-1",
                "owner_lane": "native-static",
                "scope_class": "runtime-source",
            },
            {
                "ci_id": "CI-03",
                "signal": "CI03_TODO_HACK",
                "severity": "low",
                "confidence": "low",
                "target_file": "docs/note.py",
                "line": 3,
                "reason": "TODO line 1%2C line 2",
                "fingerprint": "fp-2",
                "owner_lane": "human-judgment",
                "scope_class": "docs-evidence",
            },
            {
                "ci_id": "CI-14",
                "signal": "CI14_PLAINTEXT_SECRET",
                "severity": "high",
                "confidence": "high",
                "target_file": "examples/fixture.py",
                "line": 5,
                "reason": "hardcoded secret in replay fixture",
                "fingerprint": "fp-3",
                "owner_lane": "native-static",
                "scope_class": "fixtures",
            },
        ],
        "scope_rules": {"scope_mode": "self-audit", "gate_scope_classes": ["runtime-source"]},
    }


def _write_report(tmp_path: Path) -> Path:
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_sample_report()), encoding="utf-8")
    return report_path


def test_emit_github_summary_cli_matches_golden_output(tmp_path: Path, capsys) -> None:
    report_path = _write_report(tmp_path)

    result = _handle_report_command(
        SimpleNamespace(command="emit-github-summary", report=report_path, report_scope_class=[], report_owner_lane=[])
    )

    assert result == 0
    assert capsys.readouterr().out == (
        "## ACI Review Summary\n"
        "\n"
        "- Gate: `fail`\n"
        "- Findings: `3`\n"
        "- Blockers: `1`\n"
        "- Visible view: `3` of `3` finding(s)\n"
        "- Scope mode: `self-audit`\n"
        "\n"
        "1 blocking finding needs owner action.\n"
        "\n"
        "Advisory-only findings outside the gate: `2`\n"
        "\n"
        "2 advisory-only findings sit outside the gate in docs-evidence, fixtures.\n"
        "\n"
        "### Hottest Files\n"
        "\n"
        "- `src/app.py`: 1 finding(s)\n"
        "- `docs/note.py`: 1 finding(s)\n"
        "- `examples/fixture.py`: 1 finding(s)\n"
        "\n"
        "### Top Signals\n"
        "\n"
        "- `CI21_BROAD_EXCEPTION_SWALLOW`: 1\n"
        "- `CI03_TODO_HACK`: 1\n"
        "- `CI14_PLAINTEXT_SECRET`: 1\n"
        "\n"
        "### Advisory Scope Classes\n"
        "\n"
        "- `docs-evidence`: 1\n"
        "- `fixtures`: 1\n"
        "\n"
        "### Analyzer Failures\n"
        "\n"
        "- `ruff`: `runtime-failure`\n"
        "\n"
        "### Analyzer Availability Notes\n"
        "\n"
        "- `codeql`: `downstream-setup-required`\n"
    )


def test_emit_annotations_cli_matches_golden_output(tmp_path: Path, capsys) -> None:
    report_path = _write_report(tmp_path)

    result = _handle_report_command(
        SimpleNamespace(command="emit-annotations", report=report_path, report_scope_class=[], report_owner_lane=[])
    )

    assert result == 0
    assert capsys.readouterr().out.splitlines() == [
        "::error file=src/app.py,line=7,title=CI-21 CI21_BROAD_EXCEPTION_SWALLOW::broad except, tighten error routing",
        "::notice file=docs/note.py,line=3,title=CI-03 CI03_TODO_HACK::advisory-only (docs-evidence): TODO line 1%252C line 2",
        "::notice file=examples/fixture.py,line=5,title=CI-14 CI14_PLAINTEXT_SECRET::advisory-only (fixtures): hardcoded secret in replay fixture",
    ]


def test_emit_sarif_cli_matches_golden_shape(tmp_path: Path, capsys) -> None:
    report_path = _write_report(tmp_path)

    result = _handle_report_command(
        SimpleNamespace(command="emit-sarif", report=report_path, report_scope_class=[], report_owner_lane=[])
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["version"] == "2.1.0"
    assert payload["runs"][0]["tool"]["driver"]["name"] == "ACI"
    assert payload["runs"][0]["tool"]["driver"]["rules"] == [
        {
            "id": "CI21_BROAD_EXCEPTION_SWALLOW",
            "name": "CI-21",
            "shortDescription": {"text": "broad except, tighten error routing"},
            "properties": {"precision": "medium", "problem.severity": "high"},
        },
        {
            "id": "CI03_TODO_HACK",
            "name": "CI-03",
            "shortDescription": {"text": "TODO line 1%2C line 2"},
            "properties": {"precision": "low", "problem.severity": "low"},
        },
        {
            "id": "CI14_PLAINTEXT_SECRET",
            "name": "CI-14",
            "shortDescription": {"text": "hardcoded secret in replay fixture"},
            "properties": {"precision": "high", "problem.severity": "high"},
        },
    ]
    results = payload["runs"][0]["results"]
    assert results[0]["level"] == "error"
    assert results[1]["level"] == "note"
    assert results[1]["message"]["text"] == "Advisory-only (docs-evidence): TODO line 1%2C line 2"
    assert results[1]["properties"] == {
        "aci.scope_class": "docs-evidence",
        "aci.scope_policy": "advisory-only",
    }
    assert results[2]["level"] == "note"
    assert results[2]["message"]["text"] == "Advisory-only (fixtures): hardcoded secret in replay fixture"
    assert results[2]["properties"] == {
        "aci.scope_class": "fixtures",
        "aci.scope_policy": "advisory-only",
    }


def test_emit_github_summary_cli_filters_scope_class(tmp_path: Path, capsys) -> None:
    report_path = _write_report(tmp_path)

    result = _handle_report_command(
        SimpleNamespace(
            command="emit-github-summary",
            report=report_path,
            report_scope_class=["docs-evidence"],
            report_owner_lane=[],
        )
    )

    assert result == 0
    output = capsys.readouterr().out
    assert "- Visible view: `1` of `3` finding(s)" in output
    assert "- Findings: `1`" in output
    assert "- Gate: `pass`" in output
    assert "docs-evidence" in output


def test_emit_annotations_cli_filters_owner_lane(tmp_path: Path, capsys) -> None:
    report_path = _write_report(tmp_path)

    result = _handle_report_command(
        SimpleNamespace(
            command="emit-annotations",
            report=report_path,
            report_scope_class=[],
            report_owner_lane=["human-judgment"],
        )
    )

    assert result == 0
    assert capsys.readouterr().out.splitlines() == [
        "::notice file=docs/note.py,line=3,title=CI-03 CI03_TODO_HACK::advisory-only (docs-evidence): TODO line 1%252C line 2",
    ]


def test_emit_sarif_cli_filters_scope_class(tmp_path: Path, capsys) -> None:
    report_path = _write_report(tmp_path)

    result = _handle_report_command(
        SimpleNamespace(
            command="emit-sarif",
            report=report_path,
            report_scope_class=["docs-evidence"],
            report_owner_lane=[],
        )
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    results = payload["runs"][0]["results"]
    assert len(results) == 1
    assert results[0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "docs/note.py"


def test_github_summary_carries_the_detection_disclosure_at_the_point_of_use() -> None:
    # ACI's purpose includes making users aware that even its declared checks are
    # not 100%. The JSON report carries that disclosure, but the human-facing PR
    # summary is where a reviewer concludes "ACI passed, the code is clean" -- and
    # a clean, zero-finding pass is exactly where that false confidence is highest.
    # The disclosure must therefore travel with the summary, sourced from the same
    # report key (single source of truth).
    disclosure = "Bounded best-effort audit; detection is not 100%."
    clean_report: dict[str, object] = {
        "gate": {"decision": "pass"},
        "summary": {"total_findings": 0, "blocker_count": 0},
        "review_brief": {"scope_mode": "full-repo", "blocker_headline": "No blocking findings remain."},
        "detection_disclosure": disclosure,
    }
    markdown = build_github_summary_markdown(clean_report)
    assert disclosure in markdown, "the non-exhaustiveness disclosure must appear in the human summary"
    assert "Gate: `pass`" in markdown and "Findings: `0`" in markdown

    # A report without the key must still render (older reports, partial payloads).
    no_disclosure = {k: v for k, v in clean_report.items() if k != "detection_disclosure"}
    rendered = build_github_summary_markdown(no_disclosure)
    assert "Scope note:" not in rendered
