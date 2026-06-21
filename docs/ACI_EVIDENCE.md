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

### 2e. Change-review (diff) mode — an operational defect found by testing, then fixed

Testing ACI's *actual* intended use — reviewing a change, not auditing a whole
repo — surfaced a defect that whole-repo testing could not. On **15 real merged
PRs** (textual, poetry, httpx), the old file-level diff mode produced **70
findings, 83% of them >40 lines from any changed line** — pre-existing issues in
touched files. Example: poetry PR #10917 (resolve relative URLs) was told its
`Executor` class is a god class and a function is too long — both untouched by
the PR.

Root cause: `--diff-from` scoped to changed *files*, then scanned them whole.
Fix: **change-aware scoping** — keep a finding only when its flagged construct (a
function/class line span for structural signals, the exact line for line-specific
ones) intersects the lines the change actually touched.

| | findings on the 15 PRs |
|---|---|
| before (file-level) | 70 (83% incidental) |
| after (change-aware) | **8** — each a structural concern the PR modified *inside* |

Reproducible: `examples/aci-field-precision/diff-mode-scan.json`; behaviour locked
by `test_diff_from_scopes_findings_to_changed_lines` and
`test_construct_spans_maps_def_to_end_line`.

### 2f. Baseline stability — a second "only new issues" defect, found and fixed

Asking the same operational question of the *other* "show only new issues"
mechanism — baselining ACI on a legacy codebase — exposed a sibling defect.
Findings are matched to a baseline by fingerprint, but the fingerprint included
the **line number** (and the volatile reason text, e.g. "161 lines"). So a single
unrelated line added above a finding shifted its fingerprint, the baseline no
longer matched it, and it **re-surfaced as "new"** — making the baseline gate
useless on active code.

Verified: the same `except Exception:` handler changed fingerprint
(`e58d2f06…` → `7aa3b0a0…`) after one unrelated comment line was prepended.

Fix: identify a finding by its **enclosing symbol + the flagged line's own
content**, not its line number or the volatile reason. Now the fingerprint is
stable when unrelated edits shift lines, still distinguishes findings in
different functions, and changes only when the flagged code (or its symbol)
actually changes. Locked by `test_fingerprint_is_stable_under_unrelated_line_shifts`,
`test_fingerprint_distinguishes_findings_in_different_symbols`, and
`test_structural_fingerprint_stable_when_construct_grows`. (Migration: existing
baseline/waiver files keyed on the old fingerprints must be regenerated.)

Both "only new issues" paths — diff mode (§2e) and baseline (here) — were broken
by the same root cause: encoding a finding's identity by line number. Both are
now line-shift-stable.

### 2g. diff × baseline interaction — a third defect, found by running the real workflow

Edge-case inspection found nothing more; running the *combined* workflow did.
Simulating real adoption — establish a baseline on `textual`, then walk ~10 real
commits in `--diff-from` + baseline mode — surfaced an interaction defect: each
diff scan reported **353 of 354 baseline findings as "resolved"**. A diff scan
only examines changed files, but resolution was computed against the *whole*
baseline, so every baseline finding in an untouched file looked "gone".

Fix: bound resolution to the files the scan actually examined
(`find_resolved_baseline_entries(..., scanned_files=...)`). A whole-repo scan is
unchanged (all files examined); a diff scan no longer claims findings in
unscanned files are resolved. After the fix the same walk reports 0–1 resolved
per commit (only genuine removals in changed files), and pre-existing findings on
changed code are correctly marked `existing-baseline`, not re-flagged as new.
Locked by `test_resolved_baseline_is_bounded_to_scanned_files` and
`test_diff_scan_does_not_falsely_resolve_unscanned_baseline`.

Three defects total (§2e diff scope, §2f fingerprint stability, this), all in the
"only new issues" workflow, none caught by a green unit-test suite — each surfaced
only by exercising the actual intended use, and the third only by exercising two
features *together*.

### 2h. eslint lane on a real frontend repo — a fourth defect, found by scale

Running the external lanes on a large real repo (`litellm`, 1,892 files) surfaced
a defect in the borrowed JS lane. litellm ships 100 **built/minified** JS files
(Next.js chunks, swagger bundles); ACI's eslint lane linted them, produced **11.8
MB of output (2,125 messages on build artifacts)**, and reported `parse-failure`
— so on any project with a JS frontend, the eslint lane either silently failed or
flooded the report with noise from generated code.

Root cause: the eslint lane did not exclude generated/vendored/minified paths,
even though ACI already excludes them for native detectors. Fix: the bundled
eslint config now `ignores` build output (`**/_next/**`, `**/dist/**`,
`**/*.min.js`, …), and `_has_eslint_source` no longer triggers the lane on
generated-only JS. After the fix, litellm's eslint lane no longer runs on build
artifacts; a project with real source JS still lints it (and ignores its minified
files). Locked by `test_eslint_skips_generated_and_minified_js` and
`test_eslint_lane_ignores_minified_files`.

Four defects now, each found only by exercising real use — the change-review
workflow (§2e), staged baseline adoption (§2f, §2g), and now running a borrowed
lane at real scale.

### 2i. Vendored code in the native lane — a fifth defect, the native twin of §2h

The eslint fix (§2h) prompted the same question of the native lane: does it scan
**vendored** third-party code? Scanning `pip` answered it — `pip/_vendor/` holds
345 bundled files (pygments, rich, six, …), and **280 of pip's 362 native
findings (77%) came from `_vendor/`** — code pip ships but does not own and cannot
fix.

Root cause: the generated/skip path set excluded build and cache dirs but not
vendored ones. Fix: `DEFAULT_GENERATED_PATH_SEGMENTS` now includes `_vendor`,
`vendor`, `vendored`, `third_party`, `site-packages`, etc. After the fix pip
reports 74 findings, **0 from `_vendor`**, while its own code is still scanned.
Locked by `test_vendored_third_party_code_is_not_scanned`.

Five defects, every one found only by exercising real use — and §2h/§2i are the
same defect (scanning code that isn't the project's source) in the two lanes,
found one after the other by asking the same question of each.

### 2j. Closing the root cause behind §2h/§2i — one policy, no drift

§2h and §2i were the *same* defect in two lanes, fixed twice. That repetition was
the real signal: each lane (native discovery, eslint, mypy/codeql file lists,
semgrep) kept its **own** skip set, and they had drifted out of sync. Measuring
the drift directly: the borrowed-analyzer skip sets were each missing ten
segments the native policy already had — `_vendor`, `vendor`, `vendored`,
`third_party`, `site-packages`, `bower_components`, and four cache/build dirs.

At the **report** level this leaked nothing: external findings are already bounded
to the native-discovered file set, so vendored findings were dropped before the
report (verified — raw ruff on a `_vendor`/`vendor`/`third_party` fixture emits 9
findings, 8 are dropped, only the project's own file survives). But the borrowed
tools still *processed* that code: on a pip-scale `_vendor/` tree, handing
hundreds of bundled files to mypy can exhaust the per-analyzer timeout and starve
the project's own code of any findings at all.

The fix is structural, not another patch: the analyzer skip sets are now **derived
from** `DEFAULT_GENERATED_PATH_SEGMENTS` (the single generated-path policy) plus a
few lane-specific extras, so they cannot drift again. A drift-guard test
(`test_borrowed_lane_skip_sets_cover_the_generated_path_policy`) fails if any lane
ever skips less than the policy.

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
