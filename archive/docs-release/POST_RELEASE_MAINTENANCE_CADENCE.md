# ACI Post-Release Maintenance Cadence

Status: Active

## Purpose

Define one bounded maintenance cadence for `ACI` after release so maintainers can review stability, follow-up work, and next release readiness on a predictable rhythm.

## Required Inputs

- `POST_RELEASE_REVIEW_PACKET.md`
- `RELEASE_ROLLBACK_DISCIPLINE_CONTRACT.md`
- `CHANGELOG_DISCIPLINE.md`
- `VERSIONING_POLICY.md`
- `ACI_DOWNSTREAM_ADOPTION_PACKET.md`

## Cadence Fields

- reviewed version
- review window
- outstanding follow-up count
- downstream feedback summary
- regression watch summary
- next release readiness note
- maintainer owner note

## Cadence Rules

- run this review after a release has settled enough for maintainers to observe downstream impact
- record what remains open, what stabilized, and what should feed the next release
- keep the cadence bounded to product maintenance, not incident chat
- link rollback context only when rollback affected the reviewed version

## Fail-Close Rule

If the maintainer cannot identify the reviewed version, open follow-up surface, and next release implication from this cadence note alone, maintenance tracking is incomplete.

## Out Of Scope

- live incident response
- downstream repository fixes
- release execution itself
