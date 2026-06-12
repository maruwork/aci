# ACI Release Go/No-Go Log Design

Status: Complete

## Task Design

### `ARGN-T1`

- start condition:
  - release candidate packet and evidence snapshot already exist
- read:
  - `docs/release/RELEASE_CANDIDATE_PACKET.md`
  - `docs/release/RELEASE_EVIDENCE_SNAPSHOT.md`
- write:
  - this design
- do:
  - define why a separate decision log is needed
- done when:
  - decision scope is explicit

### `ARGN-T2`

- start condition:
  - decision scope is explicit
- read:
  - release-prep contracts and packets
- write:
  - `RELEASE_GO_NO_GO_LOG.md`
- do:
  - define required decision fields and states
- done when:
  - a maintainer can see what must be recorded for a bounded decision

### `ARGN-T3`

- start condition:
  - decision field model is explicit
- read:
  - release evidence and gate documents
- write:
  - `RELEASE_GO_NO_GO_LOG.md`
- do:
  - add the bounded decision log
- done when:
  - one go/no-go log exists with inputs, fields, and decision rules

### `ARGN-T4`

- start condition:
  - log exists
- read:
  - `README.md`
  - `docs/release/RELEASE_PREP_INDEX.md`
  - `docs/release/RELEASE_EVIDENCE_SNAPSHOT.md`
- write:
  - route docs
- do:
  - point release-prep reading order to the log
- done when:
  - reader routes mention the decision log consistently

### `ARGN-T5`

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
