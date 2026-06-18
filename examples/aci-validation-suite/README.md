# ACI validation suite

Ground-truth fixtures for measuring detector recall and precision with a
**reproducible labeled benchmark** instead of a reviewer's live judgment.

- `planted/` — each file (or file pair, for cross-file detectors) contains one
  known smell that the paired detector **must** flag. Detecting all of them =
  100% recall.
- `clean/` — correct counterparts that look superficially similar but are not
  smells; the paired signal **must not** appear. Any appearance is a false
  positive.
- `manifest.json` — the fixed labels: which signals are expected on `planted/`
  and which are forbidden on `clean/`. Labels live here, set ahead of time, so
  the score does not depend on who runs it.

## Run

```bash
python shared/tools/aci_validation_scorecard.py
```

Prints recall and false-positive counts and exits non-zero on any recall gap
or false positive, so it can gate CI. This suite is the canonical precision /
recall benchmark for ACI's native detectors.

## Coverage

The clean counterparts deliberately lock in the precision fixes that are easy
to regress:

| Detector | Clean fixture guards against |
|---|---|
| CI-02 | a long-but-flat function (constructor/config) firing on length alone |
| CI-04 | a large but cohesive class firing as a god class |
| CI-05 | structurally distinct functions colliding as clones |
| CI-06 | data-collection members read as magic constants |
| CI-20 | repeated vocabulary tags (schema/discriminator words) read as scattered constants |
| CI-07 | a private helper used from another file read as dead code |
| CI-13 | a one-way import edge read as a cycle |
| CI-14 | safe YAML / JSON / exact-version dependency pinning read as security drift |
| CI-22 | a `with`-managed or retained/awaited resource/task read as a leak |
| CI-23 | explicit named parameters read as hidden `**kwargs` contract drift |
| CI-25 | a timezone-aware datetime read as nondeterminism |

Extend by adding a fixture plus its `manifest.json` entry; the scorecard and
its test pick it up automatically.
