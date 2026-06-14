"""Smoke test for the ACI-vs-ruff differentiation harness (T5).

Verifies the harness wiring (ACI scan + ruff + semantic-overlap mapping). Skips
when ruff is not installed. Does not assert exact numbers — only the contract.
"""
from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest

_TOOL = Path(__file__).parent.parent / "tools" / "aci_differentiation.py"
_spec = importlib.util.spec_from_file_location("aci_differentiation", _TOOL)
assert _spec and _spec.loader
diff = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(diff)


def test_ruff_code_ci_mapping() -> None:
    assert diff._ruff_code_ci("BLE001") == "CI-21"
    assert diff._ruff_code_ci("TD002") == "CI-03"
    assert diff._ruff_code_ci("PLR0913") == "CI-18"
    assert diff._ruff_code_ci("C901") == "CI-02"
    assert diff._ruff_code_ci("PLW0603") == "CI-26"
    assert diff._ruff_code_ci("S307") == "CI-14"
    assert diff._ruff_code_ci("E501") is None  # style, not an ACI category


@pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff not installed")
def test_differentiate_reports_semantic_overlap(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    proj.mkdir()
    # a broad except -> ACI CI-21 and ruff BLE001 at the same line (semantic dup)
    (proj / "m.py").write_text(
        "def f():\n    try:\n        return 1\n    except Exception:\n        return None\n",
        encoding="utf-8",
    )

    result = diff.differentiate([proj])
    per_ci = result["per_ci_id"]
    assert "CI-21" in per_ci
    ci21 = per_ci["CI-21"]
    assert ci21["total"] >= 1
    # ruff's BLE001 covers this category, so it should register as a semantic dup
    assert ci21["semantic_dup"] >= 1
    assert ci21["unique_category_pct"] < 100
