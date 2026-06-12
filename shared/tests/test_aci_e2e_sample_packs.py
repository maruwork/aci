"""E2E sample pack tests (MGEF-T39-restore).

Two example packs validate end-to-end detection accuracy:
- aci-false-negative-challenge-pack: confirms CI-18/CI-20/CI-21/CI-25/CI-26 are detected
- aci-precision-replay-pack: confirms no false positives for the same signals
"""
from __future__ import annotations

from pathlib import Path

from aci.aci_scan import scan_target

_EXAMPLES = Path(__file__).parent.parent.parent / "examples"
_FN_PACK = _EXAMPLES / "aci-false-negative-challenge-pack"
_PR_PACK = _EXAMPLES / "aci-precision-replay-pack"


def _signals(pack: Path) -> set[str]:
    report = scan_target(pack, "full", "core-only", include_external_analyzers=False)
    return {item["signal"] for item in report["findings"]}


# ── False-negative challenge pack ─────────────────────────────────────────

def test_fn_pack_detects_parameter_cluster() -> None:
    assert "CI18_PARAMETER_CLUSTER" in _signals(_FN_PACK)


def test_fn_pack_detects_scattered_constant() -> None:
    assert "CI20_SCATTERED_CONSTANT" in _signals(_FN_PACK)


def test_fn_pack_detects_broad_exception_swallow() -> None:
    assert "CI21_BROAD_EXCEPTION_SWALLOW" in _signals(_FN_PACK)


def test_fn_pack_detects_silent_exception_return() -> None:
    assert "CI21_SILENT_EXCEPTION_RETURN" in _signals(_FN_PACK)


def test_fn_pack_detects_environment_drift() -> None:
    assert "CI25_ENVIRONMENT_DRIFT" in _signals(_FN_PACK)


def test_fn_pack_detects_race_hazard() -> None:
    assert "CI26_RACE_HAZARD" in _signals(_FN_PACK)


# ── Precision replay pack ─────────────────────────────────────────────────

def test_pr_pack_no_false_positive_parameter_cluster() -> None:
    assert "CI18_PARAMETER_CLUSTER" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_broad_exception_swallow() -> None:
    assert "CI21_BROAD_EXCEPTION_SWALLOW" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_silent_exception_return() -> None:
    assert "CI21_SILENT_EXCEPTION_RETURN" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_environment_drift() -> None:
    assert "CI25_ENVIRONMENT_DRIFT" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_race_hazard() -> None:
    assert "CI26_RACE_HAZARD" not in _signals(_PR_PACK)
