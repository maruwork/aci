# ACI Post-Release Maintenance Cadence Design

Status: Complete

## Task Design

### `APRMC-T1`

- start condition:
  - post-release review already exists
- read:
  - `docs/release/POST_RELEASE_REVIEW_PACKET.md`
  - `docs/release/RELEASE_ROLLBACK_DISCIPLINE_CONTRACT.md`
- write:
  - this design
- do:
  - define why a separate maintenance cadence is needed
- done when:
  - maintenance scope is explicit

### `APRMC-T2`

- start condition:
  - maintenance scope is explicit
- read:
  - review, changelog, versioning, and downstream adoption surfaces
- write:
  - `docs/release/POST_RELEASE_MAINTENANCE_CADENCE.md`
- do:
  - define required cadence fields and fail-close rule
- done when:
  - a maintainer can see what must be recorded during post-release maintenance

### `APRMC-T3`

- start condition:
  - cadence field model is explicit
- read:
  - post-release review and downstream adoption surfaces
- write:
  - `docs/release/POST_RELEASE_MAINTENANCE_CADENCE.md`
- do:
  - add the bounded maintenance cadence
- done when:
  - one maintenance cadence document exists with inputs, fields, and rules

### `APRMC-T4`

- start condition:
  - maintenance cadence exists
- read:
  - `README.md`
  - `docs/release/RELEASE_PREP_INDEX.md`
  - `docs/release/MAINTAINER_HISTORY_INDEX.md`
- write:
  - route docs
- do:
  - point reader routes to the maintenance cadence
- done when:
  - reader routes mention the cadence consistently

### `APRMC-T5`

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
