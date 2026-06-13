#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ACI corpus precision harness (maintainer QA tool, not part of the package).

Runs the ACI native-static lane over one or more real Python codebases and
aggregates findings per CI-ID. On mature, well-maintained corpora the expected
true-positive rate is low, so a high finding density for a given CI-ID is a
precision signal (likely false positives) that should be triaged.

This does NOT compute true precision/recall — that needs human-labeled ground
truth. It produces the per-CI-ID density + sampled findings that a human triages
to label TP/FP, the same workflow recorded in
domains/pier/aci-pier-validation-decision-register.md.

Usage:
    python shared/tools/aci_corpus_harness.py <path> [<path> ...] \
        [--samples N] [--json OUT.json] [--markdown OUT.md]

Each <path> is a project directory (scanned with profile=full, native lane only
so external-analyzer availability does not affect the baseline).
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

try:
    from aci.aci_scan import scan_target
except ImportError:  # pragma: no cover - direct source checkout path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from aci_scan import scan_target  # type: ignore[no-redef]


def scan_corpus(paths: list[Path], samples: int) -> dict:
    """Scan each path (native lane) and aggregate findings per CI-ID."""
    per_ci: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "files": set(), "samples": []}
    )
    projects: list[dict] = []

    for path in paths:
        report = scan_target(
            path, "full", "core-only", include_external_analyzers=False
        )
        findings = report["findings"]
        projects.append({"path": str(path), "total_findings": len(findings)})
        for f in findings:
            ci = f.get("ci_id", "UNKNOWN")
            bucket = per_ci[ci]
            bucket["count"] += 1
            bucket["files"].add(f.get("target_file", ""))
            if len(bucket["samples"]) < samples:
                bucket["samples"].append(
                    {
                        "project": str(path),
                        "signal": f.get("signal"),
                        "confidence": f.get("confidence"),
                        "target_file": f.get("target_file"),
                        "line": f.get("line"),
                        "excerpt": (f.get("excerpt") or "")[:160],
                    }
                )

    summary = {
        ci: {
            "count": b["count"],
            "files_affected": len(b["files"]),
            "samples": b["samples"],
        }
        for ci, b in sorted(per_ci.items(), key=lambda kv: -kv[1]["count"])
    }
    return {
        "projects": projects,
        "total_findings": sum(p["total_findings"] for p in projects),
        "per_ci_id": summary,
    }


def to_markdown(result: dict) -> str:
    lines = ["# ACI Corpus Precision Baseline", ""]
    lines.append(f"Total findings: **{result['total_findings']}** across {len(result['projects'])} project(s)")
    lines.append("")
    lines.append("## Per-CI-ID density (triage: high count on mature code => likely FP)")
    lines.append("")
    lines.append("| CI-ID | count | files | top signal |")
    lines.append("|---|--:|--:|---|")
    for ci, b in result["per_ci_id"].items():
        top_signal = b["samples"][0]["signal"] if b["samples"] else "-"
        lines.append(f"| {ci} | {b['count']} | {b['files_affected']} | `{top_signal}` |")
    lines.append("")
    lines.append("## Projects scanned")
    lines.append("")
    for p in result["projects"]:
        lines.append(f"- `{p['path']}` — {p['total_findings']} findings")
    lines.append("")
    lines.append("## Triage samples (per CI-ID)")
    lines.append("")
    for ci, b in result["per_ci_id"].items():
        lines.append(f"### {ci} ({b['count']} findings, {b['files_affected']} files)")
        lines.append("")
        for s in b["samples"]:
            loc = f"{s['target_file']}:{s['line']}"
            lines.append(f"- [{s['confidence']}] `{s['signal']}` {loc}")
            if s["excerpt"]:
                lines.append(f"  - `{s['excerpt']}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(prog="aci-corpus-harness")
    parser.add_argument("paths", nargs="+", type=Path, help="project directories to scan")
    parser.add_argument("--samples", type=int, default=5, help="max sampled findings per CI-ID")
    parser.add_argument("--json", type=Path, default=None, help="write full JSON result here")
    parser.add_argument("--markdown", type=Path, default=None, help="write markdown triage report here")
    args = parser.parse_args()

    missing = [p for p in args.paths if not p.is_dir()]
    if missing:
        parser.error(f"not a directory: {', '.join(str(m) for m in missing)}")

    result = scan_corpus(args.paths, args.samples)

    if args.json:
        args.json.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    if args.markdown:
        args.markdown.write_text(to_markdown(result), encoding="utf-8")

    # Always print the compact per-CI-ID table to stdout.
    print(f"Total findings: {result['total_findings']} across {len(result['projects'])} project(s)")
    print(f"{'CI-ID':<8} {'count':>6} {'files':>6}")
    for ci, b in result["per_ci_id"].items():
        print(f"{ci:<8} {b['count']:>6} {b['files_affected']:>6}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
