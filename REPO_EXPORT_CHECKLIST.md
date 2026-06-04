# ACI Repo Export Checklist

Status: Active

## Purpose

List the minimum repository-facing conditions for lifting this shelf into a standalone public repository.

## Checklist

- public-facing commands are repo-relative
- public-facing file paths are repo-relative
- `README.md` explains current monorepo placement and standalone-repo view
- `REPO_EXPORT_GUIDE.md` defines the expected standalone root shape
- `ACI_SHELF_CLASSIFICATION.md` can be read without host-specific absolute paths
- public sample reports use repo-relative references
- `aci_public_smoke.py` emits repo-relative sample evidence
- domain bridge docs do not require host-specific absolute paths to explain generic/core boundaries

## Out Of Scope

- license selection
- org/repository hosting decision
- CI/CD setup outside this shelf
