"""ACI validation scorecard.

Runs the detectors against the ground-truth validation suite
(``examples/aci-validation-suite``) and reports reproducible recall and
false-positive numbers.

Why this exists: precision/recall claims made by eyeballing scan output are
circular -- the same judgment that built a detector grades its findings. Here
the labels are fixed in ``manifest.json`` ahead of time, so the score is a
property of the code, not of a reviewer's live opinion, and anyone can re-run
it to reproduce the number.

  - recall      = planted signals detected / planted signals expected
  - false-pos   = forbidden signals raised on the clean counterparts

Run directly for a human report; exits non-zero if recall < 100% or any
false positive appears, so it can gate CI.

    python shared/tools/aci_validation_scorecard.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SUITE = _REPO_ROOT / "examples" / "aci-validation-suite"

# Make the package importable whether or not ACI is pip-installed.
sys.path.insert(0, str(_REPO_ROOT / "shared" / "python"))

try:
    from aci.aci_scan import scan_target  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - direct-source layout
    from aci_scan import scan_target  # type: ignore[no-redef]


def _signals(target: Path) -> set[str]:
    report = scan_target(target, "full", "core-only", include_external_analyzers=False)
    return {item["signal"] for item in report["findings"]}


def score(suite: Path = _SUITE) -> dict:
    manifest = json.loads((suite / "manifest.json").read_text(encoding="utf-8"))
    expected = set(manifest["planted_expected_signals"])
    forbidden = set(manifest["clean_forbidden_signals"])

    planted_signals = _signals(suite / "planted")
    clean_signals = _signals(suite / "clean")

    detected = expected & planted_signals
    missed = sorted(expected - planted_signals)
    false_positives = sorted(forbidden & clean_signals)

    recall = len(detected) / len(expected) if expected else 1.0
    return {
        "expected_count": len(expected),
        "detected_count": len(detected),
        "missed": missed,
        "recall": recall,
        "false_positives": false_positives,
        "clean_total_findings": len(clean_signals),
        "passed": not missed and not false_positives,
    }


def main() -> int:
    result = score()
    print("ACI validation scorecard")
    print("=" * 48)
    print(f"recall          : {result['detected_count']}/{result['expected_count']} "
          f"({result['recall'] * 100:.0f}%)")
    print(f"false positives : {len(result['false_positives'])}")
    if result["missed"]:
        print(f"  MISSED (recall gap): {', '.join(result['missed'])}")
    if result["false_positives"]:
        print(f"  FALSE POSITIVES    : {', '.join(result['false_positives'])}")
    print(f"clean-suite signals total : {result['clean_total_findings']} (target 0)")
    print("=" * 48)
    print("PASS" if result["passed"] else "FAIL")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
