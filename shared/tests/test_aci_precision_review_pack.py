from __future__ import annotations

import importlib.util
import json
from pathlib import Path


_TOOL = Path(__file__).parent.parent / "tools" / "aci_precision_review_pack.py"
_SPEC = importlib.util.spec_from_file_location("aci_precision_review_pack", _TOOL)
assert _SPEC and _SPEC.loader
review_pack = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(review_pack)


def test_write_review_pack_bootstraps_review_files(tmp_path: Path) -> None:
    out_dir = tmp_path / "review-pack"
    corpus_result = {
        "projects": [{"path": "demo", "total_findings": 1}],
        "total_findings": 1,
        "per_ci_id": {
            "CI-21": {
                "count": 1,
                "files_affected": 1,
                "samples": [
                    {
                        "project": "demo",
                        "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
                        "confidence": "medium",
                        "target_file": "a.py",
                        "line": 7,
                        "excerpt": "except Exception",
                    }
                ],
            }
        },
        "findings": [
            {
                "fingerprint": "fp-1",
                "ci_id": "CI-21",
                "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
                "severity": "medium",
                "confidence": "medium",
                "project": "demo",
                "target_file": "a.py",
                "line": 7,
                "reason": "broad except",
                "excerpt": "except Exception",
            }
        ],
    }

    written = review_pack.write_review_pack(out_dir, [Path("demo")], corpus_result)

    assert written["benchmark_written"] is True
    assert written["selection_mode"] == "full-findings"
    assert (out_dir / "findings.json").exists()
    assert (out_dir / "corpus.json").exists()
    assert (out_dir / "triage.md").exists()
    assert (out_dir / "labels.json").exists()
    assert (out_dir / "README.md").exists()
    assert (out_dir / "benchmark.json").exists()
    assert (out_dir / "benchmark.md").exists()
    labels = json.loads((out_dir / "labels.json").read_text(encoding="utf-8"))
    assert labels[0]["fingerprint"] == "fp-1"
    assert labels[0]["label"] == ""
    benchmark_payload = json.loads((out_dir / "benchmark.json").read_text(encoding="utf-8"))
    assert benchmark_payload["unlabeled_findings"] == 1
    readme = (out_dir / "README.md").read_text(encoding="utf-8")
    assert "Full corpus findings: `1`" in readme
    assert "Review findings exported: `1`" in readme
    assert "Review selection mode: `full-findings`" in readme
    assert "Label rows prepared: `1`" in readme
    assert "Currently labeled rows: `0`" in readme
    assert "blank labels are treated as unlabeled" in readme
    assert "python shared/tools/aci_precision_benchmark.py" in readme
    assert "This pack is workflow scaffolding, not publishable evidence by itself." in readme


def test_write_review_pack_preserves_existing_labels_and_refreshes_benchmark(tmp_path: Path) -> None:
    out_dir = tmp_path / "review-pack"
    corpus_result = {
        "projects": [{"path": "demo", "total_findings": 1}],
        "total_findings": 1,
        "per_ci_id": {
            "CI-21": {
                "count": 1,
                "files_affected": 1,
                "samples": [
                    {
                        "project": "demo",
                        "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
                        "confidence": "medium",
                        "target_file": "a.py",
                        "line": 7,
                        "excerpt": "except Exception",
                    }
                ],
            }
        },
        "findings": [
            {
                "fingerprint": "fp-1",
                "ci_id": "CI-21",
                "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
                "severity": "medium",
                "confidence": "medium",
                "project": "demo",
                "target_file": "a.py",
                "line": 7,
                "reason": "broad except",
                "excerpt": "except Exception",
            }
        ],
    }

    written = review_pack.write_review_pack(
        out_dir,
        [Path("demo")],
        corpus_result,
        existing_label_rows=[
            {"fingerprint": "fp-1", "label": "true-positive", "notes": "reviewed"}
        ],
    )

    assert written["benchmark_written"] is True
    benchmark_payload = json.loads((out_dir / "benchmark.json").read_text(encoding="utf-8"))
    assert benchmark_payload["labeled_findings"] == 1
    labels = json.loads((out_dir / "labels.json").read_text(encoding="utf-8"))
    assert labels[0]["label"] == "true-positive"
    assert "Overall labeled precision" in (out_dir / "benchmark.md").read_text(encoding="utf-8")
    readme = (out_dir / "README.md").read_text(encoding="utf-8")
    assert "Currently labeled rows: `1`" in readme
    assert "Benchmark files were refreshed from the current label state." in readme


def test_select_review_findings_round_robins_projects_per_ci() -> None:
    findings = [
        {"fingerprint": "fp-1", "ci_id": "CI-21", "project": "a", "target_file": "a1.py", "line": 1},
        {"fingerprint": "fp-2", "ci_id": "CI-21", "project": "a", "target_file": "a2.py", "line": 2},
        {"fingerprint": "fp-3", "ci_id": "CI-21", "project": "b", "target_file": "b1.py", "line": 3},
        {"fingerprint": "fp-4", "ci_id": "CI-21", "project": "c", "target_file": "c1.py", "line": 4},
    ]

    selected = review_pack.select_review_findings(findings, max_per_ci=3)

    assert [row["fingerprint"] for row in selected] == ["fp-1", "fp-3", "fp-4"]


def test_write_review_pack_can_export_sampled_review_subset(tmp_path: Path) -> None:
    out_dir = tmp_path / "review-pack"
    corpus_result = {
        "projects": [
            {"path": "demo-a", "total_findings": 2},
            {"path": "demo-b", "total_findings": 1},
        ],
        "total_findings": 3,
        "per_ci_id": {
            "CI-21": {
                "count": 3,
                "files_affected": 3,
                "samples": [],
            }
        },
        "findings": [
            {
                "fingerprint": "fp-1",
                "ci_id": "CI-21",
                "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
                "severity": "medium",
                "confidence": "medium",
                "project": "demo-a",
                "target_file": "a.py",
                "line": 7,
                "reason": "broad except",
                "excerpt": "except Exception",
            },
            {
                "fingerprint": "fp-2",
                "ci_id": "CI-21",
                "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
                "severity": "medium",
                "confidence": "medium",
                "project": "demo-a",
                "target_file": "b.py",
                "line": 8,
                "reason": "broad except",
                "excerpt": "except Exception",
            },
            {
                "fingerprint": "fp-3",
                "ci_id": "CI-21",
                "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
                "severity": "medium",
                "confidence": "medium",
                "project": "demo-b",
                "target_file": "c.py",
                "line": 9,
                "reason": "broad except",
                "excerpt": "except Exception",
            },
        ],
    }

    written = review_pack.write_review_pack(
        out_dir,
        [Path("demo-a"), Path("demo-b")],
        corpus_result,
        max_per_ci=2,
    )

    review_payload = json.loads((out_dir / "findings.json").read_text(encoding="utf-8"))
    labels = json.loads((out_dir / "labels.json").read_text(encoding="utf-8"))

    assert written["review_finding_count"] == 2
    assert written["selection_mode"] == "round-robin-per-ci(max=2)"
    assert review_payload["source_total_findings"] == 3
    assert review_payload["total_findings"] == 2
    assert [row["fingerprint"] for row in review_payload["findings"]] == ["fp-1", "fp-3"]
    assert [row["fingerprint"] for row in labels] == ["fp-1", "fp-3"]
    readme = (out_dir / "README.md").read_text(encoding="utf-8")
    assert "Full corpus findings: `3`" in readme
    assert "Review findings exported: `2`" in readme
    assert "Review selection mode: `round-robin-per-ci(max=2)`" in readme
