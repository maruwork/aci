"""Gate the recall probe.

Asserts every harder positive variant that is *expected* to be caught is
caught (no untagged recall gap), so a future change that quietly drops recall
fails the build. Variants tagged as intentional precision/recall trade-offs
are allowed to miss.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOL = _REPO_ROOT / "shared" / "tools" / "aci_recall_probe.py"

_spec = importlib.util.spec_from_file_location("aci_recall_probe", _TOOL)
assert _spec and _spec.loader
_probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_probe)


def test_no_untagged_recall_gaps() -> None:
    result = _probe.run()
    assert result["recall"] == 1.0, (
        "recall gap on variants expected to be caught: "
        + ", ".join(g["label"] for g in result["gaps"])
    )
