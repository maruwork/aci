"""End-to-end proof that the external-analyzer lane runs real tools (P0-1).

The unit tests in test_aci_analyzer_execution.py mock subprocess and verify the
parsing/normalization logic. This file complements them by running the *real*
analyzer binary against a fixture and asserting a normalized finding is produced.

CI-07/CI-09/CI-13/CI-15 have no native detector — they depend entirely on this
lane — so a real end-to-end check guards against silent breakage of the lane
wiring (analyzer invocation -> output parse -> normalized finding).

Each test skips gracefully when the underlying analyzer binary is not installed,
so the suite stays green on minimal environments while still exercising the lane
in CI (where ruff is installed).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from aci.aci_scan import scan_target


def _scan_with_external(pack: Path) -> dict:
    return scan_target(pack, "full", "core-only", include_external_analyzers=True)


@pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff not installed")
def test_ruff_lane_produces_normalized_external_finding(tmp_path: Path) -> None:
    # Two unused imports -> ruff F401 -> CI-07 (Lava Flow), external-analyzer lane.
    (tmp_path / "bad.py").write_text(
        "import os\nimport sys\n\n\ndef f():\n    return 1\n", encoding="utf-8"
    )

    report = _scan_with_external(tmp_path)

    external = [f for f in report["findings"] if f.get("owner_lane") == "external-analyzer"]
    ci07 = [f for f in external if f.get("ci_id") == "CI-07"]
    assert ci07, f"expected a CI-07 external finding from ruff; got {external!r}"

    # Findings must carry the normalized contract fields, not raw tool output.
    sample = ci07[0]
    assert sample["target_file"].endswith("bad.py")
    assert isinstance(sample.get("line"), int) and sample["line"] >= 1
    assert sample.get("signal", "").startswith("EXT_")


@pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff not installed")
def test_external_lane_records_per_analyzer_runtime_state(tmp_path: Path) -> None:
    (tmp_path / "clean.py").write_text("def f():\n    return 1\n", encoding="utf-8")

    report = _scan_with_external(tmp_path)
    runs = {r["analyzer_id"]: r for r in report.get("external_analyzer_runs", [])}

    # ruff is wired into the lane (its actual execution + normalization is
    # asserted by test_ruff_lane_produces_normalized_external_finding).
    assert "ruff" in runs

    # Every analyzer run records a recognized runtime_state (never empty/garbage)
    # and never crashes the scan. This is the full valid set from
    # aci_analyzer_execution, including the transient failure states that can
    # legitimately occur under load (e.g. a flaky external tool invocation).
    valid_states = {
        "executed",
        "not-installed",
        "no-tests-collected",
        "no-applicable-source",
        "runtime-failure",
        "parse-failure",
        "spawn-failure",
        "timeout",
    }
    for run in runs.values():
        assert run["runtime_state"] in valid_states, run


def test_external_lane_off_yields_no_external_findings(tmp_path: Path) -> None:
    (tmp_path / "bad.py").write_text("import os\n\n\ndef f():\n    return 1\n", encoding="utf-8")

    report = scan_target(tmp_path, "full", "core-only", include_external_analyzers=False)
    external = [f for f in report["findings"] if f.get("owner_lane") == "external-analyzer"]
    assert external == [], f"external lane must be silent when disabled; got {external!r}"
