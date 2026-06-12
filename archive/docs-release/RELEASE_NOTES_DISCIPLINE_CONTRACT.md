# ACI Release Notes Discipline Contract

Status: Active

## Purpose

Define the bounded discipline that must be satisfied before `ACI` release notes are considered ready.

## What This Contract Owns

- required release-note sections
- required evidence references
- hold-line rules before release notes are called ready
- the boundary between shelf-owned release notes and hosted release-page formatting

## What This Contract Does Not Own

- hosted release-page formatting
- public announcement copy
- marketing messaging
- downstream rollout

## Required Sections

Every reviewed `ACI` release note must make these visible:

1. version intent
2. product summary
3. why the release was needed
4. user-facing impact
5. verification evidence
6. compatibility notes
7. remaining out-of-scope items, if any

## Required Evidence

Before release notes are called ready, the maintainer must be able to point to:

- `VERSIONING_POLICY.md`
- `CHANGELOG_DISCIPLINE.md`
- `RELEASE_DISCIPLINE_PACKET.md`
- current proof contracts that changed in the release

## Hold Lines

Do not call release notes ready when any of the following is true:

- one required section is missing
- version intent is still ambiguous
- verification evidence is not reviewable
- compatibility impact is still oral-only

## Reading Rule

Read this contract together with:

1. `RELEASE_DISCIPLINE_PACKET.md`
2. `CHANGELOG_DISCIPLINE.md`
3. `VERSIONING_POLICY.md`
4. `RELEASE_PREP_INDEX.md`
