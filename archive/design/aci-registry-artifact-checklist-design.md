# ACI Registry Artifact Checklist Design

Status: Complete

## ARAC-T1

- Purpose:
  - define the bounded checklist scope
- Start Conditions:
  - registry publishing discipline is complete
- Inputs:
  - `docs/release/REGISTRY_PUBLISHING_DISCIPLINE_CONTRACT.md`
  - `docs/release/RELEASE_PREP_INDEX.md`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - state exactly what this artifact checklist governs and what it does not govern
- Output:
  - explicit scope
- Acceptance:
  - scope does not overclaim live publication execution
- Failure Conditions:
  - scope silently assumes provider-specific packaging behavior
- Stop Conditions:
  - scope depends on unstated owner behavior
- Evidence:
  - scope note in summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARAC-T2

- Purpose:
  - define the required artifact set
- Start Conditions:
  - scope is explicit
- Inputs:
  - release and publishing discipline docs
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define which package files, notes, proofs, and release docs must exist before publication can proceed
- Output:
  - explicit artifact set
- Acceptance:
  - artifact requirements are concrete and reviewable
- Failure Conditions:
  - artifact requirements still rely on oral explanation
- Stop Conditions:
  - artifact requirements would require live registry interaction
- Evidence:
  - checklist content
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARAC-T3

- Purpose:
  - add one bounded registry artifact checklist
- Start Conditions:
  - artifact set is fixed
- Inputs:
  - scope and artifact set
- Read:
  - ``
- Write:
  - ``
- Do:
  - add the smallest useful checklist that captures required artifacts and evidence
- Output:
  - reviewable artifact checklist
- Acceptance:
  - checklist explains the artifact gate without oral explanation
- Failure Conditions:
  - checklist implies live publication actions
- Stop Conditions:
  - checklist would require credentials or remote mutation
- Evidence:
  - new checklist
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARAC-T4

- Purpose:
  - align release-prep routes
- Start Conditions:
  - checklist exists
- Inputs:
  - checklist
- Read:
  - ``
- Write:
  - ``
- Do:
  - update release-prep reading order and publishing discipline references so they point to the same checklist
- Output:
  - aligned routes
- Acceptance:
  - no reviewed route conflict remains
- Failure Conditions:
  - one route still points to an older artifact expectation
- Stop Conditions:
  - route alignment would rewrite proof documents outside this wave
- Evidence:
  - updated docs
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARAC-T5

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
