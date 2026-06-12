# ACI Post-Release Review Packet

Status: Active

## Purpose

Provide one bounded packet for reviewing an `ACI` release after it has been published, so maintainers can capture outcomes, regressions, and follow-up work without relying on scattered notes.

## Required Inputs

- `RELEASE_EXECUTION_HANDOFF_PACKET.md`
- `RELEASE_NOTES_DISCIPLINE_CONTRACT.md`
- `RELEASE_ROLLBACK_DISCIPLINE_CONTRACT.md`
- `CHANGELOG_DISCIPLINE.md`
- `VERSIONING_POLICY.md`

## Review Fields

- released version
- release date
- intended change class
- observed outcome summary
- downstream impact summary
- regression summary
- rollback involvement
- follow-up work summary
- maintainer note

## Review Rules

- create the review after release execution is completed
- record facts and follow-up items, not speculative blame
- link rollback context only if rollback or hold action was required
- keep the packet bounded to product outcome and next work

## Fail-Close Rule

If the maintainer cannot identify the released version, observed outcome, and follow-up work from this packet alone, the post-release review is incomplete.

## Out Of Scope

- live incident response
- downstream repository fixes
- marketing or announcement copy
