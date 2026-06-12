# ACI Release Notes Discipline Design

Status: Complete

## ARND-T1

- Purpose:
  - define the bounded release-notes scope
- Start Conditions:
  - registry upload runbook is complete
- Inputs:
  - `docs/release/RELEASE_DISCIPLINE_PACKET.md`
  - `docs/release/CHANGELOG_DISCIPLINE.md`
  - `docs/release/REGISTRY_UPLOAD_RUNBOOK.md`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - state exactly what this wave governs and what it does not govern
- Output:
  - explicit scope
- Acceptance:
  - scope does not overclaim hosted release-page ownership
- Failure Conditions:
  - scope silently assumes provider-specific formatting
- Stop Conditions:
  - scope depends on unstated owner behavior
- Evidence:
  - scope note in summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARND-T2

- Purpose:
  - define the required release-note content model
- Start Conditions:
  - scope is explicit
- Inputs:
  - release discipline and changelog docs
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define the exact bounded sections and evidence that a reviewed release note must include
- Output:
  - explicit content model
- Acceptance:
  - content model is reviewable and fail-close
- Failure Conditions:
  - content model still relies on oral explanation
- Stop Conditions:
  - content model would require hosted release-page behavior in this wave
- Evidence:
  - contract content
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARND-T3

- Purpose:
  - add a bounded release-notes discipline contract
- Start Conditions:
  - content model is fixed
- Inputs:
  - scope and content model
- Read:
  - ``
- Write:
  - ``
- Do:
  - add the smallest useful contract that captures release-note sections, evidence, and hold lines
- Output:
  - reviewable release-notes discipline contract
- Acceptance:
  - contract explains the release-note discipline without oral explanation
- Failure Conditions:
  - contract implies hosted release-page actions
- Stop Conditions:
  - contract would require provider-specific formatting rules
- Evidence:
  - new contract
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARND-T4

- Purpose:
  - align release-prep routes
- Start Conditions:
  - release-notes contract exists
- Inputs:
  - release-notes contract
- Read:
  - ``
- Write:
  - ``
- Do:
  - update release-prep reading order and release packet references so they point to the same release-notes contract
- Output:
  - aligned routes
- Acceptance:
  - no reviewed route conflict remains
- Failure Conditions:
  - one route still points to an older release-note rule
- Stop Conditions:
  - route alignment would rewrite proof documents outside this wave
- Evidence:
  - updated docs
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARND-T5

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
