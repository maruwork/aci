"""Ratchet gate: prevents per-CI-ID finding counts from increasing across scans."""
from __future__ import annotations

import json
from pathlib import Path

_STATE_VERSION = "1"


def count_by_ci_id(findings: list[dict[str, object]]) -> dict[str, int]:
    """Return non-waived finding counts keyed by CI-ID."""
    counts: dict[str, int] = {}
    for f in findings:
        if f.get("waiver_status") != "none":
            continue
        ci_id = str(f.get("ci_id", ""))
        if ci_id:
            counts[ci_id] = counts.get(ci_id, 0) + 1
    return counts


def load_ratchet_state(path: Path) -> dict[str, int] | None:
    """Return stored CI-ID counts, or None if the file does not exist."""
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return dict(data.get("ci_id_counts", {}))


def save_ratchet_state(path: Path, counts: dict[str, int]) -> None:
    path.write_text(
        json.dumps({"version": _STATE_VERSION, "ci_id_counts": counts}, indent=2),
        encoding="utf-8",
    )


def check_ratchet(
    findings: list[dict[str, object]],
    *,
    state_path: Path,
) -> dict[str, object]:
    """Run ratchet check against stored state.

    First call (no state file): writes baseline and returns pass.
    Subsequent calls: fails if any CI-ID count exceeds stored value.
    On pass, updates stored state so count reductions are locked in.
    """
    current = count_by_ci_id(findings)
    stored = load_ratchet_state(state_path)

    if stored is None:
        save_ratchet_state(state_path, current)
        return {
            "decision": "pass",
            "mode": "baseline-created",
            "state_path": str(state_path),
            "ci_id_counts": current,
            "violations": [],
        }

    violations = [
        {
            "ci_id": ci_id,
            "previous": stored.get(ci_id, 0),
            "current": count,
            "delta": count - stored.get(ci_id, 0),
        }
        for ci_id, count in current.items()
        if count > stored.get(ci_id, 0)
    ]

    if not violations:
        save_ratchet_state(state_path, current)

    return {
        "decision": "fail" if violations else "pass",
        "mode": "check",
        "state_path": str(state_path),
        "ci_id_counts": current,
        "violations": violations,
    }
