# ACI Registry Upload Dry-Run Proof

Status: Active

## Purpose

Provide one bounded dry-run proof surface that lets a maintainer confirm `ACI` is ready for release execution without performing any live upload.

## Required Inputs

- `RELEASE_GO_NO_GO_LOG.md`
- `REGISTRY_UPLOAD_RUNBOOK.md`
- `REGISTRY_ARTIFACT_CHECKLIST.md`
- `RELEASE_TAG_DISCIPLINE_CONTRACT.md`
- `runtime/aci-built-wheel-install-proof-contract.md`
- `runtime/aci-source-distribution-proof-contract.md`

## Dry-Run Fields

- candidate label
- intended version
- wheel artifact status
- source distribution status
- release tag readiness status
- upload command readiness status
- hold line confirmation
- unresolved blocker summary

## Dry-Run Rule

- treat this proof as current only when required package artifacts exist and the upload runbook can be followed without ambiguity
- keep the dry-run bounded to local or private evidence only
- do not perform any remote registry action from this proof surface

## Fail-Close Rule

If artifact status, tag readiness, or upload command readiness cannot be stated clearly, do not treat the current candidate as execution-ready.

## Out Of Scope

- actual upload
- remote tag creation
- hosted release publication
