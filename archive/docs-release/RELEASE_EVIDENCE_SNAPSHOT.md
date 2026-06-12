# ACI Release Evidence Snapshot

Status: Active

## Purpose

Capture one bounded snapshot of release-candidate evidence so a maintainer can review current `ACI` release readiness without re-deriving proof state from many separate documents.

## Snapshot Scope

- candidate packet status
- version intent
- release-note readiness
- package proof status
- registry publication gate status
- remaining blockers that still stop a release candidate from being called ready

## Snapshot Inputs

- `RELEASE_CANDIDATE_PACKET.md`
- `RELEASE_GO_NO_GO_LOG.md`
- `RELEASE_DISCIPLINE_PACKET.md`
- `RELEASE_NOTES_DISCIPLINE_CONTRACT.md`
- `REGISTRY_PUBLISHING_DISCIPLINE_CONTRACT.md`
- `REGISTRY_ARTIFACT_CHECKLIST.md`
- `RELEASE_TAG_DISCIPLINE_CONTRACT.md`
- `REGISTRY_UPLOAD_RUNBOOK.md`
- `runtime/aci-installed-package-verification-contract.md`
- `runtime/aci-editable-install-proof-contract.md`
- `runtime/aci-built-wheel-install-proof-contract.md`
- `runtime/aci-source-distribution-proof-contract.md`

## Snapshot Fields

- candidate label
- intended version
- current shelf scope
- current verification result
- package proof result
- registry gate result
- release-note result
- unresolved blocker list
- maintainer signoff note

## Fail-Close Rule

If one input proof is stale, missing, or contradictory, the snapshot is not current and must not be treated as release-ready evidence.

## Out Of Scope

- actual upload
- remote tag creation
- hosted release publication
