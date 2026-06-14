"""Native-vs-external dedup tests (T6).

When the external-analyzer lane (ruff) reports a CI-ID at a location, ACI drops
the duplicate native finding — it complements the external linter rather than
re-reporting what it already covers.
"""
from __future__ import annotations

from aci.aci_scan import _deduplicate_findings
from aci.aci_findings import build_finding, LANE_NATIVE_STATIC, LANE_EXTERNAL_ANALYZER


def _finding(ci_id: str, line: int, lane: str, signal: str, fid: str):
    return build_finding(
        finding_id=fid,
        ci_id=ci_id,
        signal=signal,
        severity="medium",
        target_file="m.py",
        reason="r",
        evidence_ref="e",
        line=line,
        owner_lane=lane,
    )


def test_native_deduped_against_external_same_ci_location() -> None:
    native = _finding("CI-21", 4, LANE_NATIVE_STATIC, "CI21_BROAD_EXCEPTION_SWALLOW", "F1")
    external = _finding("CI-21", 4, LANE_EXTERNAL_ANALYZER, "EXT_RUFF", "F2")
    result = _deduplicate_findings([native, external])
    assert len(result) == 1
    assert result[0].owner_lane == LANE_EXTERNAL_ANALYZER


def test_native_deduped_within_one_line_tolerance() -> None:
    native = _finding("CI-21", 5, LANE_NATIVE_STATIC, "CI21_BROAD_EXCEPTION_SWALLOW", "F1")
    external = _finding("CI-21", 4, LANE_EXTERNAL_ANALYZER, "EXT_RUFF", "F2")
    result = _deduplicate_findings([native, external])
    assert len(result) == 1
    assert result[0].owner_lane == LANE_EXTERNAL_ANALYZER


def test_native_kept_when_external_is_different_ci() -> None:
    native = _finding("CI-21", 4, LANE_NATIVE_STATIC, "CI21_BROAD_EXCEPTION_SWALLOW", "F1")
    external = _finding("CI-07", 4, LANE_EXTERNAL_ANALYZER, "EXT_RUFF", "F2")
    result = _deduplicate_findings([native, external])
    assert len(result) == 2


def test_native_kept_when_no_external_lane() -> None:
    a = _finding("CI-21", 4, LANE_NATIVE_STATIC, "CI21_BROAD_EXCEPTION_SWALLOW", "F1")
    b = _finding("CI-04", 9, LANE_NATIVE_STATIC, "CI04_GOD_CLASS", "F2")
    result = _deduplicate_findings([a, b])
    assert len(result) == 2
