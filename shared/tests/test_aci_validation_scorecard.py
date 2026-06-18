"""Gate the detector validation scorecard.

Asserts the ground-truth suite scores 100% recall with zero false positives,
so a regression in any detector's recall or precision fails the build with a
reproducible, label-driven number rather than a reviewer's opinion.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOL = _REPO_ROOT / "shared" / "tools" / "aci_validation_scorecard.py"

_spec = importlib.util.spec_from_file_location("aci_validation_scorecard", _TOOL)
assert _spec and _spec.loader
_scorecard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scorecard)


def test_validation_suite_full_recall_zero_false_positives() -> None:
    result = _scorecard.score()
    assert result["recall"] == 1.0, f"recall gap: missed {result['missed']}"
    assert result["false_positives"] == [], f"false positives: {result['false_positives']}"
    assert result["clean_total_findings"] == 0, "clean suite should produce no findings"
    assert result["per_signal"]["CI22_RESOURCE_CLEANUP_GAP"]["planted_detected"] is True
    assert result["per_signal"]["CI22_FIRE_AND_FORGET_TASK"]["clean_detected"] is False
    assert result["per_signal"]["CI14_UNSAFE_YAML_LOAD"]["planted_detected"] is True
    assert result["passed"]
