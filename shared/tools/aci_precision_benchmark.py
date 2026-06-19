#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Labeled precision benchmark for ACI maintainer QA.

This tool evaluates human-labeled findings exported from
`shared/tools/aci_corpus_harness.py --include-findings`.

It computes labeled precision only. It does not claim real recall, because that
still requires a separate labeled false-negative / missed-signal workflow.

Label file shape:

[
  {
    "fingerprint": "abc123...",
    "label": "true-positive",
    "notes": "optional human review note"
  }
]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


ALLOWED_LABELS: frozenset[str] = frozenset({"true-positive", "false-positive", "skip"})


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_harness_findings(path: Path) -> list[dict[str, object]]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("Harness JSON must be an object")
    findings = payload.get("findings")
    if not isinstance(findings, list):
        raise ValueError("Harness JSON must contain a top-level 'findings' list; re-run with --include-findings")
    normalized: list[dict[str, object]] = []
    for item in findings:
        if not isinstance(item, dict):
            raise ValueError("Each harness finding row must be an object")
        fingerprint = str(item.get("fingerprint") or "").strip()
        if not fingerprint:
            raise ValueError("Each harness finding row must include a non-empty fingerprint")
        normalized.append(dict(item))
    return normalized


def _load_labels(
    path: Path,
    *,
    allow_unlabeled: bool = False,
) -> dict[str, dict[str, object]]:
    payload = _load_json(path)
    if not isinstance(payload, list):
        raise ValueError("Label JSON must be a list")
    labels_by_fingerprint: dict[str, dict[str, object]] = {}
    for raw_item in payload:
        if not isinstance(raw_item, dict):
            raise ValueError("Each label row must be an object")
        fingerprint = str(raw_item.get("fingerprint") or "").strip()
        label = str(raw_item.get("label") or "").strip()
        if not fingerprint:
            raise ValueError("Each label row must include a non-empty fingerprint")
        if not label and allow_unlabeled:
            normalized_label = ""
        elif label in ALLOWED_LABELS:
            normalized_label = label
        else:
            raise ValueError(
                f"Unsupported label '{label}' for fingerprint {fingerprint}; "
                f"allowed labels: {', '.join(sorted(ALLOWED_LABELS))}"
            )
        if fingerprint in labels_by_fingerprint:
            raise ValueError(f"Duplicate label for fingerprint {fingerprint}")
        labels_by_fingerprint[fingerprint] = {
            "fingerprint": fingerprint,
            "label": normalized_label,
            "notes": str(raw_item.get("notes") or ""),
        }
    return labels_by_fingerprint


def _precision(tp: int, fp: int) -> float | None:
    denom = tp + fp
    if denom == 0:
        return None
    return tp / denom


def _finding_sort_key(row: dict[str, object]) -> tuple[str, str, int, str]:
    line = row.get("line")
    normalized_line = line if isinstance(line, int) else 0
    return (
        str(row.get("ci_id") or "UNKNOWN"),
        str(row.get("project") or ""),
        str(row.get("target_file") or ""),
        normalized_line,
        str(row.get("fingerprint") or ""),
    )


def benchmark_precision(findings: list[dict[str, object]], labels_by_fingerprint: dict[str, dict[str, object]]) -> dict[str, object]:
    labeled_rows: list[dict[str, object]] = []
    unlabeled_rows: list[dict[str, object]] = []
    per_ci: dict[str, Counter[str]] = defaultdict(Counter)
    unlabeled_per_ci: dict[str, list[dict[str, object]]] = defaultdict(list)
    unknown_label_fingerprints = sorted(
        fingerprint for fingerprint in labels_by_fingerprint if fingerprint not in {str(item.get("fingerprint") or "") for item in findings}
    )

    for finding in findings:
        fingerprint = str(finding.get("fingerprint") or "")
        label_row = labels_by_fingerprint.get(fingerprint)
        if label_row is None:
            row = dict(finding)
            unlabeled_rows.append(row)
            unlabeled_per_ci[str(finding.get("ci_id") or "UNKNOWN")].append(row)
            continue
        label = str(label_row["label"])
        if not label:
            row = dict(finding)
            unlabeled_rows.append(row)
            unlabeled_per_ci[str(finding.get("ci_id") or "UNKNOWN")].append(row)
            continue
        row = dict(finding)
        row["label"] = label
        row["notes"] = label_row.get("notes", "")
        labeled_rows.append(row)
        ci_id = str(finding.get("ci_id") or "UNKNOWN")
        per_ci[ci_id][label] += 1

    totals = Counter(str(item["label"]) for item in labeled_rows)
    tp = totals["true-positive"]
    fp = totals["false-positive"]
    skipped = totals["skip"]

    per_ci_summary: dict[str, dict[str, object]] = {}
    for ci_id, counts in sorted(per_ci.items()):
        ci_tp = counts["true-positive"]
        ci_fp = counts["false-positive"]
        ci_skipped = counts["skip"]
        per_ci_summary[ci_id] = {
            "true_positive": ci_tp,
            "false_positive": ci_fp,
            "skipped": ci_skipped,
            "labeled": ci_tp + ci_fp + ci_skipped,
            "precision": _precision(ci_tp, ci_fp),
        }

    unlabeled_summary: dict[str, dict[str, object]] = {}
    for ci_id, rows in sorted(unlabeled_per_ci.items()):
        sorted_rows = sorted(rows, key=_finding_sort_key)
        unlabeled_summary[ci_id] = {
            "count": len(sorted_rows),
            "samples": sorted_rows[:3],
        }

    return {
        "total_findings": len(findings),
        "labeled_findings": len(labeled_rows),
        "unlabeled_findings": len(unlabeled_rows),
        "label_coverage": (
            len(labeled_rows) / len(findings) if findings else 1.0
        ),
        "true_positive": tp,
        "false_positive": fp,
        "skipped": skipped,
        "precision": _precision(tp, fp),
        "per_ci_id": per_ci_summary,
        "unlabeled_per_ci_id": unlabeled_summary,
        "unknown_label_fingerprints": unknown_label_fingerprints,
        "unlabeled_samples": sorted(unlabeled_rows, key=_finding_sort_key)[:10],
    }


