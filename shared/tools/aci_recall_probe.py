"""ACI recall probe.

The precision scorecard answers "are the findings real?". This answers the
other half: "what real smells does ACI miss?". For each detector it runs a
catalog of harder, realistic positive variants (not the easy planted cases)
and reports which are detected and which slip through.

A miss is not automatically a bug: some are deliberate precision/recall
trade-offs (tagged ``known-limit``). Untagged misses are genuine recall gaps
worth a look. Run for a human report:

    python shared/tools/aci_recall_probe.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import shutil

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKSPACE_ROOT = _REPO_ROOT / "workspace"
sys.path.insert(0, str(_REPO_ROOT / "shared" / "python"))

try:
    from aci.aci_scan import scan_target  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - direct-source layout
    from aci_scan import scan_target  # type: ignore[no-redef]

# Each probe: (label, expected_signal, {filename: source}, known_limit_reason|None)
PROBES: list[tuple[str, str, dict[str, str], str | None]] = [
    # ── CI-13 circular import: cycle sizes and entry styles ──────────────
    ("CI13 two-node cycle", "CI13_CIRCULAR_IMPORT",
     {"a.py": "from b import fb\ndef fa(): return fb()\n",
      "b.py": "from a import fa\ndef fb(): return fa()\n"}, None),
    ("CI13 three-node cycle", "CI13_CIRCULAR_IMPORT",
     {"a.py": "from b import fb\ndef fa(): return fb()\n",
      "b.py": "from c import fc\ndef fb(): return fc()\n",
      "c.py": "from a import fa\ndef fc(): return fa()\n"}, None),
    ("CI13 import-module form", "CI13_CIRCULAR_IMPORT",
     {"a.py": "import b\ndef fa(): return b.fb()\n",
      "b.py": "import a\ndef fb(): return a.fa()\n"}, None),

    # ── CI-05 copy-paste: structural variants ────────────────────────────
    ("CI05 exact duplicate", "CI05_COPY_PASTE_CODE",
     {"x.py": "def f(a,b):\n    r=a*b\n    r+=a\n    r-=b\n    if r>0:\n        r*=2\n    return r\n",
      "y.py": "def f(a,b):\n    r=a*b\n    r+=a\n    r-=b\n    if r>0:\n        r*=2\n    return r\n"}, None),
    ("CI05 renamed near-duplicate", "CI05_COPY_PASTE_CODE",
     {"x.py": "def compute(a,b):\n    r=a*b\n    r+=a\n    r-=b\n    if r>0:\n        r*=2\n    return r\n",
      "y.py": "def tally(c,d):\n    t=c*d\n    t+=c\n    t-=d\n    if t>0:\n        t*=2\n    return t\n"}, None),
    ("CI05 clone with one inserted statement", "CI05_COPY_PASTE_CODE",
     {"x.py": "def compute(a,b):\n    r=a*b\n    r+=a\n    r-=b\n    if r>0:\n        r*=2\n    return r\n",
      "y.py": "def tally(c,d):\n    t=c*d\n    t+=c\n    z=0\n    t-=d\n    if t>0:\n        t*=2\n    return t\n"},
     "structure-exact signature; statement insertion is a documented recall limit"),
    ("CI05 clone with reordered statements", "CI05_COPY_PASTE_CODE",
     {"x.py": "def compute(a,b):\n    r=a*b\n    r+=a\n    r-=b\n    if r>0:\n        r*=2\n    return r\n",
      "y.py": "def tally(c,d):\n    t=c*d\n    t-=d\n    t+=c\n    if t>0:\n        t*=2\n    return t\n"},
     "structure-exact signature; statement reordering is a documented recall limit"),

    # ── CI-07 dead private symbol: shapes ────────────────────────────────
    ("CI07 dead private function", "CI07_UNUSED_PRIVATE_SYMBOL",
     {"m.py": "def pub(): return 1\ndef _dead(x): return x+1\n"}, None),
    ("CI07 dead private class", "CI07_UNUSED_PRIVATE_SYMBOL",
     {"m.py": "def pub(): return 1\nclass _Dead:\n    def go(self): return 2\n"}, None),
    ("CI07 mutually-dead pair", "CI07_UNUSED_PRIVATE_SYMBOL",
     {"m.py": "def pub(): return 1\ndef _a(): return _b()\ndef _b(): return 2\n"}, None),

    # ── CI-22 resource leak: paths ───────────────────────────────────────
    ("CI22 dropped handle", "CI22_RESOURCE_CLEANUP_GAP",
     {"r.py": "def read(p):\n    f=open(p)\n    return f.readline()\n"}, None),
    ("CI22 close only on success path", "CI22_RESOURCE_CLEANUP_GAP",
     {"r.py": "def read(p):\n    f=open(p)\n    data=f.read()\n    f.close()\n    return data\n"},
     "bare .close() counts as managed; exception-path leak needs flow analysis"),

    # ── CI-26 race hazard: mutation forms ────────────────────────────────
    ("CI26 unguarded rebind", "CI26_RACE_HAZARD",
     {"m.py": "counter=0\ndef bump():\n    global counter\n    counter+=1\n    return counter\n"}, None),
    ("CI26 lazy-init guard (should NOT count as race)", "CI26_RACE_HAZARD",
     {"m.py": "_c=None\ndef get():\n    global _c\n    if _c is None:\n        _c={}\n    return _c\n"},
     "lazy-init is intentionally excluded; this probe is expected to MISS"),

    # ── CI-23 contract drift: kwargs access forms ────────────────────────
    ("CI23 kwargs subscript", "CI23_CONTRACT_FIELD_DRIFT",
     {"c.py": "def build(**kw):\n    return kw['host'], kw['port']\n"}, None),
    ("CI23 kwargs.get", "CI23_CONTRACT_FIELD_DRIFT",
     {"c.py": "def build(**kw):\n    return kw.get('host'), kw.get('port')\n"}, None),

    # ── CI-25 nondeterminism: call forms ─────────────────────────────────
    ("CI25 naive datetime.now", "CI25_ENVIRONMENT_DRIFT",
     {"d.py": "import datetime\ndef s(): return datetime.now()\n"}, None),
    ("CI25 random.random", "CI25_ENVIRONMENT_DRIFT",
     {"d.py": "import random\ndef s(): return random.random()\n"}, None),

    # ── CI-14 security: forms ────────────────────────────────────────────
    ("CI14 eval call", "CI14_DYNAMIC_CODE_EXECUTION",
     {"s.py": "def r(c): return eval(c)\n"}, None),
    ("CI14 genuine plaintext endpoint", "CI14_INSECURE_HTTP",
     {"s.py": "URL='http://api.acme-corp.com/v1'\ndef e(): return URL\n"}, None),

    # ── CI-04 god class: composition ─────────────────────────────────────
    ("CI04 god class via many methods, two clusters", "CI04_GOD_CLASS",
     {"g.py": "class M:\n    def __init__(self):\n        self.a=0\n        self.b=0\n"
      + "".join(f"    def ga{i}(self): return self.a+{i}\n" for i in range(9))
      + "".join(f"    def gb{i}(self): return self.b+{i}\n" for i in range(9))}, None),
]


def _signals(files: dict[str, str]) -> set[str]:
    _WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="aci_recall_probe_", dir=_WORKSPACE_ROOT))
    d = scratch / "probe"
    d.mkdir()
    try:
        for name, body in files.items():
            (d / name).write_text(body, encoding="utf-8")
        report = scan_target(d, "full", "core-only", include_external_analyzers=False)
        return {item["signal"] for item in report["findings"]}
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def run() -> dict:
    rows = []
    for label, expected, files, known_limit in PROBES:
        detected = expected in _signals(files)
        rows.append({"label": label, "expected": expected, "detected": detected,
                     "known_limit": known_limit})
    # A probe tagged known-limit is EXPECTED to miss; an untagged miss is a gap.
    real = [r for r in rows if r["known_limit"] is None]
    detected_real = [r for r in real if r["detected"]]
    gaps = [r for r in real if not r["detected"]]
    surprises = [r for r in rows if r["known_limit"] and r["detected"]]
    return {
        "rows": rows,
        "real_total": len(real),
        "real_detected": len(detected_real),
        "recall": len(detected_real) / len(real) if real else 1.0,
        "gaps": gaps,
        "surprises": surprises,
    }


def main() -> int:
    res = run()
    print("ACI recall probe (harder positive variants)")
    print("=" * 60)
    for r in res["rows"]:
        if r["known_limit"]:
            mark = "·known-limit (miss expected)" if not r["detected"] else "·known-limit BUT DETECTED"
        else:
            mark = "OK" if r["detected"] else "*** RECALL GAP ***"
        print(f"  [{'HIT' if r['detected'] else 'miss'}] {r['label']:48s} {mark}")
    print("=" * 60)
    print(f"recall on real (untagged) variants: {res['real_detected']}/{res['real_total']} "
          f"({res['recall'] * 100:.0f}%)")
    if res["gaps"]:
        print("RECALL GAPS:")
        for g in res["gaps"]:
            print(f"  - {g['label']} ({g['expected']})")
    return 1 if res["gaps"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
