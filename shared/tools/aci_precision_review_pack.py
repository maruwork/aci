#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a ready-to-review representative-corpus precision pack for ACI.

This tool turns one or more project paths into a review pack that contains:

- `findings.json`: flat finding export with stable fingerprints
- `triage.md`: per-CI-ID density report
- `labels.json`: human-review template, preserving any existing labels
- `benchmark.json` / `benchmark.md`: written automatically, including the
  unlabeled queue before review starts
- `README.md`: exact next-step commands for reviewers

Usage:
    python shared/tools/aci_precision_review_pack.py <path> [<path> ...] \
        --out-dir workspace/precision-review-pack [--scope-mode source-only] \
        [--include-path PATH] [--exclude-path PATH]
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

try:
    from aci_corpus_harness import scan_corpus, to_markdown as corpus_to_markdown
    from aci_precision_benchmark import benchmark_precision, to_markdown as benchmark_to_markdown
    from aci_precision_labelset import build_label_template
except ImportError:  # pragma: no cover - direct invocation from source checkout
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from aci_corpus_harness import scan_corpus, to_markdown as corpus_to_markdown  # type: ignore[no-redef]
    from aci_precision_benchmark import benchmark_precision, to_markdown as benchmark_to_markdown  # type: ignore[no-redef]
    from aci_precision_labelset import build_label_template  # type: ignore[no-redef]


