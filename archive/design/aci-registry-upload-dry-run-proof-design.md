# ACI Registry Upload Dry-Run Proof Design

Status: Complete

## Task Design

### `ARUDP-T1`

- start condition:
  - go/no-go log and upload runbook already exist
- read:
  - `RELEASE_GO_NO_GO_LOG.md`
  - `docs/release/REGISTRY_UPLOAD_RUNBOOK.md`
- write:
  - this design
- do:
  - define why a dry-run proof is needed before any live action
- done when:
  - dry-run scope is explicit

### `ARUDP-T2`

- start condition:
  - dry-run scope is explicit
- read:
  - artifact checklist and package proof contracts
- write:
  - `docs/release/REGISTRY_UPLOAD_DRY_RUN_PROOF.md`
- do:
  - define required dry-run fields and fail-close rule
- done when:
  - a maintainer can see what must be recorded for a bounded dry run

### `ARUDP-T3`

- start condition:
  - dry-run field model is explicit
- read:
  - upload runbook and proof surfaces
- write:
  - `docs/release/REGISTRY_UPLOAD_DRY_RUN_PROOF.md`
- do:
  - add the bounded dry-run proof surface
- done when:
  - one dry-run proof document exists with inputs, fields, and rules

### `ARUDP-T4`

- start condition:
  - dry-run proof exists
- read:
  - `README.md`
  - `docs/release/RELEASE_PREP_INDEX.md`
  - `RELEASE_GO_NO_GO_LOG.md`
- write:
  - route docs
- do:
  - point release-prep reading order to the dry-run proof
- done when:
  - reader routes mention the dry-run proof consistently

### `ARUDP-T5`

- start condition:
  - routes are aligned
- read:
  - mirror pair requirements
- write:
  - mirror docs and summary
- do:
  - close the wave and keep mirror sync current
- done when:
  - summary exists and mirror sync covers the new wave
