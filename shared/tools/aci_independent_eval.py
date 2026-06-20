"""ACI independent evaluation harness.

The validation scorecard grades ACI on fixtures authored alongside the detectors,
so its 25/25 recall and 0-FP numbers are a property of a tuned, in-repo set. This
harness measures the same detectors against code they were **never tuned on**: the
Python standard library, which is always present (so the measurement is reproducible
in CI), real, mature, and outside ACI's fixture corpus.

Two independent numbers are computed:

1. **Recall (mutation)** — a known smell is injected into a copy of a real stdlib
   file that is verified clean for that signal; recall = detected / injected. The
   surrounding host code is real and unfamiliar, so this is not a fixture replay.

2. **Noise / FP-candidate rate** — every selected stdlib file is scanned unmodified;
   findings per signal and per 1k lines are reported. On mature, widely-reviewed
   code a high-confidence structural/security finding is a precision-review
   candidate. This is the independent counterpart to the in-repo "0 false
   positives" claim.

True labelled precision still needs human adjudication (see
``aci_precision_review_pack.py``); this harness provides the independent recall and
noise surfaces that previously did not exist. Run for a human report:

    python shared/tools/aci_independent_eval.py
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import shutil
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "shared" / "python"))

try:
    from aci.aci_scan import scan_target  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - direct-source layout
    from aci_scan import scan_target  # type: ignore[no-redef]

# Real stdlib modules used as host code. Chosen for size and ubiquity; all ship
# with CPython so the corpus is reproducible anywhere the test runs.
_HOST_MODULES: tuple[str, ...] = (
    "argparse", "json", "csv", "configparser", "logging",
    "http.client", "email.parser", "xml.etree.ElementTree", "calendar", "gettext",
)

# Each injection: append a self-contained smelly function to a clean host file and
# expect the paired signal. The injected forms deliberately use import aliases so
# the harness also exercises the Phase 1 name-resolution path on real host code.
_INJECTIONS: tuple[tuple[str, str], ...] = (
    ("CI14_UNSAFE_DESERIALIZATION",
     "\n\nimport pickle as _aci_p\ndef _aci_inj_deser(_b):\n    return _aci_p.loads(_b)\n"),
    ("CI14_SUBPROCESS_SHELL_TRUE",
     "\n\nimport subprocess as _aci_sp\ndef _aci_inj_shell(_c):\n    _aci_sp.run(_c, shell=True)\n"),
    ("CI25_ENVIRONMENT_DRIFT",
     "\n\nimport datetime as _aci_dt\ndef _aci_inj_now():\n    return _aci_dt.datetime.now()\n"),
    ("CI21_BROAD_EXCEPTION_SWALLOW",
     "\n\ndef _aci_inj_swallow(_x):\n    try:\n        return _x()\n    except Exception:\n        return None\n"),
    ("CI26_RACE_HAZARD",
     "\n\n_aci_inj_state = 0\ndef _aci_inj_race():\n    global _aci_inj_state\n    _aci_inj_state += 1\n    return _aci_inj_state\n"),
)


def _host_files() -> list[Path]:
    paths: list[Path] = []
    for name in _HOST_MODULES:
        spec = importlib.util.find_spec(name)
        if spec is None or not spec.origin or not spec.origin.endswith(".py"):
            continue
        paths.append(Path(spec.origin))
    return paths


def _scan_source(name: str, source: str) -> set[str]:
    scratch = Path(tempfile.mkdtemp(prefix="aci_indep_"))
    try:
        (scratch / name).write_text(source, encoding="utf-8")
        report = scan_target(scratch, "full", "core-only", include_external_analyzers=False)
        return {item["signal"] for item in report["findings"]}
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def run() -> dict:
    hosts = _host_files()
    host_sources: list[tuple[str, str]] = []
    for path in hosts:
        try:
            host_sources.append((path.name, path.read_text(encoding="utf-8", errors="ignore")))
        except OSError:  # pragma: no cover - unreadable stdlib file
            continue

    # ── Recall via mutation on real, signal-clean host files ─────────────────
    recall_rows: list[dict] = []
    for signal, snippet in _INJECTIONS:
        injected = 0
        detected = 0
        used_hosts: list[str] = []
        for name, source in host_sources:
            # Only inject into a host that is already CLEAN for this signal, so a
            # detection is attributable to the injection, not the host.
            if signal in _scan_source(name, source):
                continue
            injected += 1
            used_hosts.append(name)
            if signal in _scan_source(name, source + snippet):
                detected += 1
            if injected >= 5:  # 5 distinct real hosts per signal is enough signal
                break
        recall_rows.append({
            "signal": signal,
            "injected": injected,
            "detected": detected,
            "recall": detected / injected if injected else None,
            "hosts": used_hosts,
        })

    # ── Noise / FP-candidate rate on unmodified real code ────────────────────
    from collections import Counter
    signal_counts: Counter[str] = Counter()
    total_lines = 0
    files_scanned = 0
    for name, source in host_sources:
        total_lines += source.count("\n") + 1
        files_scanned += 1
        for sig in _scan_source(name, source):
            signal_counts[sig] += 1

    return {
        "host_count": len(host_sources),
        "total_lines": total_lines,
        "recall_rows": recall_rows,
        "recall_overall": (
            sum(r["detected"] for r in recall_rows) / sum(r["injected"] for r in recall_rows)
            if sum(r["injected"] for r in recall_rows) else None
        ),
        "noise_by_signal": dict(sorted(signal_counts.items())),
        "noise_findings_per_kloc": (
            sum(signal_counts.values()) / (total_lines / 1000) if total_lines else 0.0
        ),
    }


def main() -> int:
    res = run()
    print("ACI independent evaluation (host corpus: Python standard library)")
    print("=" * 64)
    print(f"host files: {res['host_count']}  |  total lines: {res['total_lines']}")
    print("\nRecall via mutation (smell injected into real, signal-clean host code):")
    for r in res["recall_rows"]:
        pct = f"{r['recall'] * 100:.0f}%" if r["recall"] is not None else "n/a"
        print(f"  {r['signal']:30s} {r['detected']}/{r['injected']} ({pct})")
    overall = res["recall_overall"]
    print(f"  {'OVERALL':30s} {overall * 100:.0f}%" if overall is not None else "  OVERALL n/a")
    print("\nNoise / FP-candidate rate on UNMODIFIED stdlib (each = a finding to review):")
    if res["noise_by_signal"]:
        for sig, count in res["noise_by_signal"].items():
            print(f"  {sig:30s} {count} file(s)")
    else:
        print("  (no findings on the unmodified stdlib corpus)")
    print(f"  findings per 1k lines: {res['noise_findings_per_kloc']:.2f}")
    print("=" * 64)
    # The gate is on independent recall; noise is reported for human precision review.
    gaps = [r for r in res["recall_rows"] if r["recall"] is not None and r["recall"] < 1.0]
    if gaps:
        print("INDEPENDENT RECALL GAPS:")
        for g in gaps:
            print(f"  - {g['signal']} ({g['detected']}/{g['injected']})")
    return 1 if gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
