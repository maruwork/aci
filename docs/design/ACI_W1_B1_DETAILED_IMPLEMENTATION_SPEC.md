# ACI W1 B1 Detailed Implementation Spec

Status: Active
Parent task: `ACI-W1`
Active bundle: `ACI-W1-B1`

## Purpose

Fix the implementation shape for precision-evidence maintenance tightly enough
that different implementers converge on the same code structure, behavior, and
verification surface.

This document is intentionally narrower than the repo-local execution design.
It covers only the current active bundle.

## Read Order

1. `docs/roadmap/ACI_COMPLETION_POLICY.md`
2. `docs/roadmap/ACI_REPO_LOCAL_EXECUTION_PLAN.md`
3. `docs/roadmap/ACI_REPO_LOCAL_CHECKPOINTS.md`
4. `docs/tasks/ACI_REPO_LOCAL_TASK_BREAKDOWN.md`
5. `docs/tasks/ACI_TASK_W1_PRECISION_EVIDENCE_MAINTENANCE.md`
6. `docs/tasks/ACI_W1_B1_IMPLEMENTATION_PLAN.md`
7. this file

## 1. Success Subject

The success subject for `ACI-W1-B1` is not "better precision" in the abstract.

It is this narrower claim:

- the review-pack workflow remains reproducible
- prior human labels survive safe reruns
- unlabeled rows remain explicitly unlabeled
- benchmark outputs remain precision-only and do not drift into recall claims

If a change does not materially improve one of those four points, it is outside
this bundle.

## 2. Non-Negotiable Semantics

These semantics are fixed and may not be reinterpreted during implementation.

### 2.1 Label Meaning

- blank `label` means `not reviewed yet`
- blank `label` must not be counted as `false-positive`
- `skip` means reviewed but excluded from precision numerator/denominator
- only `true-positive` and `false-positive` contribute to labeled precision

### 2.2 Scope Honesty

- benchmark output may claim labeled precision only
- benchmark output must not imply measured recall
- workflow docs must continue to state that recall needs a separate labeled
  workflow

### 2.3 Review-Subset Stability

- when `max_per_ci` is omitted, the full finding list is exported
- when `max_per_ci` is set, selection is deterministic
- deterministic means:
  - findings are grouped by `ci_id`
  - within a `ci_id`, findings are grouped by `project`
  - projects are traversed in lexical order
  - findings within each project are traversed by the existing `_finding_sort_key`
  - one row per project is taken per round until the cap is reached or rows are
    exhausted

### 2.4 Label Preservation Boundary

- labels are preserved by `fingerprint`
- duplicate fingerprints in an existing label file are an error
- rows for fingerprints that no longer appear in the current sampled findings
  are not copied into the new `labels.json`
- those stale fingerprints may still be reported by the benchmark as
  `unknown_label_fingerprints` when benchmark input includes them

## 3. Target Surface

Only these files are in the primary change window for this bundle:

| File | Status | Allowed Change |
|---|---|---|
| `docs/PRECISION_REVIEW_WORKFLOW.md` | primary | wording, steps, cautions, command guidance |
| `shared/tools/aci_precision_review_pack.py` | primary | pack-generation behavior and README generation |
| `shared/tools/aci_precision_benchmark.py` | primary | benchmark loading, aggregation, and markdown rendering |
| `shared/tests/test_aci_precision_review_pack.py` | primary | regression tests for pack behavior |
| `shared/tests/test_aci_precision_benchmark.py` | primary | regression tests for benchmark behavior |
| `docs/roadmap/ACI_AUDIT_TOOL_COMPLETION_INVENTORY_2026-06-18.md` | writeback-only | status/evidence wording when meaning changes |

## 4. Non-Target Surface

These files are read-only for `ACI-W1-B1` unless a contradiction makes progress
impossible:

| File | Why non-target |
|---|---|
| `shared/tools/aci_corpus_harness.py` | corpus collection is not the semantics bottleneck in this bundle |
| `shared/tools/aci_precision_labelset.py` | label template shape already follows finding rows and existing labels |
| `shared/python/` | detector/runtime behavior is outside precision-workflow maintenance |
| `docs/CI_REFERENCE.md` | CI semantics are not being redefined here |

