# ACI — Evidence of usefulness

This document collects, in one place, the **measured** data behind ACI's
usefulness claims. Every number here is reproducible from the tools and labeled
datasets committed in this repository; nothing is asserted without an experiment
you can re-run. Where the data is unflattering, it is reported anyway — the point
is an honest picture, not a sales sheet.

**What ACI is:** a Python-native structural/security code auditor plus a
live-verified, multi-language orchestration of best-in-class analyzers
(ruff, semgrep, codeql, eslint, mypy, …). It does not aim to be exhaustive or
perfect; it aims to be *useful where it is used* and *honest about the rest*.

---

## 1. Headline

| Claim | Measured | Evidence |
|---|---|---|
| Useful on code under active development | **36% of findings review-worthy**, 73% detection precision (n=207, 6 projects) | [`examples/aci-field-precision/dev-code/`](../examples/aci-field-precision/dev-code/README.md) |
| Honestly bounded on finished code | 3% review-worthy, 70% precision (n=276, 10 packages) | [`examples/aci-field-precision/`](../examples/aci-field-precision/README.md) |
| Multi-language taint, precision-gated | recall 1.0 / **0 false positives** on a source→sink + control corpus | [`shared/tools/aci_taint_eval.py`](../shared/tools/aci_taint_eval.py) |
| Detectors generalize to untuned real code | **100% mutation recall** on the CPython stdlib | [`shared/tools/aci_independent_eval.py`](../shared/tools/aci_independent_eval.py) |
| Orchestration actually runs | **13/13 analyzers execution-ready, CI-proven** on Linux/Windows/macOS | `.github/workflows/ci.yml` |
| Scales to many projects | **2,546 findings across 35 packages**; ~1,462 from ≈95–100%-precision detectors | [`large-scan-summary.json`](../examples/aci-field-precision/large-scan-summary.json) |

---

## 2. Real-code precision & usefulness (the core evidence)

ACI's findings were measured on **real third-party code**, with **every finding
human-adjudicated by reading the actual source** on two independent axes:

- **Detection precision** — does the flagged construct genuinely have the
  property claimed? (true vs false positive)
- **Review-worthiness** — would a competent maintainer of *that* project actually
  act on it? (a finding can be a true positive yet not worth acting on)

Two corpora were measured, and **the contrast between them is the central
finding**.

### 2a. Mature, finished libraries (the conservative case)

Corpus (10 packages, 276 findings adjudicated): `click 8.1.8`, `jinja2 3.1.6`,
`attrs 25.4.0`, `packaging 26.0`, `pyyaml 6.0.3`, `pluggy 1.6.0`,
`werkzeug @1b00618`, `flask @36e4a82`, `rich 14.3.3`, `pygments 2.19.2`.

- **Detection precision: 70%**
- **Review-worthiness: 3%**

| detector | precision | n | note |
|---|---:|--:|---|
| CI-06 / CI-18 | 100% | 33 | exact literals / argument counts |
| CI-03 TODO/HACK | 96% | 28 | text markers |
| CI-02 long/tangled | 95% | 42 | inherently complex lexers/parsers |
| CI-23 / CI-05 | ~87% | 37 | idiomatic `**kwargs` APIs / parallel structures |
| CI-21 broad except | 75% | 52 | FPs on handlers that log / re-raise |
| CI-14 security | 35% | 23 | FPs on lexer `url=` metadata & docstring text |
| CI-22 resource | 33% | 15 | FPs where the resource is caller-managed |
| CI-07 unused/dead | 23% | 13 | FPs on symbols reached via module `__getattr__` |
| CI-20 / CI-04 | 0% | 27 | lexer regex fragments / cohesion clustering misfires |

On a finished, heavily-reviewed library, most of what ACI flags is idiomatic and
not worth acting on. **3% review-worthiness means "ACI on a polished library is
mostly noise" — not "ACI is mostly noise."**

### 2b. Actively-developed projects (the intended use)

