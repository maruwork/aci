# ACI Registry Artifact Checklist

Status: Active

## Purpose

List the bounded package artifacts and release-support documents that must exist before `ACI` can enter any live registry publication step.

## Required Package Artifacts

- one reviewed source distribution file
- one reviewed wheel file
- package metadata from `pyproject.toml`
- the reviewed CLI entrypoint definition

## Required Proof Artifacts

- `runtime/aci-installed-package-verification-contract.md`
- `runtime/aci-editable-install-proof-contract.md`
- `runtime/aci-built-wheel-install-proof-contract.md`
- `runtime/aci-source-distribution-proof-contract.md`

## Required Release Artifacts

- `RELEASE_DISCIPLINE_PACKET.md`
- `VERSIONING_POLICY.md`
- `CHANGELOG_DISCIPLINE.md`
- `PUBLIC_RELEASE_CHECKLIST.md`
- `PUBLISHABLE_HOLD_CHECKLIST.md`
- `docs/governance/OWNER_DECISION_PACKET.md`

## Required Reader-Facing Artifacts

- `README.md`
- `USER_EVALUATION_INDEX.md`
- `RELEASE_PREP_INDEX.md`

## Fail-Close Rule

Do not proceed to live registry publication when any required artifact is missing, contradictory, or still depends on oral explanation.

## Out Of Scope

- actual upload commands
- registry credentials
- hosted release-page formatting
