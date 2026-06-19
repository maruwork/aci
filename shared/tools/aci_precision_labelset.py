#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate or refresh a human-label template for the ACI precision benchmark."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from aci_precision_benchmark import _load_harness_findings, _load_labels
except ImportError:  # pragma: no cover - direct source checkout path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from aci_precision_benchmark import _load_harness_findings, _load_labels  # type: ignore[no-redef]


def build_label_template(
    findings: list[dict[str, object]],
    existing_labels_by_fingerprint: dict[str, dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    existing_labels_by_fingerprint = existing_labels_by_fingerprint or {}
    rows: list[dict[str, object]] = []
    for finding in findings:
        fingerprint = str(finding.get("fingerprint") or "")
        existing = existing_labels_by_fingerprint.get(fingerprint, {})
        rows.append(
            {
                "fingerprint": fingerprint,
                "label": str(existing.get("label") or ""),
                "notes": str(existing.get("notes") or ""),
                "ci_id": str(finding.get("ci_id") or ""),
                "signal": str(finding.get("signal") or ""),
                "severity": str(finding.get("severity") or ""),
                "confidence": str(finding.get("confidence") or ""),
                "project": str(finding.get("project") or ""),
                "target_file": str(finding.get("target_file") or ""),
                "line": finding.get("line"),
                "reason": str(finding.get("reason") or ""),
                "excerpt": str(finding.get("excerpt") or ""),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(prog="aci-precision-labelset")
    parser.add_argument("--findings-json", required=True, type=Path, help="JSON export from aci_corpus_harness.py --include-findings")
    parser.add_argument("--out", required=True, type=Path, help="Write the label template JSON here")
    parser.add_argument("--existing-labels-json", type=Path, default=None, help="Optional existing label file to merge and preserve")
    args = parser.parse_args()

    findings = _load_harness_findings(args.findings_json)
    existing = _load_labels(args.existing_labels_json, allow_unlabeled=True) if args.existing_labels_json else {}
    rows = build_label_template(findings, existing)
    args.out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"label rows: {len(rows)}")
    print(f"pre-labeled rows preserved: {sum(1 for row in rows if row['label'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
