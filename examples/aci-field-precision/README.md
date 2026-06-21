# ACI field-precision evidence pack

The in-repo validation scorecard reports **100% recall / 0 false positives** — but
on fixtures authored alongside the detectors. This pack is the **independent,
field** counterpart: ACI's native-static lane run over **real third-party code**,
with **every counted finding human-adjudicated against the actual source**.

It is the labeled real corpus that `shared/tools/aci_precision_review_pack.py`
named as the thing blocking an honest precision claim. The contrast pack in
[`dev-code/`](dev-code/README.md) repeats the measurement on actively-developed
code — read both; the difference between them is the real story.

## Method

- **Corpus** (native lane, `--scope-mode source-only`) — 10 mature, widely
  reviewed Python libraries, **276 findings adjudicated**:
  `click 8.1.8`, `jinja2 3.1.6`, `attrs 25.4.0`, `packaging 26.0`,
  `pyyaml 6.0.3`, `pluggy 1.6.0`, `werkzeug @1b00618`, `flask @36e4a82`,
  `rich 14.3.3`, `pygments 2.19.2`.
- **Pipeline** (existing maintainer rails, no new tooling):
  `aci_corpus_harness.py` → findings with fingerprints →
  `aci_precision_benchmark.py` over the human labels in `labels.json`. For the
  larger packages a stratified per-CI-ID sample was adjudicated (capped per CI-ID
  to keep the label set diverse); smaller ones were adjudicated in full.
- **Adjudication** — each counted finding was judged by reading ~20 lines around
  the cited location on two independent axes:
  - **detection correctness** (`label`): does the flagged construct genuinely
    have the property the signal claims?
  - **review-worthiness** (`review_worthy`): would a competent maintainer of this
    mature library reasonably act on it? (a finding can be a true positive *and*
    not review-worthy).

## Headline results (mature libraries, n=276)

- **Detection precision: 70%**
- **Review-worthiness: 3%**

| detector | precision | n | note |
|---|---:|--:|---|
| CI-06 magic number | 100% | 14 | exact literals |
| CI-18 param cluster | 100% | 19 | exact argument counts |
| CI-03 TODO/HACK | 96% | 28 | text markers |
| CI-02 long/tangled | 95% | 42 | inherently complex lexers/parsers/renderers |
| CI-23 field drift | 88% | 16 | `**kwargs` option APIs (idiomatic) |
| CI-05 copy-paste | 86% | 21 | mostly idiomatic parallel structures |
| CI-21 broad except | 75% | 52 | FPs on handlers that log / re-raise |
| CI-14 security | 35% | 23 | FPs on lexer `url=` metadata & docstring `http://` text |
| CI-22 resource | 33% | 15 | FPs where the resource is caller-managed / `communicate()`-drained |
| CI-07 unused/dead | 23% | 13 | FPs on symbols reached via module `__getattr__` |
| CI-20 scattered const | 0% | 6 | per-lexer grammar regex fragments, not owned constants |
| CI-04 god class | 0% | 21 | cohesion clustering misfires on cohesive classes — **every one wrong** |

On finished, heavily-reviewed libraries, most of what ACI flags is idiomatic and
not worth acting on. **3% review-worthiness means "ACI on a polished library is
mostly noise" — not "ACI is mostly noise."**

## The two honest divergences from the curated scorecard

1. **Curated 0-FP → field 30% FP.** The fixture scorecard overstates precision
   because it grades clean, purpose-built code. Real code triggers systematic
   false positives — above all **CI-04's cohesion clustering**, which labels
   large-but-cohesive classes (a Jinja2 `CodeGenerator`, a `flask.App`, a
   Pygments lexer, an `httpx.URL` value object) as "unrelated responsibility
   groups". On 21 mature-code CI-04 findings it was wrong **every single time**.
2. **Review-worthiness is ~3%** for a maintainer of mature code. ACI flags
   structural smells that are idiomatic or intentional in these libraries
   (a library's own bytecode-cache `pickle.load`; capability-probe
   `except Exception: return False`; inherently complex parser/lexer functions;
   lexer `url=` homepage metadata). On *mature* code ACI is mostly noise — by
   design it surfaces structure, and mature structure is usually deliberate.

## Honest caveats (this is evidence, not a verdict)

- n = 276 findings across 10 packages; directionally strong, not statistically
  tight. Larger packages were stratified-sampled per CI-ID, not adjudicated in
  full.
- Python + native lane only; external-analyzer lanes are not measured here.
- "Review-worthy" is judged for *mature third-party libraries*. On actively
  developed code a much higher share is actionable — see `dev-code/`.
- Adjudication is a careful single-rubric review, not multi-reviewer consensus.

## How this fed back: balancing the whole tool

The right response to "CI-04 is 0%" is not to tunnel-fix the worst detector but
to **balance the whole tool** so every detector's standing matches its measured
field reliability. Two layers already carried most of that balance, and a small
calibration closed the rest:

- **Gate layer.** The default `severity_threshold` is `high` and the gate ranks by
  *severity*, so every field-weak structural detector (CI-04/05/22, low/medium
  severity) is **advisory by default** — it cannot fail a build.
- **Confidence layer.** CI-04 already emitted `CONFIDENCE_LOW` (matching its 0%
  field precision); CI-14/CI-03 emit `HIGH` where precision is high.
- **Default selection.** A native detector runs in the **default** scan only if
  ACI is confident (`>= MEDIUM`) in at least one of its signals; wholly
  low-confidence detectors (CI-04, CI-05, CI-06, CI-18, CI-23) are **opt-in**
  (`full` profile only). CI-04 still has value on first-party code under active
  change, so it is kept available-but-opt-in rather than removed.

The mandatory `detection_disclosure` on every report ("detection is not 100%")
is backed by these measured numbers.

Files: `labels.json` (the adjudicated dataset), `findings.json` (portable
records), `benchmark.md` (an `aci_precision_benchmark.py` report on the initial
6-package subset). Contrast on actively-developed code: `dev-code/`.
