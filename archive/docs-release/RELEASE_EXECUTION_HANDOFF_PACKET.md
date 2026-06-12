# ACI Release Execution Handoff Packet

Status: Active

## Purpose

Provide one bounded handoff packet that lets a maintainer pass the current `ACI` release candidate to the person who will perform release execution, without requiring extra oral context.

## Required Inputs

- `RELEASE_CANDIDATE_PACKET.md`
- `RELEASE_EVIDENCE_SNAPSHOT.md`
- `RELEASE_GO_NO_GO_LOG.md`
- `REGISTRY_UPLOAD_DRY_RUN_PROOF.md`
- `REGISTRY_UPLOAD_RUNBOOK.md`
- `PUBLIC_GO_LIVE_SEQUENCE_DRAFT.md`

## Handoff Fields

- candidate label
- intended version
- current decision outcome
- current dry-run status
- required local artifacts
- required release-prep documents
- hold-line reminder
- execution owner note

## Handoff Rule

- use this packet only after go/no-go and dry-run proof are current
- keep the packet bounded to release execution preparation
- do not treat this packet as permission to perform remote actions automatically

## Fail-Close Rule

If the execution owner cannot identify the candidate, version, dry-run status, and required documents from this packet alone, the handoff is incomplete.

## Out Of Scope

- actual upload
- remote tag creation
- hosted release publication
