# ACI Release Rollback Discipline Design

Status: Complete

## Task Design

### `ARRD-T1`

- start condition:
  - release handoff and release discipline already exist
- read:
  - `docs/release/RELEASE_EXECUTION_HANDOFF_PACKET.md`
  - `docs/release/RELEASE_DISCIPLINE_PACKET.md`
- write:
  - this design
- do:
  - define why a separate rollback discipline is needed
- done when:
  - rollback scope is explicit

### `ARRD-T2`

- start condition:
  - rollback scope is explicit
- read:
  - release notes and versioning discipline
- write:
  - `docs/release/RELEASE_ROLLBACK_DISCIPLINE_CONTRACT.md`
- do:
  - define required rollback fields and fail-close rule
- done when:
  - a maintainer can see what must be recorded during rollback

### `ARRD-T3`

- start condition:
  - rollback field model is explicit
- read:
  - handoff, go/no-go, and release-note surfaces
- write:
  - `docs/release/RELEASE_ROLLBACK_DISCIPLINE_CONTRACT.md`
- do:
  - add the bounded rollback discipline contract
- done when:
  - one rollback contract exists with inputs, fields, and rules

### `ARRD-T4`

- start condition:
  - rollback contract exists
- read:
  - `README.md`
  - `docs/release/RELEASE_PREP_INDEX.md`
  - `docs/release/MAINTAINER_HISTORY_INDEX.md`
- write:
  - route docs
- do:
  - point release-prep routes to the rollback discipline
- done when:
  - reader routes mention the rollback discipline consistently

### `ARRD-T5`

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