def _load_existing_label_rows(path: Path | None) -> list[dict[str, object]]:
    if path is None or not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Existing labels JSON must be a list")
    rows: list[dict[str, object]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Each existing label row must be an object")
        fingerprint = str(item.get("fingerprint") or "").strip()
        if not fingerprint:
            raise ValueError("Each existing label row must include a non-empty fingerprint")
        rows.append(
            {
                "fingerprint": fingerprint,
                "label": str(item.get("label") or "").strip(),
                "notes": str(item.get("notes") or ""),
            }
        )
    return rows


def _rows_by_fingerprint(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}
    for row in rows:
        fingerprint = str(row["fingerprint"])
        if fingerprint in merged:
            raise ValueError(f"Duplicate label row for fingerprint {fingerprint}")
        merged[fingerprint] = dict(row)
    return merged


def _labeled_rows_by_fingerprint(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {
        str(row["fingerprint"]): dict(row)
        for row in rows
        if str(row.get("label") or "").strip()
    }


def _finding_sort_key(row: dict[str, object]) -> tuple[str, str, int, str]:
    line = row.get("line")
    normalized_line = line if isinstance(line, int) else 0
    return (
        str(row.get("project") or ""),
        str(row.get("target_file") or ""),
        normalized_line,
        str(row.get("fingerprint") or ""),
    )


def _review_projection(result: dict[str, object], findings: list[dict[str, object]], *, selection_mode: str) -> dict[str, object]:
    per_ci: dict[str, dict[str, object]] = {}
    by_ci: dict[str, list[dict[str, object]]] = defaultdict(list)
    for finding in findings:
        ci_id = str(finding.get("ci_id") or "UNKNOWN")
        by_ci[ci_id].append(finding)
    for ci_id, rows in sorted(by_ci.items()):
        per_ci[ci_id] = {
            "count": len(rows),
            "files_affected": len(
                {
                    (
                        str(row.get("project") or ""),
                        str(row.get("target_file") or ""),
                    )
                    for row in rows
                }
            ),
            "samples": [
                {
                    "project": str(row.get("project") or ""),
                    "signal": str(row.get("signal") or ""),
                    "confidence": str(row.get("confidence") or ""),
                    "target_file": str(row.get("target_file") or ""),
                    "line": row.get("line"),
                    "excerpt": str(row.get("excerpt") or ""),
                }
                for row in sorted(rows, key=_finding_sort_key)[:5]
            ],
        }
    return {
        "projects": result.get("projects", []),
        "total_findings": len(findings),
        "per_ci_id": per_ci,
        "findings": findings,
        "selection_mode": selection_mode,
        "source_total_findings": result.get("total_findings", len(findings)),
    }


def select_review_findings(
    findings: list[dict[str, object]],
    *,
    max_per_ci: int | None = None,
) -> list[dict[str, object]]:
    if max_per_ci is None:
        return [dict(row) for row in findings]
    if max_per_ci <= 0:
        raise ValueError("--max-per-ci must be positive when provided")

    grouped: dict[str, dict[str, list[dict[str, object]]]] = defaultdict(lambda: defaultdict(list))
    for finding in findings:
        ci_id = str(finding.get("ci_id") or "UNKNOWN")
        project = str(finding.get("project") or "")
        grouped[ci_id][project].append(dict(finding))

    selected: list[dict[str, object]] = []
    for ci_id in sorted(grouped):
        per_project = {
            project: sorted(rows, key=_finding_sort_key)
            for project, rows in grouped[ci_id].items()
        }
        ci_selected: list[dict[str, object]] = []
        project_names = sorted(per_project)
        while len(ci_selected) < max_per_ci:
            progressed = False
            for project_name in project_names:
                rows = per_project[project_name]
                if not rows:
                    continue
                ci_selected.append(rows.pop(0))
                progressed = True
                if len(ci_selected) >= max_per_ci:
                    break
            if not progressed:
                break
        selected.extend(ci_selected)
    return selected


def build_pack_readme(
    out_dir: Path,
    corpus_paths: list[Path],
    corpus_result: dict[str, object],
    label_rows: list[dict[str, object]],
    *,
    review_findings_count: int,
    selection_mode: str,
    benchmark_written: bool,
) -> str:
    labeled_count = sum(1 for row in label_rows if str(row.get("label") or "").strip())
    lines = ["# ACI Precision Review Pack", ""]
    lines.append("## Corpus paths")
    lines.append("")
    for path in corpus_paths:
        lines.append(f"- `{path}`")
    lines.append("")
    lines.append(f"- Full corpus findings: `{corpus_result['total_findings']}`")
    lines.append(f"- Review findings exported: `{review_findings_count}`")
    lines.append(f"- Corpus scope mode: `{corpus_result.get('scope_mode', 'unknown')}`")
    include_paths = corpus_result.get("include_paths")
    exclude_paths = corpus_result.get("exclude_paths")
    if isinstance(include_paths, list) and include_paths:
        lines.append(f"- Include paths: `{', '.join(str(item) for item in include_paths)}`")
    if isinstance(exclude_paths, list) and exclude_paths:
        lines.append(f"- Exclude paths: `{', '.join(str(item) for item in exclude_paths)}`")
    lines.append(f"- Review selection mode: `{selection_mode}`")
    lines.append(f"- Label rows prepared: `{len(label_rows)}`")
    lines.append(f"- Currently labeled rows: `{labeled_count}`")
    lines.append("")
    lines.append("## Review flow")
    lines.append("")
    lines.append(f"1. Open `{out_dir / 'triage.md'}` to see full-corpus density and hot CI-IDs first.")
    lines.append(f"2. Review `{out_dir / 'findings.json'}` and edit `{out_dir / 'labels.json'}` to fill `label` with `true-positive`, `false-positive`, or `skip`.")
    lines.append("3. Re-run the benchmark command below at any time; blank labels are treated as unlabeled.")
    lines.append("")
    lines.append("## Commands")
    lines.append("")
    lines.append("```powershell")
    lines.append(
        "python shared/tools/aci_precision_benchmark.py "
        f"--findings-json \"{out_dir / 'findings.json'}\" "
        f"--labels-json \"{out_dir / 'labels.json'}\" "
        f"--json \"{out_dir / 'benchmark.json'}\" "
        f"--markdown \"{out_dir / 'benchmark.md'}\""
    )
    lines.append("```")
    lines.append("")
    lines.append(f"Full-corpus export is also preserved at `{out_dir / 'corpus.json'}`.")
    lines.append("")
    if benchmark_written:
        lines.append("Benchmark files were refreshed from the current label state.")
    else:
        lines.append("Benchmark files were written with an unlabeled queue only; no labeled precision exists yet.")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This pack is workflow scaffolding, not publishable evidence by itself.")
    lines.append("- Completion remains blocked until a representative real corpus is actually human-labeled.")
    return "\n".join(lines)


def write_review_pack(
    out_dir: Path,
    corpus_paths: list[Path],
    corpus_result: dict[str, object],
    *,
    existing_label_rows: list[dict[str, object]] | None = None,
    max_per_ci: int | None = None,
) -> dict[str, object]:
    findings = corpus_result.get("findings")
    if not isinstance(findings, list):
        raise ValueError("Corpus result must include flat findings; run scan_corpus(..., include_findings=True)")
    out_dir.mkdir(parents=True, exist_ok=True)

    existing_label_rows = existing_label_rows or []
    review_findings = select_review_findings(findings, max_per_ci=max_per_ci)
    selection_mode = "full-findings" if max_per_ci is None else f"round-robin-per-ci(max={max_per_ci})"
    review_result = _review_projection(corpus_result, review_findings, selection_mode=selection_mode)
    label_rows = build_label_template(review_findings, _rows_by_fingerprint(existing_label_rows))

    corpus_path = out_dir / "corpus.json"
    findings_path = out_dir / "findings.json"
    triage_path = out_dir / "triage.md"
    labels_path = out_dir / "labels.json"
    benchmark_json_path = out_dir / "benchmark.json"
    benchmark_md_path = out_dir / "benchmark.md"
    readme_path = out_dir / "README.md"

    corpus_path.write_text(json.dumps(corpus_result, indent=2), encoding="utf-8")
    findings_path.write_text(json.dumps(review_result, indent=2), encoding="utf-8")
    triage_path.write_text(corpus_to_markdown(corpus_result), encoding="utf-8")
    labels_path.write_text(json.dumps(label_rows, indent=2), encoding="utf-8")

    labeled = _labeled_rows_by_fingerprint(label_rows)
    benchmark_result = benchmark_precision(review_findings, labeled)
    benchmark_json_path.write_text(json.dumps(benchmark_result, indent=2), encoding="utf-8")
    benchmark_md_path.write_text(benchmark_to_markdown(benchmark_result), encoding="utf-8")
    benchmark_written = True

    readme_path.write_text(
        build_pack_readme(
            out_dir,
            corpus_paths,
            corpus_result,
            label_rows,
            review_findings_count=len(review_findings),
            selection_mode=selection_mode,
            benchmark_written=benchmark_written,
        ),
        encoding="utf-8",
    )
    return {
        "corpus_path": corpus_path,
        "findings_path": findings_path,
        "triage_path": triage_path,
        "labels_path": labels_path,
        "benchmark_json_path": benchmark_json_path,
        "benchmark_md_path": benchmark_md_path,
        "readme_path": readme_path,
        "benchmark_written": benchmark_written,
        "selection_mode": selection_mode,
        "review_finding_count": len(review_findings),
        "label_row_count": len(label_rows),
        "labeled_row_count": len(labeled),
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="aci-precision-review-pack")
    parser.add_argument("paths", nargs="+", type=Path, help="project directories to scan")
    parser.add_argument("--out-dir", required=True, type=Path, help="directory where the review pack should be written")
    parser.add_argument("--samples", type=int, default=5, help="max sampled findings per CI-ID in triage.md")
    parser.add_argument(
        "--existing-labels-json",
        type=Path,
        default=None,
        help="optional existing labels/template JSON to merge and preserve; defaults to <out-dir>/labels.json when present",
    )
    parser.add_argument(
        "--max-per-ci",
        type=int,
        default=None,
        help="optional deterministic review cap per CI-ID using round-robin project selection",
    )
    parser.add_argument(
        "--scope-mode",
        default="source-only",
        help="scan scope mode for corpus review (default: source-only)",
    )
    parser.add_argument(
        "--include-path",
        action="append",
        default=[],
        help="optional relative include path passed through to scan_target; may be repeated",
    )
    parser.add_argument(
        "--exclude-path",
        action="append",
        default=[],
        help="optional relative exclude path passed through to scan_target; may be repeated",
    )
    args = parser.parse_args()

    missing = [p for p in args.paths if not p.is_dir()]
    if missing:
        parser.error(f"not a directory: {', '.join(str(m) for m in missing)}")

    existing_path = args.existing_labels_json
    if existing_path is None:
        candidate = args.out_dir / "labels.json"
        existing_path = candidate if candidate.exists() else None

    corpus_result = scan_corpus(
        args.paths,
        args.samples,
        include_findings=True,
        scope_mode=args.scope_mode,
        include_paths=tuple(str(item) for item in args.include_path),
        exclude_paths=tuple(str(item) for item in args.exclude_path),
    )
    written = write_review_pack(
        args.out_dir,
        args.paths,
        corpus_result,
        existing_label_rows=_load_existing_label_rows(existing_path),
        max_per_ci=args.max_per_ci,
    )

    print(f"review pack: {args.out_dir}")
    print(f"findings exported: {corpus_result['total_findings']}")
    print(f"review findings: {written['review_finding_count']}")
    print(f"label rows: {written['label_row_count']}")
    print(f"labeled rows: {written['labeled_row_count']}")
    print(f"selection mode: {written['selection_mode']}")
    print(f"benchmark written: {'yes' if written['benchmark_written'] else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