Corpus (6 projects, 207 findings adjudicated): `httpie @5b604c3` (CLI app),
`mkdocs @2862536` (docs tool), `textual @182277f` (TUI framework),
`poetry @cf54a1c` and `pdm @ad49b1d` (packaging tools), `httpx @b5addb6`.

- **Detection precision: 73%**
- **Review-worthiness: 36%** — roughly **12× the mature-library rate**

| detector | precision | review-worthy | n |
|---|---:|---:|--:|
| CI-03 TODO/FIXME/HACK | 100% | 38/40 | 40 |
| CI-02 long/tangled | 96% | 23/28 | 28 |
| CI-18 param cluster | 100% | 3/16 | 16 |
| CI-21 broad except | 71% | 4/31 | 31 |
| CI-05 copy-paste | 70% | 1/23 | 23 |
| CI-14 security | 42% | 1/12 | 12 |
| CI-04 god class | 13% | 2/23 | 23 |

On code still being written, **about a third of ACI's findings are worth acting
on**. The driver is exactly what you'd expect of live code: CI-03 surfaces the
developers' own live reminders ("Refactor and drastically simplify…", "TODO:
this should move into poetry-core"), and CI-02 flags long functions a maintainer
would reasonably consider splitting. (An earlier 2-project sample measured 50%;
the 6-project number is the more honest one — see `dev-code/`.)

### 2c. The finding

**ACI's usefulness depends heavily on code maturity.** It is noisy on finished
libraries (3% review-worthy) and genuinely useful on code under active
development (36%) — which is its intended use. Both numbers are published;
neither alone is the truth.

---

### 2d. Large-N volume scan (35 projects, 2,546 findings) — what scales and what doesn't

Per-finding human adjudication does not scale to thousands by hand, so the
precision/usefulness percentages above are a **483-finding labeled sample**. What
*does* scale, with no adjudication, is **finding volume and distribution**, plus
the yield of the **deterministic high-precision detectors** whose precision is an
established property of the detector (a TODO marker is a TODO; an argument count
is exact). A single scan over **35 real packages** produced **2,546 findings**:

