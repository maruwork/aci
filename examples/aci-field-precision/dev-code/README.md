# Field precision on actively-developed code (the contrast pack)

The parent pack measured ACI on **mature, finished libraries** and found ~4%
review-worthiness — useful as a warning, but only half the picture. ACI's home
turf is code **being actively developed**, which the mature sample did not
represent. This pack closes that gap: the same harness and the same two-axis
rubric, run on two real, actively-developed application/tool projects.

This is **current-state confirmation, not new work** — ACI is unchanged. It
verifies a claim the parent pack left unverified.

## Method

- **Corpus** (native lane, `--scope-mode source-only`): `httpie` (CLI HTTP
  client, app code) `@5b604c3` and `mkdocs` (docs tool) `@2862536` — real,
  actively-developed end-user projects rather than foundational libraries.
- Same pipeline (`aci_corpus_harness.py` → 50 findings → human adjudication) and
  the same two axes as the parent pack: **detection correctness** and
  **review-worthiness** (would a maintainer of this *live* project act on it?).
- All 50 findings were adjudicated by reading the cited code.

## Result — the contrast is the finding

| corpus | detection precision | review-worthiness |
|---|---:|---:|
| mature libraries (parent pack) | 76% | **4%** |
| **actively-developed app/tool** (this pack) | **84%** | **50%** |

On code that is still being written, **half of ACI's findings are worth acting
on** — about 12x the rate on mature libraries. The driver is exactly what you
would expect of live code:

- **CI-03 (TODO/FIXME/HACK)** dominates and is mostly review-worthy: these are
  the developers' own live reminders of unfinished work ("Refactor and
  drastically simplify…", "FIXME: some servers still might send…", "TODO: raise
  a deprecation warning in 1.3"). On a finished library the same markers were
  stale; on live code they are actionable.
- **CI-02 (long/tangled functions)** flagged functions whose own code carries a
  TODO asking to split them — true positives a maintainer would act on.
- Detection precision is also a little higher (84% vs 76%): app code has fewer of
  the huge-but-cohesive classes that made CI-04 misfire on libraries.

## What this means

ACI is **noisy on mature code and genuinely useful on code under active
development** — which is its intended use. The 4% figure is not "ACI is mostly
noise"; it is "ACI on a finished library is mostly noise." Both numbers belong in
the honest picture; neither alone is the truth.

## Caveats

- n = 50 on two projects; small. "Actively-developed" is approximated by
  app/tool projects vs foundational libraries, not by commit recency.
- True first-party in-progress code (the user's own) is still not measured; these
  external app projects are the closest reproducible proxy.

Files: `labels.json` (the adjudicated dataset), `findings.json` (portable
records). Parent method and the mature baseline: `../README.md`.
