# ACI Release Candidate Packet Design

Status: Complete

## ARCP-T1

- Purpose:
  - define the bounded release-candidate packet scope
- Start Conditions:
  - release notes discipline is complete
- Inputs:
  - `docs/release/RELEASE_DISCIPLINE_PACKET.md`
  - `docs/release/RELEASE_NOTES_DISCIPLINE_CONTRACT.md`
  - `docs/release/RELEASE_PREP_INDEX.md`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - state exactly what this packet governs and what it does not govern
- Output:
  - explicit scope
- Acceptance:
  - scope does not overclaim live release execution
- Failure Conditions:
  - scope silently assumes hosted release tooling
- Stop Conditions:
  - scope depends on unstated owner behavior
- Evidence:
  - scope note in summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARCP-T2

- Purpose:
  - define the packet content model
- Start Conditions:
  - scope is explicit
- Inputs:
  - release discipline and release-note discipline docs
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define the exact sections and evidence that one release candidate packet must include
- Output:
  - explicit content model
- Acceptance:
  - content model is reviewable and fail-close
- Failure Conditions:
  - content model still relies on oral explanation
- Stop Conditions:
  - content model would require live provider actions in this wave
- Evidence:
  - packet content definition
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARCP-T3

- Purpose:
  - add one bounded release candidate packet
- Start Conditions:
  - content model is fixed
- Inputs:
  - scope and content model
- Read:
  - ``
- Write:
  - ``
- Do:
  - add the smallest useful packet that collects current release-candidate evidence and gates
- Output:
  - reviewable release candidate packet
- Acceptance:
  - packet explains release-candidate readiness without oral explanation
- Failure Conditions:
  - packet contradicts source documents
- Stop Conditions:
  - packet would require live release actions
- Evidence:
  - new packet
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARCP-T4

- Purpose:
  - align release-prep routes
- Start Conditions:
  - packet exists
- Inputs:
  - packet
- Read:
  - ``
- Write:
  - ``
- Do:
  - update release-prep reading order and discipline references so they point to the same packet
- Output:
  - aligned routes
- Acceptance:
  - no reviewed route conflict remains
- Failure Conditions:
  - one route still points to an older release-candidate summary pattern
- Stop Conditions:
  - route alignment would rewrite proof documents outside this wave
- Evidence:
  - updated docs
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARCP-T5

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