| layer | result | basis |
|---|---|---|
| Raw volume | 2,546 findings across 35 projects (median 34/project) | direct scan, fully reproducible |
| High-precision detectors | **1,462 findings** from CI-02 / CI-03 / CI-18 (≈95–100% precision) | counts are credible without re-judging — precision is a measured detector property |
| Estimated true positives | **≈2,057** (each CI-ID's count × its sample-measured precision) | **extrapolation**, not 2,546 hand-judgments |
| Confirmed weak at scale | CI-04 = 0% (127 findings → ~0 TP), CI-20 = 0% | sample precision applied to scale |

This is honestly an *extrapolation*: 2,546 findings were **not** individually
adjudicated. It scales the credible dimensions (volume, deterministic-detector
yield) while the precision/usefulness rates remain anchored to the 483 hand-judged
findings. A truly rigorous public benchmark would label more — the human-judgment
ceiling is real and is stated, not hidden. Raw per-CI-ID and per-project counts:
`examples/aci-field-precision/large-scan-summary.json`.

## 3. Multi-language source→sink taint, precision-gated

The default scan carries a **closed** semgrep taint-mode baseline (JavaScript +
Python). Its precision is gated by a curated corpus of source→sink **positives**
(direct, one-hop, multi-hop, several sink kinds) and **control** flows that must
stay silent (a constant fed to the sink; a tainted value that never reaches the
sink; a source with no dangerous sink):

- **Recall: 100%** (every real flow caught)
- **False-positive rate: 0%** (every control stayed silent)

The controls are the point: they prove the rules *discriminate* a real flow from
a look-alike, which a bare `eval()`-pattern match cannot. Deeper, broader taint
is borrowed from `codeql` (a database-build → analyze → SARIF pipeline proven
live in a dedicated CI job on a `request.args → eval` data-flow).

Re-run: `python shared/tools/aci_taint_eval.py` (with semgrep installed).

---

## 4. Detectors generalize to code they were never tuned on

The in-repo scorecard grades detectors on fixtures authored alongside them, which
is circular. The independent harness instead injects a known smell into a copy of
a real **CPython standard-library** file verified clean for that signal, on host
code the detectors were never tuned on:

- **Mutation recall: 100%** (CI-14 deserialization, CI-14 shell=True, CI-21
  broad-except, CI-25 env-drift, CI-26 race — 5/5 each)
- Noise on the unmodified stdlib: **1.71 findings per 1k lines**

Re-run: `python shared/tools/aci_independent_eval.py`.

---

## 5. Orchestration breadth (all proven to run)

ACI normalizes 13 best-in-class analyzers into one finding contract. **All 13 are
execution-ready and live-verified in CI** on Linux, Windows, and macOS:

`ruff`, `pyflakes`, `mypy`, `pytest` (Python); `semgrep` (multi-language SAST +
taint); `eslint`, `tsc` (JS/TS); `shellcheck` (shell); `sqlfluff` (SQL);
`osv-scanner`, `trivy` (dependencies/vulns); `gitleaks` (secrets); `codeql`
(multi-language data-flow, opt-in because its per-language DB build is heavy).

Live runs — not parser tests — surfaced and fixed ~12 real invocation bugs that
unit tests could not (e.g. semgrep's `tests/` default-ignore silently scanning
zero files; a 10s version-probe edge; codeql's empty-SARIF query-suite). The CI
installs every tool, so the orchestration is proven end-to-end, not by mock.

---

## 6. Internal validation & engineering (regression guards, not field claims)

- **Curated validation scorecard:** 100% recall / 0 false positives across 25
  ground-truth signals (`shared/tools/aci_validation_scorecard.py`). This proves
  internal consistency and guards against regressions; it is **not** field
  precision (it grades detector-authored fixtures — see §2 for field numbers).
- **805 tests**, 17 native detector modules, 3-OS CI green.
- Every scan report carries a mandatory `detection_disclosure` stating that
  detection is **not 100%** — a clean result is evidence, not proof.

---

## 7. Honest caveats & boundaries (what this evidence does *not* show)

- **Sample sizes are moderate:** n=276 (mature, 10 packages) and n=207 (dev, 6
  projects), all human-adjudicated; larger packages were stratified-sampled per
  CI-ID. Directionally strong, not statistically tight.
- **Python-centric:** native structural and intra-procedural taint depth is
  **Python only**; multi-language depth is borrowed from orchestrated analyzers,
  not natively re-implemented (an explicit non-goal).
- **"Actively-developed" is approximated** by application/tool projects vs
  foundational libraries, not by commit recency. True first-party in-progress
  code (a user's own work) is the closest case still unmeasured here.
- **Adjudication is a single careful rubric pass**, not multi-reviewer consensus.
- **Weakest detector:** CI-04 (god class) scored 0% on mature code; it is
  low-confidence, advisory, and **excluded from the default scan** (it runs only
  in the opt-in `full` profile). Default selection applies one criterion:
  a detector runs by default only if ACI is confident (`>= MEDIUM`) in at least
  one of its signals.

---

## 8. Reproduce every number

| Number | Command (with the named tool installed) |
|---|---|
| Mature-library precision/usefulness | `python shared/tools/aci_corpus_harness.py <pkgs> --include-findings --json out.json` then `aci_precision_benchmark.py` against `examples/aci-field-precision/labels.json` |
| Dev-code precision/usefulness | same pipeline against `examples/aci-field-precision/dev-code/labels.json` |
| Taint precision gate | `python shared/tools/aci_taint_eval.py` |
| Independent recall on stdlib | `python shared/tools/aci_independent_eval.py` |
| Curated scorecard | `python shared/tools/aci_validation_scorecard.py` |
| Orchestration end-to-end | `pytest shared/tests/test_aci_external_analyzer_e2e.py` |

All labeled datasets (`labels.json`, `findings.json`) and per-finding evidence
notes are committed under `examples/aci-field-precision/`, so the adjudication
itself is auditable, not just the totals.
