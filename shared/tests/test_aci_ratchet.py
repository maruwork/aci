"""Ratchet gate unit tests."""
from __future__ import annotations

from pathlib import Path

from aci.aci_ratchet import (
    check_ratchet,
    count_by_ci_id,
    load_ratchet_state,
    save_ratchet_state,
)


def _finding(ci_id: str, waiver_status: str = "none") -> dict[str, object]:
    return {"ci_id": ci_id, "waiver_status": waiver_status}


# ── count_by_ci_id ──────────────────────────────────────────────────────────


def test_count_excludes_waived_findings() -> None:
    findings = [
        _finding("CI-02"),
        _finding("CI-02", waiver_status="waived"),
        _finding("CI-06"),
    ]
    assert count_by_ci_id(findings) == {"CI-02": 1, "CI-06": 1}


def test_count_empty_findings() -> None:
    assert count_by_ci_id([]) == {}


def test_count_all_waived() -> None:
    findings = [_finding("CI-02", waiver_status="waived")]
    assert count_by_ci_id(findings) == {}


# ── load / save state ────────────────────────────────────────────────────────


def test_load_returns_none_when_missing(tmp_path: Path) -> None:
    assert load_ratchet_state(tmp_path / ".aci-ratchet") is None


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / ".aci-ratchet"
    save_ratchet_state(path, {"CI-02": 3, "CI-06": 1})
    assert load_ratchet_state(path) == {"CI-02": 3, "CI-06": 1}


# ── check_ratchet: first run (baseline creation) ─────────────────────────────


def test_first_run_creates_baseline_and_passes(tmp_path: Path) -> None:
    path = tmp_path / ".aci-ratchet"
    findings = [_finding("CI-02"), _finding("CI-02"), _finding("CI-06")]
    result = check_ratchet(findings, state_path=path)

    assert result["decision"] == "pass"
    assert result["mode"] == "baseline-created"
    assert result["violations"] == []
    assert path.exists()
    assert load_ratchet_state(path) == {"CI-02": 2, "CI-06": 1}


# ── check_ratchet: subsequent runs ──────────────────────────────────────────


def test_stable_counts_pass(tmp_path: Path) -> None:
    path = tmp_path / ".aci-ratchet"
    save_ratchet_state(path, {"CI-02": 2})
    findings = [_finding("CI-02"), _finding("CI-02")]
    result = check_ratchet(findings, state_path=path)

    assert result["decision"] == "pass"
    assert result["violations"] == []


def test_decreased_count_passes_and_locks_in(tmp_path: Path) -> None:
    path = tmp_path / ".aci-ratchet"
    save_ratchet_state(path, {"CI-02": 3})
    findings = [_finding("CI-02")]
    result = check_ratchet(findings, state_path=path)

    assert result["decision"] == "pass"
    # Improvement locked in: stored count must now be 1, not 3
    assert load_ratchet_state(path) == {"CI-02": 1}


def test_increased_count_fails(tmp_path: Path) -> None:
    path = tmp_path / ".aci-ratchet"
    save_ratchet_state(path, {"CI-02": 1})
    findings = [_finding("CI-02"), _finding("CI-02"), _finding("CI-02")]
    result = check_ratchet(findings, state_path=path)

    assert result["decision"] == "fail"
    assert len(result["violations"]) == 1  # type: ignore[arg-type]
    violation = result["violations"][0]  # type: ignore[index]
    assert violation["ci_id"] == "CI-02"
    assert violation["previous"] == 1
    assert violation["current"] == 3
    assert violation["delta"] == 2


def test_fail_does_not_update_state(tmp_path: Path) -> None:
    path = tmp_path / ".aci-ratchet"
    save_ratchet_state(path, {"CI-02": 1})
    findings = [_finding("CI-02"), _finding("CI-02"), _finding("CI-02")]
    check_ratchet(findings, state_path=path)

    # State must be unchanged after a failed check
    assert load_ratchet_state(path) == {"CI-02": 1}


def test_new_ci_id_in_current_triggers_violation(tmp_path: Path) -> None:
    path = tmp_path / ".aci-ratchet"
    save_ratchet_state(path, {"CI-02": 1})
    findings = [_finding("CI-02"), _finding("CI-06")]
    result = check_ratchet(findings, state_path=path)

    assert result["decision"] == "fail"
    violations = result["violations"]  # type: ignore[assignment]
    assert any(v["ci_id"] == "CI-06" and v["previous"] == 0 for v in violations)


def test_ci_id_disappears_from_current_passes(tmp_path: Path) -> None:
    path = tmp_path / ".aci-ratchet"
    save_ratchet_state(path, {"CI-02": 2, "CI-06": 1})
    findings = [_finding("CI-02"), _finding("CI-02")]
    result = check_ratchet(findings, state_path=path)

    assert result["decision"] == "pass"
    assert load_ratchet_state(path) == {"CI-02": 2}


def test_waived_findings_excluded_from_ratchet_count(tmp_path: Path) -> None:
    path = tmp_path / ".aci-ratchet"
    save_ratchet_state(path, {"CI-02": 1})
    findings = [
        _finding("CI-02"),
        _finding("CI-02", waiver_status="waived"),
        _finding("CI-02", waiver_status="waived"),
    ]
    result = check_ratchet(findings, state_path=path)

    # 2 waived + 1 active = effective count 1, same as stored → pass
    assert result["decision"] == "pass"