def to_markdown(result: dict[str, object]) -> str:
    lines = ["# ACI Labeled Precision Benchmark", ""]
    lines.append(f"- Total findings in corpus export: `{result['total_findings']}`")
    lines.append(f"- Labeled findings: `{result['labeled_findings']}`")
    lines.append(f"- Unlabeled findings: `{result['unlabeled_findings']}`")
    lines.append(f"- Label coverage: `{result['label_coverage']:.1%}`")
    precision = result["precision"]
    lines.append(
        f"- Overall labeled precision: `{precision:.1%}`" if isinstance(precision, float) else "- Overall labeled precision: `n/a`"
    )
    lines.append("")
    lines.append("| CI-ID | TP | FP | skipped | labeled | precision |")
    lines.append("|---|--:|--:|--:|--:|---:|")
    per_ci_id = result["per_ci_id"]
    assert isinstance(per_ci_id, dict)
    for ci_id, row in per_ci_id.items():
        assert isinstance(row, dict)
        row_precision = row.get("precision")
        precision_text = f"{row_precision:.1%}" if isinstance(row_precision, float) else "n/a"
        lines.append(
            f"| {ci_id} | {row['true_positive']} | {row['false_positive']} | {row['skipped']} | {row['labeled']} | {precision_text} |"
        )
    unlabeled_per_ci_id = result["unlabeled_per_ci_id"]
    assert isinstance(unlabeled_per_ci_id, dict)
    if unlabeled_per_ci_id:
        lines.append("")
        lines.append("## Unlabeled Queue By CI-ID")
        lines.append("")
        lines.append("| CI-ID | unlabeled | sample queue |")
        lines.append("|---|--:|---|")
        for ci_id, row in unlabeled_per_ci_id.items():
            assert isinstance(row, dict)
            samples = row.get("samples")
            assert isinstance(samples, list)
            sample_text = ", ".join(
                f"`{item.get('target_file')}:{item.get('line')}`"
                for item in samples
                if isinstance(item, dict)
            ) or "-"
            lines.append(f"| {ci_id} | {row['count']} | {sample_text} |")
    unknown = result["unknown_label_fingerprints"]
    assert isinstance(unknown, list)
    if unknown:
        lines.append("")
        lines.append("## Unknown label fingerprints")
        lines.append("")
        for fingerprint in unknown:
            lines.append(f"- `{fingerprint}`")
    unlabeled = result["unlabeled_samples"]
    assert isinstance(unlabeled, list)
    if unlabeled:
        lines.append("")
        lines.append("## Unlabeled sample findings")
        lines.append("")
        for item in unlabeled:
            assert isinstance(item, dict)
            lines.append(
                f"- `{item.get('ci_id')}` `{item.get('signal')}` `{item.get('target_file')}:{item.get('line')}`"
            )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(prog="aci-precision-benchmark")
    parser.add_argument("--findings-json", required=True, type=Path, help="JSON export from aci_corpus_harness.py --include-findings")
    parser.add_argument("--labels-json", required=True, type=Path, help="Human labels keyed by finding fingerprint")
    parser.add_argument("--json", type=Path, default=None, help="Write benchmark JSON result here")
    parser.add_argument("--markdown", type=Path, default=None, help="Write benchmark markdown report here")
    args = parser.parse_args()

    findings = _load_harness_findings(args.findings_json)
    labels_by_fingerprint = _load_labels(args.labels_json, allow_unlabeled=True)
    result = benchmark_precision(findings, labels_by_fingerprint)

    if args.json:
        args.json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if args.markdown:
        args.markdown.write_text(to_markdown(result), encoding="utf-8")

    precision = result["precision"]
    precision_text = f"{precision:.1%}" if isinstance(precision, float) else "n/a"
    print(f"labeled findings: {result['labeled_findings']} / {result['total_findings']}")
    print(f"label coverage: {result['label_coverage']:.1%}")
    print(f"overall labeled precision: {precision_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
