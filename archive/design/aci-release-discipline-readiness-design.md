# ACI Release Discipline Readiness Design

Status: Complete

## ARD-T1

- Purpose:
  - identify how release-discipline language already appears in the common shelf
- Start Conditions:
  - downstream adoption readiness is complete
- Inputs:
  - `docs/release/RELEASE_PREP_INDEX.md`
  - `docs/release/PUBLIC_RELEASE_CHECKLIST.md`
  - `docs/release/PUBLISHABLE_HOLD_CHECKLIST.md`
  - `docs/release/PUBLIC_GO_LIVE_SEQUENCE_DRAFT.md`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - inventory current release-prep route, versioning language, changelog language, and authority boundaries
- Output:
  - explicit release-discipline inventory
- Acceptance:
  - inventory separates current facts from later live release actions
- Failure Conditions:
  - inventory assumes provider-specific release behavior
- Stop Conditions:
  - release meaning depends on host-specific operations
- Send-Back Conditions:
  - inventory reveals contradictory release authority
- Human Decision Gate:
  - stop if current docs cannot separate preparation from live publication
- Evidence:
  - inventory summary with cited source files
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARD-T2

- Purpose:
  - define the smallest useful release discipline model
- Start Conditions:
  - inventory complete
- Inputs:
  - release-discipline inventory
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define model fields such as release candidate inputs, versioning rule, changelog expectation, release note expectation, and verification gates
- Output:
  - explicit release discipline model
- Acceptance:
  - model fields are generic and bounded
- Failure Conditions:
  - fields start owning remote publication behavior
- Stop Conditions:
  - a field belongs to a later owner-action wave
- Send-Back Conditions:
  - model cannot explain one existing release-prep document
- Human Decision Gate:
  - stop if adding a field would force a host-specific process
- Evidence:
  - model written as a bounded contract
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARD-T3

- Purpose:
  - implement the common release discipline packet
- Start Conditions:
  - release discipline model fixed
- Inputs:
  - release discipline model
- Read:
  - ``
- Write:
  - ``
- Do:
  - add versioning/changelog/release-note discipline docs and link them from the release-prep route
- Output:
  - working release discipline packet
- Acceptance:
  - another maintainer can prepare the next release candidate without oral explanation
- Failure Conditions:
  - implementation overclaims live publication support
- Stop Conditions:
  - implementation requires remote operations
- Send-Back Conditions:
  - packet cannot stay generic without host-specific instructions
- Human Decision Gate:
  - stop if the packet starts deciding actual release timing or version choice
- Evidence:
  - new docs and updated route
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARD-T4

- Purpose:
  - make release-prep boundaries readable
- Start Conditions:
  - packet support exists
- Inputs:
  - implemented release discipline packet
- Read:
  - ``
- Write:
  - ``
- Do:
  - document what belongs to common release prep and what belongs to later owner actions
- Output:
  - updated docs
- Acceptance:
  - another maintainer can tell what is ready now and what waits for owner timing
- Failure Conditions:
  - docs blur preparation and publication
- Stop Conditions:
  - docs require unresolved owner-specific timing
- Send-Back Conditions:
  - reader route still depends on oral explanation
- Human Decision Gate:
  - stop if documentation forces a release timing decision
- Evidence:
  - updated index and contract route
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARD-T5

- Purpose:
  - verify the reviewed release discipline surface
- Start Conditions:
  - docs updated
- Inputs:
  - revised release discipline surface
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - run route checks and manual review
- Output:
  - closure summary
- Acceptance:
  - no reviewed inconsistency remains in the release discipline surface
- Failure Conditions:
  - release discipline still depends on oral explanation
- Stop Conditions:
  - 5-layer drift appears before closure
- Send-Back Conditions:
  - verification reveals route mismatch or boundary overclaim
- Human Decision Gate:
  - stop if reviewed evidence contradicts the bounded release model
- Evidence:
  - route checks and manual review notes
- Record Destination:
  - summary
- Final Decider:
  - Codex B
