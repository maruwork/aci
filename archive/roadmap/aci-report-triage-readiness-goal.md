# ACI Report Triage Readiness Goal

Status: Complete

## Goal

Make `ACI` reports usable as a generic triage surface, not only as a structure-review artifact.

## Complete When

- human-readable and machine-readable report contracts expose generic triage fields
- `ACI` findings and finding helpers can express confidence, triage state, priority, and fixability without project-local wording
- sample reports show the new triage fields in a neutral generic example
- `README.md` or report-facing docs explain how to read the new triage surface
- reviewed report surfaces no longer depend on maintainer memory to decide what to fix now, what to review, and what to accept as residual

## Out of Scope

- project-local suppression storage
- project-local DB writeback
- external analyzer installation
- public release execution

## Failure Conditions

- new report fields are Pier-specific
- human-readable and machine-readable contracts drift
- sample reports use fields that the contracts do not define
- triage fields are added but do not change operator readability
