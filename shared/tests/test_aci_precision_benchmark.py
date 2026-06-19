from __future__ import annotations

import importlib.util
import json
from pathlib import Path


_TOOL = Path(__file__).parent.parent / "tools" / "aci_precision_benchmark.py"
_SPEC = importlib.util.spec_from_file_location("aci_precision_benchmark", _TOOL)
assert _SPEC and _SPEC.loader
benchmark = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(benchmark)


def test_benchmark_precision_computes_overall_and_per_ci_metrics() -> None:
    findings = [
        {
            "fingerprint": "fp-1",
            "ci_id": "CI-21",
            "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
            "target_file": "a.py",
            "line": 1,
        },
        {
            "fingerprint": "fp-2",
            "ci_id": "CI-21",
            "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
            "target_file": "b.py",
            "line": 2,
        },
        {
            "fingerprint": "fp-3",
            "ci_id": "CI-04",
            "signal": "CI04_GOD_CLASS",
            "target_file": "c.py",
            "line": 3,
        },
    ]
    labels = {
        "fp-1": {"fingerprint": "fp-1", "label": "true-positive", "notes": ""},
        "fp-2": {"fingerprint": "fp-2", "label": "false-positive", "notes": ""},
        "fp-3": {"fingerprint": "fp-3", "label": "skip", "notes": ""},
    }

    result = benchmark.benchmark_precision(findings, labels)

    assert result["total_findings"] == 3
    assert result["labeled_findings"] == 3
    assert result["unlabeled_findings"] == 0
    assert result["true_positive"] == 1
    assert result["false_positive"] == 1
    assert result["skipped"] == 1
    assert result["precision"] == 0.5
    assert result["per_ci_id"]["CI-21"]["precision"] == 0.5
    assert result["per_ci_id"]["CI-04"]["precision"] is None
    assert result["unlabeled_per_ci_id"] == {}


def test_load_labels_rejects_duplicates_and_unknown_labels(tmp_path: Path) -> None:
    duplicate_path = tmp_path / "duplicate.json"
    duplicate_path.write_text(
        json.dumps(
            [
                {"fingerprint": "fp-1", "label": "true-positive"},
                {"fingerprint": "fp-1", "label": "false-positive"},
            ]
        ),
        encoding="utf-8",
    )
    try:
        benchmark._load_labels(duplicate_path)
        assert False, "expected duplicate labels to raise"
    except ValueError as exc:
        assert "Duplicate label" in str(exc)

    bad_label_path = tmp_path / "bad-label.json"
    bad_label_path.write_text(
        json.dumps([{"fingerprint": "fp-2", "label": "maybe"}]),
        encoding="utf-8",
    )
    try:
        benchmark._load_labels(bad_label_path)
        assert False, "expected unknown label to raise"
    except ValueError as exc:
        assert "Unsupported label" in str(exc)


def test_load_labels_can_keep_unlabeled_template_rows_when_requested(tmp_path: Path) -> None:
    labels_path = tmp_path / "labels.json"
    labels_path.write_text(
        json.dumps(
            [
                {"fingerprint": "fp-1", "label": "", "notes": "not reviewed yet"},
                {"fingerprint": "fp-2", "label": "true-positive", "notes": "confirmed"},
            ]
        ),
        encoding="utf-8",
    )

    labels = benchmark._load_labels(labels_path, allow_unlabeled=True)

    assert labels["fp-1"]["label"] == ""
    assert labels["fp-2"]["label"] == "true-positive"


def test_load_harness_findings_requires_findings_export(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.json"
    missing_path.write_text(json.dumps({"projects": []}), encoding="utf-8")

    try:
        benchmark._load_harness_findings(missing_path)
        assert False, "expected missing findings to raise"
    except ValueError as exc:
        assert "--include-findings" in str(exc)


def test_to_markdown_includes_precision_summary() -> None:
    result = {
        "total_findings": 4,
        "labeled_findings": 3,
        "unlabeled_findings": 1,
        "label_coverage": 0.75,
        "true_positive": 2,
        "false_positive": 1,
        "skipped": 0,
        "precision": 2 / 3,
        "per_ci_id": {
            "CI-21": {
                "true_positive": 2,
                "false_positive": 1,
                "skipped": 0,
                "labeled": 3,
                "precision": 2 / 3,
            }
        },
        "unlabeled_per_ci_id": {
            "CI-04": {
                "count": 1,
                "samples": [{"ci_id": "CI-04", "signal": "CI04_GOD_CLASS", "target_file": "x.py", "line": 8}],
            }
        },
        "unknown_label_fingerprints": ["fp-missing"],
        "unlabeled_samples": [{"ci_id": "CI-04", "signal": "CI04_GOD_CLASS", "target_file": "x.py", "line": 8}],
    }

    markdown = benchmark.to_markdown(result)

    assert "# ACI Labeled Precision Benchmark" in markdown
    assert "66.7%" in markdown
    assert "fp-missing" in markdown
    assert "CI04_GOD_CLASS" in markdown
    assert "Unlabeled Queue By CI-ID" in markdown


def test_benchmark_precision_treats_blank_labels_as_unlabeled() -> None:
    findings = [
        {
            "fingerprint": "fp-1",
            "ci_id": "CI-21",
            "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
            "target_file": "a.py",
            "line": 1,
        }
    ]
    labels = {
        "fp-1": {"fingerprint": "fp-1", "label": "", "notes": "pending"},
    }

    result = benchmark.benchmark_precision(findings, labels)

    assert result["labeled_findings"] == 0
    assert result["unlabeled_findings"] == 1
    assert result["precision"] is None
    assert result["unlabeled_per_ci_id"]["CI-21"]["count"] == 1
