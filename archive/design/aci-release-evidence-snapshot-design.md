# ACI Release Evidence Snapshot Design

Status: Complete

## Task Design

### `ARES-T1`

- start condition:
  - release-candidate packet already exists
- read:
  - `docs/release/RELEASE_CANDIDATE_PACKET.md`
  - `docs/release/RELEASE_DISCIPLINE_PACKET.md`
- write:
  - this design
- do:
  - define why a separate evidence snapshot is needed
- done when:
  - snapshot scope is explicit

### `ARES-T2`

- start condition:
  - snapshot scope is explicit
- read:
  - release-prep contracts and package proof contracts
- write:
  - `docs/release/RELEASE_EVIDENCE_SNAPSHOT.md`
- do:
  - define required fields and fail-close rule
- done when:
  - a maintainer can see what evidence must be captured

### `ARES-T3`

- start condition:
  - field model is explicit
- read:
  - release candidate and package proof documents
- write:
  - `docs/release/RELEASE_EVIDENCE_SNAPSHOT.md`
- do:
  - add the bounded snapshot document
- done when:
  - one snapshot document exists with inputs, fields, and scope

### `ARES-T4`

- start condition:
  - snapshot exists
- read:
  - `README.md`
  - `docs/release/RELEASE_PREP_INDEX.md`
  - `docs/release/RELEASE_CANDIDATE_PACKET.md`
- write:
  - route docs
- do:
  - point release-prep reading order to the snapshot
- done when:
  - reader routes mention the snapshot consistently

### `ARES-T5`

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
