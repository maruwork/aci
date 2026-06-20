"""ACI taint-rule precision/recall evaluation harness.

G3 proved the bundled semgrep taint-mode rules *fire* on a source->sink flow for
JS and Python. "Fires" is not "is precise". This harness measures the two numbers
that turn a detection claim into an evidence claim, mirroring
``aci_independent_eval.py`` but for the orchestrated taint lane:

1. **Recall (positive flows)** — labelled cases where untrusted input genuinely
   reaches a dangerous sink (direct, one-hop, multi-hop, several sink kinds).
   A taint rule must fire. recall = detected / positives.

2. **False-positive rate (control flows)** — labelled cases that look similar but
   carry **no** real source->sink flow: a constant fed to the sink, a tainted
   value that never reaches the sink, a source with no dangerous sink. A taint
   rule must **not** fire. This is the precision counterpart and the old
   Phase-3 closure criterion ("constant-flow control set produces no false
   positive").

Only taint-mode findings are counted (evidence_ref carries ``taint-``); the
pattern rules (e.g. ``js-eval``) fire on any ``eval`` and are intentionally
ignored here -- they are a different, lower-confidence signal.

All cases are written as distinct files into one temp dir and scanned with a
single semgrep invocation, then attributed back by filename, so the harness pays
semgrep's cold start once. Skips cleanly when semgrep is not installed; CI's
Linux job installs semgrep so the gate runs there.

    python shared/tools/aci_taint_eval.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "shared" / "python"))

try:
    from aci.aci_analyzer_execution import run_analyzer  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - direct-source layout
    from aci_analyzer_execution import run_analyzer  # type: ignore[no-redef]


# Each case: (case_id, filename, expect_taint, source).
# expect_taint is a SEMANTIC label decided independently of the rules: True iff
# untrusted input actually reaches a code-execution sink in this snippet.
_CASES: tuple[tuple[str, str, bool, str], ...] = (
    # ── Python positives: untrusted input reaches a sink ─────────────────────
    ("py_pos_direct", "py_pos_direct.py", True,
     "from flask import request\n"
     "def h():\n    return eval(request.args.get('c'))\n"),
    ("py_pos_var", "py_pos_var.py", True,
     "from flask import request\n"
     "def h():\n    code = request.args.get('c')\n    return eval(code)\n"),
    ("py_pos_twohop", "py_pos_twohop.py", True,
     "from flask import request\n"
     "def h():\n    a = request.args.get('c')\n    b = a\n    return eval(b)\n"),
    ("py_pos_form_exec", "py_pos_form_exec.py", True,
     "from flask import request\n"
     "def h():\n    code = request.form.get('c')\n    exec(code)\n"),
    ("py_pos_input_ossystem", "py_pos_input_ossystem.py", True,
     "import os\n"
     "def h():\n    cmd = input()\n    os.system(cmd)\n"),

    # ── Python controls: NO real source->sink flow (must not fire) ───────────
    ("py_neg_constant", "py_neg_constant.py", False,
     "def h():\n    return eval('1 + 1')\n"),
    ("py_neg_constvar", "py_neg_constvar.py", False,
     "def h():\n    code = 'print(1)'\n    return eval(code)\n"),
    ("py_neg_source_no_sink", "py_neg_source_no_sink.py", False,
     "from flask import request\n"
     "def h():\n    code = request.args.get('c')\n    print(code)\n"),
    ("py_neg_sink_literal_arg", "py_neg_sink_literal_arg.py", False,
     "from flask import request\n"
     "def h():\n    tainted = request.args.get('c')\n    log(tainted)\n    return eval('safe')\n"),

    # ── JavaScript positives ─────────────────────────────────────────────────
    ("js_pos_direct", "js_pos_direct.js", True,
     "function h(req){ return eval(req.query.x); }\n"),
    ("js_pos_var", "js_pos_var.js", True,
     "function h(req){ const c = req.query.x; return eval(c); }\n"),
    ("js_pos_body_func", "js_pos_body_func.js", True,
     "function h(req){ const c = req.body.y; return new Function(c); }\n"),
    ("js_pos_argv", "js_pos_argv.js", True,
     "function h(){ const c = process.argv[2]; return eval(c); }\n"),

    # ── JavaScript controls (must not fire) ──────────────────────────────────
    ("js_neg_constant", "js_neg_constant.js", False,
     "function h(){ return eval('1+1'); }\n"),
    ("js_neg_constvar", "js_neg_constvar.js", False,
     "function h(){ const c = 'safe'; return eval(c); }\n"),
    ("js_neg_source_no_sink", "js_neg_source_no_sink.js", False,
     "function h(req, res){ const c = req.query.x; return res.send(c); }\n"),
)


def _taint_hits(scratch: Path) -> set[str]:
    """Filenames that produced a taint-mode finding from the semgrep lane."""
    result = run_analyzer("semgrep", scratch, 0)
    if result.runtime_state != "executed":
        raise RuntimeError(f"semgrep lane did not execute cleanly: {result.runtime_state}: {result.stderr!r}")
    hits: set[str] = set()
    for finding in result.findings:
        if "taint-" in (finding.evidence_ref or ""):
            hits.add(Path(finding.target_file).name)
    return hits


def run() -> dict | None:
    """Return the measured numbers, or None if semgrep is not installed."""
    if shutil.which("semgrep") is None:
        return None

    scratch = Path(tempfile.mkdtemp(prefix="aci_taint_eval_"))
    try:
        for _cid, filename, _expect, source in _CASES:
            (scratch / filename).write_text(source, encoding="utf-8")
        hits = _taint_hits(scratch)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    rows: list[dict] = []
    for cid, filename, expect, _source in _CASES:
        fired = filename in hits
        rows.append({
            "case": cid,
            "expect_taint": expect,
            "fired": fired,
            # outcome from the rule's perspective
            "true_positive": expect and fired,
            "false_negative": expect and not fired,
            "false_positive": (not expect) and fired,
            "true_negative": (not expect) and not fired,
        })

    positives = [r for r in rows if r["expect_taint"]]
    negatives = [r for r in rows if not r["expect_taint"]]
    tp = sum(r["true_positive"] for r in rows)
    fp = sum(r["false_positive"] for r in rows)
    return {
        "rows": rows,
        "positives": len(positives),
        "negatives": len(negatives),
        "recall": tp / len(positives) if positives else None,
        "false_positive_rate": fp / len(negatives) if negatives else None,
        "precision": tp / (tp + fp) if (tp + fp) else None,
        "false_negatives": [r["case"] for r in rows if r["false_negative"]],
        "false_positive_cases": [r["case"] for r in rows if r["false_positive"]],
    }


def main() -> int:
    res = run()
    if res is None:
        print("semgrep not installed; taint evaluation skipped.")
        return 0

    print("ACI taint-rule evaluation (orchestrated semgrep taint lane)")
    print("=" * 64)
    print(f"positive flows: {res['positives']}  |  control flows: {res['negatives']}")
    print("\nPer-case outcome (fired = a taint-mode rule matched):")
    for r in res["rows"]:
        want = "should-fire " if r["expect_taint"] else "must-not-fire"
        mark = "ok " if (r["expect_taint"] == r["fired"]) else "XX "
        print(f"  {mark}{r['case']:24s} {want}  fired={str(r['fired']).lower()}")

    recall = res["recall"]
    fpr = res["false_positive_rate"]
    prec = res["precision"]
    print("")
    print(f"recall (positives detected):     {recall * 100:.0f}%" if recall is not None else "recall: n/a")
    print(f"false-positive rate (controls):  {fpr * 100:.0f}%" if fpr is not None else "fp-rate: n/a")
    print(f"precision:                       {prec * 100:.0f}%" if prec is not None else "precision: n/a")
    print("=" * 64)

    failures = []
    if res["false_negatives"]:
        failures.append("RECALL GAPS (positive flow missed): " + ", ".join(res["false_negatives"]))
    if res["false_positive_cases"]:
        failures.append("FALSE POSITIVES (control flow fired): " + ", ".join(res["false_positive_cases"]))
    for line in failures:
        print(line)
    # Gate: every control must stay silent (precision), and recall must be perfect
    # on this curated set. Either failure is a real regression worth blocking.
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
