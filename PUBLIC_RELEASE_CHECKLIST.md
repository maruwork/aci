# ACI Public Release Checklist

Status: Active

## Purpose

Provide a bounded release-review checklist for the common ACI shelf.

## Checklist

- `README` explains what `ACI` is and is not
- `README` points to a one-command smoke check
- `README` points to sample reports
- `README` points to assumptions, non-goals, and extension guidance
- public-facing commands and file paths are repo-relative
- `python/aci_public_smoke.py` runs successfully
- report example JSON files parse successfully
- `ACI_SHELF_CLASSIFICATION.md` still cleanly separates generic vs optional domain
- no `__pycache__` remains in common authority shelves after verification

## Release Note Rule

If one checklist item fails, do not call the common shelf "publicly ready" without naming the failure explicitly.
