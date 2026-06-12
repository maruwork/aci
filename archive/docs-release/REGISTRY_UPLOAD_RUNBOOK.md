# ACI Registry Upload Runbook

Status: Active

## Purpose

Show the bounded order of checks and evidence review that must be completed immediately before any live `ACI` package registry upload is attempted.

## Runbook

1. confirm owner decisions in `docs/governance/OWNER_DECISION_PACKET.md`
2. confirm release candidate readiness in `RELEASE_DISCIPLINE_PACKET.md`
3. confirm registry publishing gates in `REGISTRY_PUBLISHING_DISCIPLINE_CONTRACT.md`
4. confirm registry artifact readiness in `REGISTRY_ARTIFACT_CHECKLIST.md`
5. confirm release tag readiness in `RELEASE_TAG_DISCIPLINE_CONTRACT.md`
6. confirm installed-package, editable-install, built-wheel, and source-distribution proofs are current
7. confirm no remaining common-shelf restructuring blocker exists
8. stop if any gate fails
9. only after all checks pass, hand off to the owner for any live upload action

## Fail-Close Rule

If one step cannot be evidenced from reviewed documents, do not proceed to any live upload action.

## Out Of Scope

- actual upload commands
- credential entry
- provider-specific UI steps
