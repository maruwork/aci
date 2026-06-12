# ACI Repo Export Readiness Task Board

Status: Complete

- list standalone-repo checks
- audit the current shelf as a standalone repo
- add missing repository-facing guidance
- record blocker status

## Execution Notes

- added `docs/release/REPO_EXPORT_GUIDE.md`
- added `docs/release/REPO_EXPORT_CHECKLIST.md`
- converted public smoke, quickstart, README, shelf classification, and public samples to repo-relative paths
- converted Pier bridge docs away from host-specific absolute path explanations
- reran public smoke and sample JSON validation
- purged regenerated `__pycache__`
