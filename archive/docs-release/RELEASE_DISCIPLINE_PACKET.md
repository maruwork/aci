# ACI Release Discipline Packet

Status: Active

## Purpose

Give maintainers one bounded packet for preparing the next `ACI` release candidate without mixing common preparation and live publication actions.

## Read First

1. `RELEASE_PREP_INDEX.md`
2. `RELEASE_DISCIPLINE_CONTRACT.md`
3. `VERSIONING_POLICY.md`
4. `CHANGELOG_DISCIPLINE.md`
5. `RELEASE_NOTES_DISCIPLINE_CONTRACT.md`
6. `REGISTRY_PUBLISHING_DISCIPLINE_CONTRACT.md`
7. `REGISTRY_ARTIFACT_CHECKLIST.md`
8. `RELEASE_TAG_DISCIPLINE_CONTRACT.md`
9. `PUBLIC_RELEASE_CHECKLIST.md`
10. `PUBLISHABLE_HOLD_CHECKLIST.md`
11. `PUBLIC_GO_LIVE_SEQUENCE_DRAFT.md`

## Release Candidate Inputs

Before preparing the next release candidate, confirm:

- current common-shelf waves that changed the product surface
- current CLI, automation, and fixture verification all pass
- current public-facing docs reflect the reviewed product surface
- current private/public preparation docs do not contradict the release route

## Versioning Rule

Use `VERSIONING_POLICY.md` for how to choose the next version implication.

The common shelf defines:

- how to classify the change
- what kind of version bump that change implies

The common shelf does not decide:

- the exact date of release
- the actual moment a tag is created

## Changelog Rule

Use `CHANGELOG_DISCIPLINE.md` for how to summarize the change set.

Each release candidate should make these visible:

- what changed
- why it changed
- who is affected
- whether the change alters CLI/config/report/contract behavior

## Verification Gate

Use these minimum checks before calling a release candidate ready:

1. compile checks pass
2. `python python/aci_cli.py smoke` passes
3. `python python/aci_cli.py automation-smoke` passes
4. `python python/aci_cli.py fixture-check` passes
5. report samples remain parseable and current
6. installed-package, editable-install, built-wheel, and source-distribution proofs are current
7. no `__pycache__` remains in common authority shelves

## Not This Packet

This packet does not own:

- public release timing
- remote tag creation
- hosted release notes
- provider-specific CI setup
