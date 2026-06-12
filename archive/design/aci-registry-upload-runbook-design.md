# ACI Registry Upload Runbook Design

Status: Complete

## ARUR-T1

- Purpose:
  - define the bounded upload-runbook scope
- Start Conditions:
  - release tag discipline is complete
- Inputs:
  - `docs/release/REGISTRY_PUBLISHING_DISCIPLINE_CONTRACT.md`
  - `docs/release/RELEASE_TAG_DISCIPLINE_CONTRACT.md`
  - `docs/release/RELEASE_PREP_INDEX.md`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - state exactly what this runbook governs and what it does not govern
- Output:
  - explicit scope
- Acceptance:
  - scope does not overclaim live upload execution
- Failure Conditions:
  - scope silently assumes credentials or provider-specific behavior
- Stop Conditions:
  - scope depends on unstated owner behavior
- Evidence:
  - scope note in summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARUR-T2

- Purpose:
  - define the upload-preparation sequence
- Start Conditions:
  - scope is explicit
- Inputs:
  - publishing discipline and tag discipline docs
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define the exact bounded order of checks, proofs, artifact review, and hold lines that must be satisfied before any upload is attempted
- Output:
  - explicit runbook sequence
- Acceptance:
  - sequence is reviewable and fail-close
- Failure Conditions:
  - sequence still relies on oral explanation
- Stop Conditions:
  - sequence would require live provider actions in this wave
- Evidence:
  - runbook content
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARUR-T3

- Purpose:
  - add one bounded registry upload runbook
- Start Conditions:
  - sequence is fixed
- Inputs:
  - scope and sequence
- Read:
  - ``
- Write:
  - ``
- Do:
  - add the smallest useful runbook that captures upload-preparation order, required evidence, and stop lines
- Output:
  - reviewable upload runbook
- Acceptance:
  - runbook explains the upload-preparation route without oral explanation
- Failure Conditions:
  - runbook implies live upload execution
- Stop Conditions:
  - runbook would require credentials or remote mutation
- Evidence:
  - new runbook
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARUR-T4

- Purpose:
  - align release-prep routes
- Start Conditions:
  - runbook exists
- Inputs:
  - runbook
- Read:
  - ``
- Write:
  - ``
- Do:
  - update release-prep reading order and publishing references so they point to the same runbook
- Output:
  - aligned routes
- Acceptance:
  - no reviewed route conflict remains
- Failure Conditions:
  - one route still points to an older upload-preparation rule
- Stop Conditions:
  - route alignment would rewrite proof documents outside this wave
- Evidence:
  - updated docs
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARUR-T5

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
