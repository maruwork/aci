# ACI Release Candidate Packet

Status: Active

## Purpose

Provide one bounded packet that lets a maintainer review whether the current `ACI` shelf is ready to be treated as a release candidate.

## Candidate Summary

- product surface:
  - common CLI, report contract, package proofs, release discipline
- current release gates:
  - release notes discipline
  - registry publishing discipline
  - registry artifact checklist
  - release tag discipline
  - registry upload runbook

## Required Evidence

- `RELEASE_EVIDENCE_SNAPSHOT.md`
- `RELEASE_DISCIPLINE_PACKET.md`
- `RELEASE_NOTES_DISCIPLINE_CONTRACT.md`
- `REGISTRY_PUBLISHING_DISCIPLINE_CONTRACT.md`
- `REGISTRY_ARTIFACT_CHECKLIST.md`
- `RELEASE_TAG_DISCIPLINE_CONTRACT.md`
- `REGISTRY_UPLOAD_RUNBOOK.md`
- current package proof summaries

## Review Questions

1. is the version intent explicit?
2. is the release-note content reviewable?
3. are the package proofs current?
4. are the publication and tag gates still consistent?
5. does any remaining blocker still require shelf restructuring?

## Fail-Close Rule

If one required evidence source is missing or contradictory, do not call the current shelf a release candidate.

## Out Of Scope

- actual release execution
- remote tag creation
- registry upload
