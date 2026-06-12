# ACI Registry Publishing Discipline Contract

Status: Active

## Purpose

Define the bounded discipline that must be satisfied before any package registry publication of `ACI` is allowed.

## What This Contract Owns

- publishing prerequisites
- publishing evidence requirements
- hold-line rules before live registry mutation
- the boundary between private proof and public registry steps

## What This Contract Does Not Own

- actual registry upload
- credential management
- public release timing
- remote repository actions
- downstream rollout

## Publishing Gate

Registry publication may be considered only when all of the following are true:

1. release candidate verification in `RELEASE_DISCIPLINE_PACKET.md` is complete
2. installed-package proof is complete
3. editable-install proof is complete
4. built-wheel install proof is complete
5. source-distribution proof is complete
6. owner decisions in `docs/governance/OWNER_DECISION_PACKET.md` are explicit
7. the publishable-hold checklist is satisfied

## Required Evidence

Before live publication is allowed, the maintainer must be able to point to:

- `REGISTRY_ARTIFACT_CHECKLIST.md`
- `RELEASE_DISCIPLINE_PACKET.md`
- `runtime/aci-installed-package-verification-contract.md`
- `runtime/aci-editable-install-proof-contract.md`
- `runtime/aci-built-wheel-install-proof-contract.md`
- `runtime/aci-source-distribution-proof-contract.md`
- `docs/governance/OWNER_DECISION_PACKET.md`
- `PUBLISHABLE_HOLD_CHECKLIST.md`

## Hold Lines

Do not proceed to live registry publication when any of the following is true:

- any required proof still depends on oral explanation
- package verification still fails in a bounded temporary environment
- owner decisions remain unresolved
- private preparation and public publication routes contradict each other
- packaging blockers still include unresolved common-shelf restructuring

## Reading Rule

Read this contract together with:

1. `RELEASE_DISCIPLINE_PACKET.md`
2. `RELEASE_DISCIPLINE_CONTRACT.md`
3. `RELEASE_PREP_INDEX.md`
4. `PUBLISHABLE_HOLD_CHECKLIST.md`
5. `PUBLIC_GO_LIVE_SEQUENCE_DRAFT.md`
6. `REGISTRY_ARTIFACT_CHECKLIST.md`
7. `REGISTRY_UPLOAD_RUNBOOK.md`
