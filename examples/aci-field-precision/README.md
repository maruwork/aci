# ACI field-precision evidence pack (2026-06-20)

The in-repo validation scorecard reports **100% recall / 0 false positives** — but
on fixtures authored alongside the detectors. This pack is the **independent,
field** counterpart: ACI's native-static lane run over **real, mature third-party
code**, with **every finding human-adjudicated against the actual source**.

It is the labeled real corpus that `shared/tools/aci_precision_review_pack.py`
named as the thing blocking an honest precision claim.

## Method

- **Corpus** (native lane only, `--scope-mode source-only`, ~45k LOC):
  `click==8.1.8`, `jinja2==3.1.6`, `attrs==25.4.0`, `packaging==26.0`,
  `pyyaml==6.0.3`, `pluggy==1.6.0` — mature, widely-reviewed packages where the
  expected true-positive *and* the expected actionability are low, so any
  high-density signal is a precision flag.
- **Pipeline** (existing maintainer rails, no new tooling):
  `aci_corpus_harness.py` → 126 findings with fingerprints →
  `aci_precision_benchmark.py` over the human labels in `labels.json`.
- **Adjudication**: each of the 126 findings was judged by reading ~20 lines
  around the cited location, on two independent axes:
  - **detection correctness** (`label`): does the flagged construct genuinely
    have the property the signal claims? (`true-positive` / `false-positive` /
    `skip`)
  - **review-worthiness** (`review_worthy`): would a competent maintainer of this
    mature library reasonably act on it? (a finding can be a true positive *and*
    not review-worthy — e.g. an inherently complex code-generation function).

## Headline results

- **Detection precision: 76%** (95 true / 125 adjudicated; 1 skip).
- **Review-worthiness: 4%** (5 of 126) on mature libraries.

| CI-ID | precision | n | note |
|---|---:|--:|---|
| CI-14 (security) | 100% | 7 | every shell=True/pickle/eval flagged was real |
| CI-18 (param cluster) | 100% | 16 | argument counts are exact |
| CI-03 (TODO/HACK) | 100% | 12 | text markers, near-exact |
| CI-25 / CI-26 | 100% | 2 | small n |
| CI-02 (long/complex) | 92% | 26 | 2 flat combinatorial fns mis-flagged as "tangled" |
| CI-21 (broad except) | 75% | 36 | FPs on handlers that re-raise / delegate to a re-raiser |
| CI-23 (field drift) | 75% | 4 | small n |
| CI-22 (resource cleanup) | 50% | 6 | FPs where the resource is handed to the caller or closed in `finally` |
| CI-05 (copy-paste) | 40% | 5 | FPs on trivial boilerplate / re-exports |
| CI-04 (god class) | **0%** | 11 | **systematically wrong on cohesive visitor/parser/registry/value-object classes** |
| CI-07 (unused private) | 0% | 1 | missed a dynamic `__import__("...")` string reference |

## The two honest divergences from the curated scorecard

1. **Curated 0-FP → field 24% FP.** The fixture scorecard overstates precision
   because it grades clean, purpose-built code. Real idiomatic code triggers
   systematic false positives — above all **CI-04's cohesion clustering**, which
   labels large-but-cohesive classes (a Jinja2 `CodeGenerator` visitor, a YAML
   `Scanner`, a pluggy `PluginManager`, a `click.Command`) as "unrelated
   responsibility groups". On this corpus CI-04 was wrong **every single time**.
2. **Even true positives are ~96% not worth acting on** for a maintainer of
   mature code. ACI flags structural smells that are idiomatic or intentional in
   these libraries (a library's own bytecode-cache `pickle.load`; capability-probe
   `except Exception: return False`; inherently complex parser/emitter functions;
   internal multi-parameter constructors). On a *mature* codebase ACI is mostly
   noise — by design it surfaces structure, and mature structure is usually a
   deliberate choice.

## Honest caveats (this is evidence, not a verdict)

- n = 126 findings on 6 Python packages; not a large statistical sample.
- Python + native lane only; external-analyzer lanes are not measured here.
- "Review-worthy" is judged for *mature third-party libraries*. On an actively
  evolving first-party codebase a materially higher share would be actionable —
  do not read 4% as ACI's value on your own in-progress code.
- Adjudication is a careful single-rubric review (one maintainer pass), not
  multi-reviewer consensus.

## What the evidence demands (recorded, not yet acted on)

- **CI-04 (0% field precision)** is the clearest defect: the LCOM "unrelated
  responsibility groups" heuristic mis-classifies cohesive many-method classes.
  It should be retuned, down-ranked, or threshold-raised before CI-04 is trusted
  on real OO code.
- **CI-05 (40%)** and **CI-22 (50%)** need precision work (trivial-similarity
  suppression; recognising caller-managed / `finally`-closed resources).
- The mandatory `detection_disclosure` on every report ("detection is not 100%")
  is now backed by a measured number: **~76% native detection precision on real
  third-party code, and ~4% review-worthiness on mature code.**

Files: `labels.json` (the adjudicated dataset), `benchmark.md` (the
`aci_precision_benchmark.py` report), `findings.json` (portable finding records).