If one of these would need to change, stop and reclassify the work.

## 5. Required Function-Level Contract

Implementation must preserve these function responsibilities.

### 5.1 `shared/tools/aci_precision_review_pack.py`

#### `_load_existing_label_rows(path)`

- input:
  - optional JSON file path
- required behavior:
  - return `[]` when the path is missing or not provided
  - require top-level JSON list
  - require each item to be an object
  - require each item to contain a non-empty `fingerprint`
  - normalize each row to:
    - `fingerprint`
    - `label`
    - `notes`
- must not:
  - silently coerce invalid shapes into empty rows
  - preserve arbitrary extra keys

#### `_rows_by_fingerprint(rows)`

- input:
  - normalized row list
- required behavior:
  - return one dict entry per fingerprint
  - raise on duplicates
- must not:
  - keep the last duplicate silently

#### `_labeled_rows_by_fingerprint(rows)`

- required behavior:
  - return only rows whose `label` is non-blank after trimming
- must not:
  - treat `" "` as a real label

#### `select_review_findings(findings, max_per_ci=None)`

- required behavior:
  - return copies of rows, not the original dict objects
  - preserve full list order only when `max_per_ci is None`
  - validate `max_per_ci > 0` when provided
  - implement the deterministic round-robin rule from section `2.3`
- must not:
  - randomize selection
  - prioritize by severity or confidence
  - mix CI-IDs during cap application

#### `_review_projection(result, findings, selection_mode=...)`

- required behavior:
  - output a review-specific object with:
    - `projects`
    - `total_findings`
    - `per_ci_id`
    - `findings`
    - `selection_mode`
    - `source_total_findings`
  - derive `samples` from the selected review findings, not the full corpus
- must not:
  - discard `source_total_findings`
  - expose more than five sample rows per CI-ID

#### `build_pack_readme(...)`

- required behavior:
  - report both full corpus finding count and review-subset count
  - state the scope mode, selection mode, label row count, and labeled row count
  - print the exact benchmark refresh command
  - state that blank labels are unlabeled
  - state that the pack is scaffolding rather than publishable evidence
- must not:
  - imply that review-pack existence alone proves completion

#### `write_review_pack(...)`

- required behavior:
  - require flat findings in `corpus_result`
  - create the output directory
  - write exactly these files:
    - `corpus.json`
    - `findings.json`
    - `triage.md`
    - `labels.json`
    - `benchmark.json`
    - `benchmark.md`
    - `README.md`
  - refresh benchmark outputs every run using the current sampled review set and
    the currently labeled rows
  - return a summary dict containing:
    - paths
    - `benchmark_written`
    - `selection_mode`
    - `review_finding_count`
    - `label_row_count`
    - `labeled_row_count`
- must not:
  - skip benchmark refresh when zero rows are labeled
  - write benchmark based on the full corpus when `max_per_ci` sampling is active

### 5.2 `shared/tools/aci_precision_benchmark.py`

#### `_load_harness_findings(path)`

- required behavior:
  - require top-level object with `findings` list
  - require every finding to have a non-empty `fingerprint`
  - preserve finding rows as dict copies
- must not:
  - accept a corpus summary without flat findings

#### `_load_labels(path, allow_unlabeled=False)`

- required behavior:
  - require top-level list
  - require one non-empty `fingerprint` per row
  - allow blank `label` only when `allow_unlabeled=True`
  - allow only:
    - `true-positive`
    - `false-positive`
    - `skip`
  - normalize rows to `fingerprint`, `label`, `notes`
  - raise on duplicates
- must not:
  - infer unknown labels
  - collapse duplicate rows

#### `benchmark_precision(findings, labels_by_fingerprint)`

