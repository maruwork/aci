"""Independent-evaluation harness regression test.

Locks in that ACI's detectors generalize to code they were never tuned on (the
Python standard library) and that the independent recall + noise surfaces stay
computable. This is the anti-circularity counterpart to the in-repo scorecard.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOL = _REPO_ROOT / "shared" / "tools" / "aci_independent_eval.py"

_spec = importlib.util.spec_from_file_location("aci_independent_eval", _TOOL)
assert _spec and _spec.loader
_indep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_indep)


def test_independent_recall_is_perfect_on_real_untuned_hosts() -> None:
    res = _indep.run()
    # Real host corpus was actually resolved and scanned.
    assert res["host_count"] >= 5
    assert res["total_lines"] > 1000

    # Every injected signal must be detected on real, signal-clean host code.
    # A None recall means no clean host was available, which should not happen
    # for these five signals across the stdlib host set.
    for row in res["recall_rows"]:
        assert row["injected"] >= 1, f"no clean host for {row['signal']}"
        assert row["recall"] == 1.0, f"independent recall gap: {row['signal']} {row['detected']}/{row['injected']}"
    assert res["recall_overall"] == 1.0


def test_noise_surface_is_reported_not_hidden() -> None:
    res = _indep.run()
    # The independent FP-candidate surface must be a real, structured number so a
    # precision regression on untuned code is visible rather than silently zero.
    assert isinstance(res["noise_by_signal"], dict)
    assert isinstance(res["noise_findings_per_kloc"], float)
    assert res["noise_findings_per_kloc"] >= 0.0
