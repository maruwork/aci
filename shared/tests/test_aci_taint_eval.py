"""Gate the taint-rule precision/recall harness (shared/tools/aci_taint_eval.py).

G3 proved the bundled semgrep taint rules fire; this asserts they *discriminate*:
every curated source->sink positive is detected (recall) and every control flow
with no real flow stays silent (zero false positives). Runs in CI's Linux job
where semgrep is installed; skips elsewhere.
"""
from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOL = _REPO_ROOT / "shared" / "tools" / "aci_taint_eval.py"

_spec = importlib.util.spec_from_file_location("aci_taint_eval", _TOOL)
assert _spec and _spec.loader
_taint_eval = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_taint_eval)


@pytest.mark.skipif(shutil.which("semgrep") is None, reason="semgrep not installed")
def test_taint_rules_have_perfect_recall_and_no_false_positives() -> None:
    res = _taint_eval.run()
    assert res is not None  # semgrep present (guarded by skipif)

    # Recall: every genuine source->sink flow is caught (direct, multi-hop, and
    # several sink kinds, across JS and Python).
    assert res["false_negatives"] == [], f"taint recall gap: {res['false_negatives']}"
    assert res["recall"] == 1.0, res

    # Precision floor: no control flow fires. A constant fed to a sink, a tainted
    # value that never reaches a sink, and a source with no dangerous sink must
    # all stay silent -- this is what separates taint tracking from a bare
    # eval()-pattern match.
    assert res["false_positive_cases"] == [], f"taint false positives: {res['false_positive_cases']}"
    assert res["false_positive_rate"] == 0.0, res

    # Guard the corpus itself against accidental shrinkage to a trivial set.
    assert res["positives"] >= 8
    assert res["negatives"] >= 6
