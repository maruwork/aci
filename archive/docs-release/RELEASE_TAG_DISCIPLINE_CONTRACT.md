# ACI Release Tag Discipline Contract

Status: Active

## Purpose

Define the bounded discipline that must be satisfied before any release tag creation for `ACI` is allowed.

## What This Contract Owns

- release-tag prerequisites
- required evidence before tag creation
- hold-line rules before any tag action
- the boundary between shelf-owned readiness and owner-owned remote actions

## What This Contract Does Not Own

- actual remote tag creation
- repository-host automation
- public release timing
- release announcement
- downstream rollout

## Release Tag Gate

Release tag creation may be considered only when all of the following are true:

1. release candidate verification in `RELEASE_DISCIPLINE_PACKET.md` is complete
2. version intent is explicit through `VERSIONING_POLICY.md`
3. changelog intent is explicit through `CHANGELOG_DISCIPLINE.md`
4. registry artifact checklist is satisfied
5. registry publishing discipline is explicit
6. owner decisions in `docs/governance/OWNER_DECISION_PACKET.md` are explicit

## Required Evidence

Before any tag creation is allowed, the maintainer must be able to point to:

- `RELEASE_DISCIPLINE_PACKET.md`
- `VERSIONING_POLICY.md`
- `CHANGELOG_DISCIPLINE.md`
- `REGISTRY_ARTIFACT_CHECKLIST.md`
- `REGISTRY_PUBLISHING_DISCIPLINE_CONTRACT.md`
- `docs/governance/OWNER_DECISION_PACKET.md`

## Hold Lines

Do not proceed to tag creation when any of the following is true:

- version intent is still ambiguous
- changelog or release summary is not reviewable
- package proofs or artifact checklist items remain unresolved
- owner decisions remain unresolved
- tag readiness still depends on oral explanation

## Reading Rule

Read this contract together with:

1. `RELEASE_DISCIPLINE_PACKET.md`
2. `VERSIONING_POLICY.md`
3. `CHANGELOG_DISCIPLINE.md`
4. `REGISTRY_ARTIFACT_CHECKLIST.md`
5. `REGISTRY_PUBLISHING_DISCIPLINE_CONTRACT.md`
