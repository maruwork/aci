# ACI Release Tag Discipline Design

Status: Complete

## ARTD-T1

- Purpose:
  - define the bounded release-tag scope
- Start Conditions:
  - registry artifact checklist is complete
- Inputs:
  - `docs/release/RELEASE_DISCIPLINE_PACKET.md`
  - `VERSIONING_POLICY.md`
  - `docs/release/CHANGELOG_DISCIPLINE.md`
  - `docs/release/REGISTRY_ARTIFACT_CHECKLIST.md`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - state exactly what this wave governs and what it does not govern
- Output:
  - explicit scope
- Acceptance:
  - scope does not overclaim remote tag execution
- Failure Conditions:
  - scope silently assumes host-specific Git behavior
- Stop Conditions:
  - scope depends on unstated owner behavior
- Evidence:
  - scope note in summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARTD-T2

- Purpose:
  - define tag gates and hold lines
- Start Conditions:
  - scope is explicit
- Inputs:
  - release discipline and artifact checklist docs
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define the decision gates, required evidence, and stop points before any release tag creation may proceed
- Output:
  - explicit gate model
- Acceptance:
  - gate model makes it clear when tag creation must not proceed
- Failure Conditions:
  - gate model mixes release-candidate prep with remote tag actions
- Stop Conditions:
  - gate model requires a live remote action in this wave
- Evidence:
  - contract content
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARTD-T3

- Purpose:
  - add a bounded release-tag discipline contract
- Start Conditions:
  - gate model is fixed
- Inputs:
  - scope and gates
- Read:
  - ``
- Write:
  - ``
- Do:
  - add the smallest useful contract that captures tag prerequisites, evidence, and hold lines
- Output:
  - reviewable tag discipline contract
- Acceptance:
  - contract explains the tag discipline without oral explanation
- Failure Conditions:
  - contract implies remote tag creation
- Stop Conditions:
  - contract would require repository-host mutation
- Evidence:
  - new contract
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARTD-T4

- Purpose:
  - align release-prep routes
- Start Conditions:
  - tag contract exists
- Inputs:
  - tag contract
- Read:
  - ``
- Write:
  - ``
- Do:
  - update release-prep reading order, release packet references, and any route docs that must point to the new tag contract
- Output:
  - aligned routes
- Acceptance:
  - no reviewed route conflict remains
- Failure Conditions:
  - one route still points to an older tag rule
- Stop Conditions:
  - route alignment would rewrite proof documents outside this wave
- Evidence:
  - updated docs
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ARTD-T5

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
