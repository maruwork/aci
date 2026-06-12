# ACI Post-Release Review Packet Design

Status: Complete

## Task Design

### `APRR-T1`

- start condition:
  - release handoff and rollback discipline already exist
- read:
  - `docs/release/RELEASE_EXECUTION_HANDOFF_PACKET.md`
  - `docs/release/RELEASE_ROLLBACK_DISCIPLINE_CONTRACT.md`
- write:
  - this design
- do:
  - define why a separate post-release review packet is needed
- done when:
  - review scope is explicit

### `APRR-T2`

- start condition:
  - review scope is explicit
- read:
  - release notes, changelog, and versioning discipline
- write:
  - `docs/release/POST_RELEASE_REVIEW_PACKET.md`
- do:
  - define required review fields and fail-close rule
- done when:
  - a maintainer can see what must be recorded after a release

### `APRR-T3`

- start condition:
  - review field model is explicit
- read:
  - handoff, release-note, and rollback surfaces
- write:
  - `docs/release/POST_RELEASE_REVIEW_PACKET.md`
- do:
  - add the bounded post-release review packet
- done when:
  - one post-release review packet exists with inputs, fields, and rules

### `APRR-T4`

- start condition:
  - review packet exists
- read:
  - `README.md`
  - `docs/release/RELEASE_PREP_INDEX.md`
  - `docs/release/MAINTAINER_HISTORY_INDEX.md`
- write:
  - route docs
- do:
  - point release-prep routes to the post-release review packet
- done when:
  - reader routes mention the post-release review packet consistently

### `APRR-T5`

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
