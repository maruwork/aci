from __future__ import annotations

import importlib.util
import json
from pathlib import Path


_TOOL = Path(__file__).parent.parent / "tools" / "aci_precision_labelset.py"
_SPEC = importlib.util.spec_from_file_location("aci_precision_labelset", _TOOL)
assert _SPEC and _SPEC.loader
labelset = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(labelset)


def test_build_label_template_projects_findings_into_review_rows() -> None:
    findings = [
        {
            "fingerprint": "fp-1",
            "ci_id": "CI-21",
            "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
            "severity": "high",
            "confidence": "medium",
            "project": "demo",
            "target_file": "a.py",
            "line": 7,
            "reason": "broad except",
            "excerpt": "except Exception",
        }
    ]

    rows = labelset.build_label_template(findings)

    assert rows == [
        {
            "fingerprint": "fp-1",
            "label": "",
            "notes": "",
            "ci_id": "CI-21",
            "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
            "severity": "high",
            "confidence": "medium",
            "project": "demo",
            "target_file": "a.py",
            "line": 7,
            "reason": "broad except",
            "excerpt": "except Exception",
        }
    ]


def test_build_label_template_preserves_existing_labels() -> None:
    findings = [
        {
            "fingerprint": "fp-1",
            "ci_id": "CI-21",
            "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
            "target_file": "a.py",
        },
        {
            "fingerprint": "fp-2",
            "ci_id": "CI-04",
            "signal": "CI04_GOD_CLASS",
            "target_file": "b.py",
        },
    ]
    existing = {
        "fp-1": {
            "fingerprint": "fp-1",
            "label": "true-positive",
            "notes": "confirmed by reviewer",
        }
    }

    rows = labelset.build_label_template(findings, existing)

    assert rows[0]["label"] == "true-positive"
    assert rows[0]["notes"] == "confirmed by reviewer"
    assert rows[1]["label"] == ""


def test_generated_template_is_json_serializable(tmp_path: Path) -> None:
    findings = [
        {
            "fingerprint": "fp-1",
            "ci_id": "CI-21",
            "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
            "target_file": "a.py",
            "line": 1,
        }
    ]
    out_path = tmp_path / "labels.json"
    out_path.write_text(json.dumps(labelset.build_label_template(findings), indent=2), encoding="utf-8")

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload[0]["fingerprint"] == "fp-1"


def test_existing_template_with_blank_rows_can_be_reloaded_for_preserve_merge(tmp_path: Path) -> None:
    findings_path = tmp_path / "findings.json"
    labels_path = tmp_path / "labels.json"
    findings_path.write_text(
        json.dumps(
            {
                "findings": [
                    {
                        "fingerprint": "fp-1",
                        "ci_id": "CI-21",
                        "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    labels_path.write_text(
        json.dumps(
            [
                {
                    "fingerprint": "fp-1",
                    "label": "",
                    "notes": "pending",
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    findings = labelset._load_harness_findings(findings_path)
    existing = labelset._load_labels(labels_path, allow_unlabeled=True)
    rows = labelset.build_label_template(findings, existing)

    assert rows[0]["label"] == ""
    assert rows[0]["notes"] == "pending"
