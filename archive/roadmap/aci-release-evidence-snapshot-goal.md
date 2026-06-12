# ACI Release Evidence Snapshot Goal

Status: Complete

## Goal

Define one bounded release-evidence snapshot that lets a maintainer capture the current `ACI` release-candidate proof state in one place.

## Complete When

- one release-evidence snapshot document exists
- release-prep reading order points to that snapshot
- the snapshot lists current evidence inputs and fail-close rules
- current candidate review and proof review can point to the same bounded snapshot

## Out of Scope

- actual release execution
- remote tag creation
- registry upload
- hosted release publication

## Failure Conditions

- maintainers still need to reconstruct candidate proof state from scattered release-prep documents
- snapshot contents disagree with release-prep contracts
- snapshot omits a proof surface needed for package or registry review
