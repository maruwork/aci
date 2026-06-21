# Field precision on actively-developed code (the contrast pack)

The parent pack measured ACI on **mature, finished libraries** and found ~3%
review-worthiness — useful as a warning, but only half the picture. ACI's home
turf is code **being actively developed**. This pack closes that gap: the same
harness and the same two-axis rubric, run on six real, actively-developed
projects.

This is **current-state confirmation, not new work** — ACI is unchanged.

## Method

- **Corpus** (native lane, `--scope-mode source-only`) — 6 actively-developed
  projects, **207 findings adjudicated**:
  `httpie @5b604c3` (CLI app), `mkdocs @2862536` (docs tool),
  `textual @182277f` (TUI framework), `poetry @cf54a1c` and `pdm @ad49b1d`
  (packaging tools), `httpx @b5addb6` (HTTP client).
- Same pipeline (`aci_corpus_harness.py` → human adjudication) and the same two
  axes as the parent pack: **detection correctness** and **review-worthiness**
  (would a maintainer of this *live* project act on it?). Larger projects were
  stratified-sampled per CI-ID.

## Result — the contrast is the finding

| corpus | n | detection precision | review-worthiness |
|---|--:|---:|---:|
| mature libraries (parent pack) | 276 | 70% | **3%** |
| **actively-developed projects** (this pack) | 207 | 73% | **36%** |

On code that is still being written, **about a third of ACI's findings are worth
acting on** — roughly **12× the mature-library rate**. Per detector:

| detector | precision | review-worthy | n |
|---|---:|---:|--:|
| CI-03 TODO/FIXME/HACK | 100% | 38/40 | 40 |
| CI-02 long/tangled | 96% | 23/28 | 28 |
| CI-18 param cluster | 100% | 3/16 | 16 |
| CI-21 broad except | 71% | 4/31 | 31 |
| CI-07 unused/dead | 50% | 2/2 | 2 |
| CI-05 copy-paste | 70% | 1/23 | 23 |
| CI-14 security | 42% | 1/12 | 12 |
| CI-22 resource | 36% | 0/14 | 14 |
| CI-04 god class | 13% | 2/23 | 23 |

The driver is exactly what you'd expect of live code: **CI-03** surfaces the
developers' own live reminders ("Refactor and drastically simplify…", "TODO:
this should move into poetry-core", "FIXME: …more targeted cache clear"), and
**CI-02** flags long functions a maintainer would reasonably consider splitting.

## Honesty note: more data moved the number down, and that's the point

The first version of this pack used only 2 projects (httpie + mkdocs, 50
findings) and measured **50%** review-worthiness. Expanding to 6 projects (207
findings) moved it to **36%** — `textual`/`poetry`/`pdm`/`httpx` are more
library-like and polished than the two CLI apps, so they sit between mature
libraries (3%) and pure application code (the apps alone were ~50%). The larger
sample is the more honest number; the contrast with mature code (12×) holds
either way.

## What this means

ACI is **noisy on mature code and genuinely useful on code under active
development** — its intended use. Both numbers are published; neither alone is
the truth.

## Caveats

- n = 207 across 6 projects; larger projects stratified-sampled, not full.
- "Actively-developed" is approximated by app/tool/framework projects vs
  foundational libraries, not by commit recency. True first-party in-progress
  code (a user's own work) is the closest case still unmeasured here.

Files: `labels.json` (adjudicated dataset), `findings.json` (portable records).
Parent method and the mature baseline: `../README.md`.
