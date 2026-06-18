from __future__ import annotations

from pathlib import Path

from aci.aci_report_view import apply_report_view
from aci.aci_scan import scan_target
from shared.tests._aci_test_helpers import write_fixture as _write


def test_apply_report_view_recomputes_visible_summary_and_gate() -> None:
    report = {
        "command": "scan",
        "scope_rules": {"scope_mode": "full-repo", "gate_scope_classes": ["runtime-source"]},
        "summary": {"total_findings": 2, "suppressed_count": 0, "resolved_baseline_count": 0, "blocker_count": 1},
        "gate": {
            "decision": "fail",
            "blocking_severities": ["high", "critical"],
            "severity_threshold": "high",
            "fail_on_new_findings": False,
            "fail_on_unreviewed_review_required": False,
            "fail_on_analyzer_errors": False,
        },
        "review_brief": {"scope_mode": "full-repo", "recommended_focus": []},
        "external_analyzer_runs": [],
        "findings": [
            {
                "finding_id": "F-1",
                "ci_id": "CI-21",
                "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
                "severity": "high",
                "confidence": "medium",
                "actor_label": "ACI-detected",
                "triage_state": "fix-now",
                "priority": "P1",
                "fixability": "direct-fix",
                "baseline_status": "new",
                "waiver_status": "none",
                "lifecycle_state": "open",
                "owner_lane": "native-static",
                "target_file": "src/app.py",
                "line": 7,
                "excerpt": "except Exception:",
                "reason": "runtime blocker",
                "evidence_ref": "test",
                "recommended_action": "tighten exception handling",
                "verification_status": "executed",
                "scope_class": "runtime-source",
            },
            {
                "finding_id": "F-2",
                "ci_id": "CI-03",
                "signal": "CI03_TODO_HACK",
                "severity": "low",
                "confidence": "low",
                "actor_label": "ACI-detected",
                "triage_state": "review-first",
                "priority": "P3",
                "fixability": "owner-decision",
                "baseline_status": "new",
                "waiver_status": "none",
                "lifecycle_state": "open",
                "owner_lane": "human-judgment",
                "target_file": "docs/note.py",
                "line": 3,
                "excerpt": "# TODO",
                "reason": "docs-only advisory",
                "evidence_ref": "test",
                "recommended_action": "triage separately",
                "verification_status": "executed",
                "scope_class": "docs-evidence",
            },
        ],
    }

    projected = apply_report_view(report, scope_classes=["docs-evidence"])

    assert projected["summary"]["total_findings"] == 1
    assert projected["summary"]["by_scope_policy"] == {"gated": 0, "advisory": 1}
    assert projected["gate"]["decision"] == "pass"
    assert projected["blockers"] == []
    assert projected["report_view"]["source_gate_decision"] == "fail"
    assert projected["report_view"]["hidden_total_findings"] == 1
    assert projected["review_brief"]["advisory_headline"].startswith("1 advisory-only")


def test_scan_report_exposes_machine_readable_known_limits(tmp_path: Path) -> None:
    _write(tmp_path / "runtime.py", "def run():\n    return open('x.txt').read()\n")

    report = scan_target(tmp_path, "full", "core-only", include_external_analyzers=False)

    known_limit_ids = {item["limit_id"] for item in report["known_limits"]}
    assert "KL-ACI-CI05-STRUCTURE-EXACT" in known_limit_ids
    assert "KL-ACI-CI07-COMPILED-EXTENSIONS" in known_limit_ids
    assert "KL-ACI-CI14-SUPPLY-CHAIN-SCOPE" in known_limit_ids
    assert "KL-ACI-CI22-NONLOCAL-LIFECYCLE" in known_limit_ids


def test_full_repo_summary_separates_gated_and_advisory_findings(tmp_path: Path) -> None:
    _write(tmp_path / "src" / "danger.py", 'API_KEY = "SECRET12345"\n')
    _write(tmp_path / "examples" / "fixture.py", 'API_KEY = "SECRET12345"\n')

    report = scan_target(
        tmp_path,
        "full",
        "core-only",
        include_external_analyzers=False,
        scope_mode="full-repo",
    )

    assert report["summary"]["by_scope_policy"]["gated"] >= 1
    assert report["summary"]["by_scope_policy"]["advisory"] >= 1
    assert report["summary"]["advisory_by_scope_class"]["fixtures"] >= 1
    assert "advisory-only" in report["review_brief"]["advisory_headline"]
