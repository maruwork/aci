# ACI Release Discipline Contract

Status: Active

## Purpose

Define the bounded release discipline model that the common `ACI` shelf is allowed to own.

## What This Contract Owns

- release-prep reading order
- release candidate input expectations
- versioning rule
- changelog expectation
- release note expectation
- verification gate before a candidate is called ready
- pointer to registry publishing discipline
- pointer to release-tag discipline
- pointer to release-notes discipline

## What This Contract Does Not Own

- live release execution
- remote tag creation
- host-provider release pages
- final publication timing
- owner-specific release approval

## Release Model Fields

Each bounded release discipline packet must make these visible:

- `read_first`
- `candidate_inputs`
- `versioning_rule`
- `changelog_rule`
- `verification_gate`
- `not_owned_here`

## Boundary Rule

The common shelf may define:

- how to classify the impact of a change
- what verification is expected before release
- how to write a bounded changelog entry

The common shelf must not define:

- when the owner must publish
- which host button to click
- how a remote tag is created

## Reading Rule

Use this contract together with:

1. `RELEASE_DISCIPLINE_PACKET.md`
2. `VERSIONING_POLICY.md`
3. `CHANGELOG_DISCIPLINE.md`
4. `RELEASE_PREP_INDEX.md`
5. `REGISTRY_PUBLISHING_DISCIPLINE_CONTRACT.md`
6. `RELEASE_TAG_DISCIPLINE_CONTRACT.md`
7. `RELEASE_NOTES_DISCIPLINE_CONTRACT.md`
