# ACI Registry Publishing Discipline Design

Status: Complete

## ARPD-T1

- Purpose:
  - define the bounded registry-publishing scope
- Start Conditions:
  - source-distribution proof is complete
- Inputs:
  - `docs/release/RELEASE_DISCIPLINE_PACKET.md`
  - `docs/release/RELEASE_DISCIPLINE_CONTRACT.md`
  - `docs/release/RELEASE_PREP_INDEX.md`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - state exactly what this wave governs and what it does not govern
- Output:
  - explicit scope
- Acceptance:
  - scope does not overclaim live publication execution
- Failure Conditions:
  - scope silently assumes credentials or live registry access
- Stop Conditions:
  - scope depends on unstated owner behavior
- Evidence:
  - scope note in summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARPD-T2

- Purpose:
  - define publish gates and hold lines
- Start Conditions:
  - scope is explicit
- Inputs:
  - release discipline docs
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define the decision gates, required evidence, stop points, and non-negotiable hold lines before registry publication
- Output:
  - explicit gate model
- Acceptance:
  - gate model makes it clear when publication must not proceed
- Failure Conditions:
  - gate model mixes private proof with public publication
- Stop Conditions:
  - gate model requires a live registry action in this wave
- Evidence:
  - contract content
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARPD-T3

- Purpose:
  - add a bounded registry-publishing contract
- Start Conditions:
  - gate model is fixed
- Inputs:
  - scope and gates
- Read:
  - ``
- Write:
  - ``
- Do:
  - add the smallest useful contract that captures publish prerequisites, evidence, and hold lines
- Output:
  - reviewable publishing discipline contract
- Acceptance:
  - contract explains the publishing discipline without oral explanation
- Failure Conditions:
  - contract implies live execution
- Stop Conditions:
  - contract would require credentials or registry mutation
- Evidence:
  - new contract
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARPD-T4

- Purpose:
  - align release-prep routes
- Start Conditions:
  - publishing contract exists
- Inputs:
  - publishing contract
- Read:
  - ``
- Write:
  - ``
- Do:
  - update release-prep reading order, release packet references, and any public/private boundary docs that must point to the new contract
- Output:
  - aligned routes
- Acceptance:
  - no reviewed route conflict remains
- Failure Conditions:
  - one route still points to an older publishing rule
- Stop Conditions:
  - route alignment would rewrite proof documents outside this wave
- Evidence:
  - updated docs
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARPD-T5

- Purpose:
  - close with summary
- Start Conditions:
  - routes are aligned
- Inputs:
  - updated docs
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - close checkpoints, tasks, and summary
- Output:
  - completed wave record
- Acceptance:
  - no reviewed inconsistency remains
- Failure Conditions:
  - closure still depends on oral explanation
- Stop Conditions:
  - 5-layer drift appears before closure
- Evidence:
  - summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B
