#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ACI vs ruff differentiation harness (maintainer evidence tool, not packaged).

Answers: do ACI's native detectors add value over an existing linter, or do they
duplicate it? Runs the ACI native lane and `ruff --select ALL` over the same
project(s) and reports, per CI-ID, how many ACI findings are CO-LOCATED with a
ruff finding (ruff already flags that line) vs ACI-unique (no ruff finding there).

High co-location => ruff already catches it (ACI duplicates).
Low co-location  => ACI surfaces something ruff does not at that location.

This is a location-overlap heuristic, not proof of semantic equivalence, but it
is concrete evidence for deepen-vs-drop decisions.

Usage:
    python shared/tools/aci_differentiation.py <project-dir> [<project-dir> ...] \
        [--json OUT.json]

Requires `ruff` on PATH (skips the comparison with a clear message otherwise).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

try:
    from aci.aci_scan import scan_target
except ImportError:  # pragma: no cover - direct source checkout path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from aci_scan import scan_target  # type: ignore[no-redef]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKSPACE_ROOT = _REPO_ROOT / "workspace"


# Ruff rule codes whose category is the SAME smell as an ACI CI-ID. Used to tell
# a genuine semantic duplicate (ruff already has a rule for this) from an
# incidental line co-location (ruff flags the same line for an unrelated reason).
# (ruff-code prefix, ACI CI-ID) pairs, longest-prefix-first so specific codes win.
_RUFF_PREFIX_TO_CI: list[tuple[str, str]] = [
    ("C901", "CI-02"),     # mccabe complexity
    ("PLR0915", "CI-02"),  # too-many-statements
    ("PLR0912", "CI-02"),  # too-many-branches
    ("PLR0904", "CI-04"),  # too-many-public-methods
    ("PLR0913", "CI-18"),  # too-many-arguments
    ("PLW0603", "CI-26"),  # global-statement
    ("SIM115", "CI-22"),   # open without context manager
    ("S311", "CI-25"),     # non-crypto random (nondeterminism)
    ("TD", "CI-03"), ("FIX", "CI-03"),  # patchwork-marker families
    ("BLE", "CI-21"),      # blind-except family
    ("S", "CI-14"),        # flake8-bandit security family
]


def _ruff_code_ci(code: str) -> str | None:
    for prefix, ci in _RUFF_PREFIX_TO_CI:
        if code.startswith(prefix):
            return ci
    return None


def _ruff_locations(project: Path) -> dict[tuple[str, int], list[str]]:
    """Map (posix-relative-file, row) -> list of ruff codes for the project."""
    result = subprocess.run(
        ["ruff", "check", "--select", "ALL", "--output-format", "json", "--no-cache", str(project)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    locations: dict[tuple[str, int], list[str]] = defaultdict(list)
    out = result.stdout.strip()
    if not out:
        return locations
    try:
        items = json.loads(out)
    except json.JSONDecodeError:
        return locations
    for item in items:
        filename = item.get("filename")
        row = (item.get("location") or {}).get("row")
        code = item.get("code")
        if not filename or row is None:
            continue
        try:
            rel = Path(filename).resolve().relative_to(project.resolve()).as_posix()
        except ValueError:
            rel = Path(filename).name
        locations[(rel, int(row))].append(code or "?")
    return locations


def differentiate(paths: list[Path]) -> dict:
    per_ci: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "ruff_colocated": 0, "semantic_dup": 0, "ruff_codes": defaultdict(int)}
    )
    for project in paths:
        # ruff hard-excludes anything under venv/site-packages, so copy the tree
        # to a neutral temp location and run both tools there (paths then match).
        _WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix="aci_diff_", dir=_WORKSPACE_ROOT))
        dest = tmp / project.name
        shutil.copytree(project, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        try:
            report = scan_target(dest, "full", "core-only", include_external_analyzers=False)
            ruff_loc = _ruff_locations(dest)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        for f in report["findings"]:
            ci = f.get("ci_id", "?")
            target = f.get("target_file", "")
            line = f.get("line")
            bucket = per_ci[ci]
            bucket["total"] += 1
            codes: list[str] = []
            if isinstance(line, int):
                for dl in (0, -1, 1):
                    codes += ruff_loc.get((target, line + dl), [])
            if codes:
                bucket["ruff_colocated"] += 1
                for c in codes:
                    bucket["ruff_codes"][c] += 1
                # semantic duplicate only if a co-located ruff code is the SAME smell
                if any(_ruff_code_ci(c) == ci for c in codes):
                    bucket["semantic_dup"] += 1

    summary = {}
    for ci, b in sorted(per_ci.items()):
        total = b["total"]
        top_codes = sorted(b["ruff_codes"].items(), key=lambda kv: -kv[1])[:4]
        summary[ci] = {
            "total": total,
            "ruff_colocated": b["ruff_colocated"],
            "semantic_dup": b["semantic_dup"],
            "unique_category_pct": round(100 * (total - b["semantic_dup"]) / total) if total else 0,
            "top_colocated_ruff_codes": [c for c, _ in top_codes],
        }
    return {"projects": [str(p) for p in paths], "per_ci_id": summary}


def main() -> int:
    parser = argparse.ArgumentParser(prog="aci-differentiation")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    if shutil.which("ruff") is None:
        print("ruff is not installed; cannot run the differentiation comparison.")
        return 2

    result = differentiate(args.paths)
    if args.json:
        args.json.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"ACI vs ruff(--select ALL) over {len(result['projects'])} project(s)")
    print("  sem-dup = ruff has the SAME-category rule at that line (genuine duplicate)")
    print("  uniq-cat% = ACI findings whose category ruff does NOT cover\n")
    print(f"{'CI-ID':<8} {'total':>6} {'sem-dup':>8} {'uniq-cat%':>9}  top-colocated-ruff-codes")
    for ci, b in result["per_ci_id"].items():
        codes = ",".join(b["top_colocated_ruff_codes"])
        print(f"{ci:<8} {b['total']:>6} {b['semantic_dup']:>8} {b['unique_category_pct']:>8}%  {codes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
