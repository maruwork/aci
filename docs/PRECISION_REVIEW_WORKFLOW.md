# Precision Review Workflow

Purpose: move ACI precision-evidence work from "tooling exists" to
"review-ready pack exists" without mixing ad hoc reviewer habits into the main
completion claim.

This workflow does not publish a precision number by itself.
It prepares and maintains the review pack that a human reviewer labels.

Current implementation semantics:

- `aci_precision_review_pack.py` always writes `benchmark.json` /
  `benchmark.md` when the pack is generated
- that automatic benchmark is computed over the current sampled review subset in
  `findings.json`, not over the full corpus in `corpus.json`
- blank labels remain `not reviewed yet`; they are visible in the unlabeled
  queue and are not counted as false positives
- rerunning the pack preserves prior labels by `fingerprint` for findings that
  still exist in the current sampled subset

## When to use this

Use this workflow when:

- native/runtime plumbing work is already stable enough that precision is the
  next blocker
- you want a representative review pack over real repositories
- you need a deterministic queue that multiple reviewers can revisit without
  losing prior labels

Do not use this workflow as proof of completion unless `labels.json` has actual
human labels and `benchmark.json` / `benchmark.md` have been refreshed from that
review.

## Current pack location

The current repo-local review pack lives at:

- `workspace/precision-review-pack/`

That pack is scratch/output, not canonical evidence.
Promotion from workspace requires a separate placement decision.

## Default command

Use the source-only default first so docs, fixtures, and scratch shelves do not
dominate the review set.

```bash
python shared/tools/aci_precision_review_pack.py \
  C:\Users\f_tan\project\aci \
  C:\Users\f_tan\project\pier \
  --out-dir workspace/precision-review-pack \
  --scope-mode source-only \
  --exclude-path shared/test-data \
  --exclude-path system-dev \
  --max-per-ci 10
```

What this gives you:

- `corpus.json`: full corpus export
- `findings.json`: sampled review subset used for review and benchmark refresh
- `triage.md`: density view over the full corpus
- `labels.json`: reviewer label template
- `benchmark.json` / `benchmark.md`: automatically refreshed labeled-precision
  and unlabeled-queue output for the current sampled review subset
- `README.md`: generated review instructions including the exact benchmark
  refresh command and the current selection mode

## Review loop

1. Open `triage.md` to identify hot CI-IDs.
2. Use `benchmark.md` to see the current unlabeled queue by CI-ID.
3. Edit `labels.json` and fill `label` with:
   - `true-positive`
   - `false-positive`
   - `skip`
4. Refresh the benchmark after label edits:

```bash
python shared/tools/aci_precision_benchmark.py \
  --findings-json workspace/precision-review-pack/findings.json \
  --labels-json workspace/precision-review-pack/labels.json \
  --json workspace/precision-review-pack/benchmark.json \
  --markdown workspace/precision-review-pack/benchmark.md
```

5. Repeat until label coverage and per-CI-ID confidence are strong enough for
   the claim you want to make.

## Practical rules

- Prefer `source-only` unless you intentionally want non-runtime noise in the
  sample.
- Use `--exclude-path` aggressively for repo-local synthetic or staging shelves.
- Keep `--max-per-ci` bounded so the first review pass is actually finishable.
- Preserve `labels.json` across reruns; the tooling is designed to keep prior
  labels intact for fingerprints that remain in the current sampled subset.
- Treat blank labels as "not reviewed yet", not as false positives.
- Read `README.md` inside the generated pack as the current operator handoff:
  it records full-corpus count, review-subset count, selection mode, label-row
  count, current labeled-row count, and the exact benchmark refresh command.
- Do not treat `corpus.json` and `findings.json` as interchangeable:
  `corpus.json` is the full export, while `findings.json` is the bounded review
  subset used for `labels.json` and benchmark refresh.

## What still remains outside this workflow

This workflow does not remove the final blockers by itself.

Still required:

- actual human labeling
- resulting labeled precision summary review
- separate recall-label workflow if a public recall claim is needed