- required behavior:
  - partition findings into labeled and unlabeled by fingerprint
  - treat blank labels as unlabeled
  - compute overall TP/FP/skipped counts
  - compute precision as `tp / (tp + fp)` and `None` when denominator is zero
  - produce:
    - `total_findings`
    - `labeled_findings`
    - `unlabeled_findings`
    - `label_coverage`
    - `true_positive`
    - `false_positive`
    - `skipped`
    - `precision`
    - `per_ci_id`
    - `unlabeled_per_ci_id`
    - `unknown_label_fingerprints`
    - `unlabeled_samples`
  - limit per-CI unlabeled samples to the first three sorted rows
  - limit top-level unlabeled samples to the first ten sorted rows
- must not:
  - count `skip` in precision
  - count blank labels as reviewed
  - infer recall or false negatives

#### `to_markdown(result)`

- required behavior:
  - emit sections in this order:
    - title
    - overall counts
    - per-CI precision table
    - unlabeled queue by CI-ID, when present
    - unknown label fingerprints, when present
    - unlabeled sample findings, when present
  - render `n/a` when precision is `None`
- must not:
  - omit the unlabeled queue when unlabeled rows exist
  - rename labeled precision into a generic "quality score"

## 6. Required Output Shapes

### 6.1 `labels.json`

Each row must contain at least:

- `fingerprint`
- `label`
- `notes`
- `ci_id`
- `signal`
- `severity`
- `confidence`
- `project`
- `target_file`
- `line`
- `reason`
- `excerpt`

The field order should remain stable in the current emitted sequence to reduce
diff churn.

### 6.2 `findings.json`

The top-level object must contain:

- `projects`
- `total_findings`
- `per_ci_id`
- `findings`
- `selection_mode`
- `source_total_findings`

`total_findings` refers to the sampled review set, not the full corpus, when
sampling is active.

### 6.3 `benchmark.json`

The JSON must stay precision-centered.
No field named `recall`, `missed_findings`, or equivalent may be added in this
bundle.

## 7. Allowed Refactor Boundary

The implementation may:

- add small private helpers inside the two tool modules
- reorder code for readability
- add narrow comments above non-obvious blocks

The implementation may not:

- introduce new public CLI flags
- change file names in the pack
- change label vocabulary
- move the workflow into packaged runtime code
- widen the task into corpus-harness or detector redesign

## 8. Mandatory Test Matrix

Any implementation under this bundle must keep or add tests proving these cases.

| Case ID | Surface | Input Shape | Expected Result |
|---|---|---|---|
| `W1-T1` | review pack | no existing labels | labels bootstrap with blank label rows and benchmark shows unlabeled findings |
| `W1-T2` | review pack | existing labeled row for sampled fingerprint | label survives rerun and benchmark counts it as labeled |
| `W1-T3` | review pack | `max_per_ci=2` over multiple projects | selected findings follow deterministic round-robin order |
| `W1-T4` | benchmark | TP + FP + skip mix | overall precision and per-CI precision match formula |
| `W1-T5` | benchmark loader | duplicate fingerprint rows | explicit `ValueError` |
| `W1-T6` | benchmark loader | unsupported label text | explicit `ValueError` |
| `W1-T7` | benchmark | blank label row | row remains unlabeled and precision is `None` when no TP/FP exist |
| `W1-T8` | markdown | unlabeled and unknown fingerprint state present | markdown contains unlabeled queue and unknown fingerprint sections |

## 9. Preferred Implementation Order

1. adjust workflow wording if the operator contract is currently ambiguous
2. change `aci_precision_review_pack.py`
3. change `aci_precision_benchmark.py`
4. update tests to make the semantics executable
5. update inventory wording only if the public meaning changed

Do not start by editing the inventory.

## 10. Stop Gates

Stop and reroute if implementation would require any of these:

- adding recall metrics or recall wording
- changing detector/runtime behavior
- changing the review-pack file set
- changing label vocabulary
- changing package/distribution behavior
- touching owner-gated release posture

## 11. Completion Evidence

This detailed spec is satisfied only when:

- code changes remain inside the target surface
- the mandatory test matrix is covered by focused pytest evidence
- workflow docs still state the precision-only boundary honestly
- writeback, if any, points to actual labeled evidence rather than tooling
  existence alone
