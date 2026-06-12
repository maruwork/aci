# ACI Release Rollback Discipline Contract

Status: Active

## Purpose

Define one bounded rollback discipline for `ACI` so a maintainer can respond consistently if a released version must be withdrawn, superseded, or marked unsafe.

## Required Inputs

- `RELEASE_EXECUTION_HANDOFF_PACKET.md`
- `RELEASE_GO_NO_GO_LOG.md`
- `RELEASE_NOTES_DISCIPLINE_CONTRACT.md`
- `VERSIONING_POLICY.md`
- `CHANGELOG_DISCIPLINE.md`
- `PUBLIC_GO_LIVE_SEQUENCE_DRAFT.md`

## Rollback Fields

- affected version
- rollback trigger
- rollback scope
- replacement version expectation
- downstream impact note
- registry/release-page follow-up note
- maintainer owner note

## Rollback Rules

- use rollback only when the released surface is materially wrong, unsafe, or contract-breaking
- record whether the response is withdrawal, superseding release, or hold notice
- keep the rollback note bounded to facts, impact, and next action
- do not rewrite prior release evidence; append rollback context instead

## Fail-Close Rule

If the maintainer cannot identify the affected version, trigger, and next action from the rollback record, the rollback discipline is incomplete.

## Out Of Scope

- remote registry deletion
- hosted release-page editing
- downstream repository fixes
