# ACI Editable Install Proof Design

Status: Complete

## AEIP-T1

- Purpose:
  - define the bounded editable-install proof scope
- Start Conditions:
  - installed-package verification is complete
- Inputs:
  - `runtime/aci-installed-package-verification-contract.md`
  - `pyproject.toml`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - state exactly what this wave proves and what it does not prove
- Output:
  - explicit proof scope
- Acceptance:
  - proof scope does not overclaim wheel or registry completion
- Failure Conditions:
  - scope silently assumes permanent environment mutation
- Stop Conditions:
  - proof boundary depends on unstated tool behavior
- Evidence:
  - scope note in summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AEIP-T2

- Purpose:
  - define the temporary-environment proof model
- Start Conditions:
  - scope is explicit
- Inputs:
  - proof scope
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define how to create, use, and discard a bounded temporary environment for proof
- Output:
  - explicit proof contract
- Acceptance:
  - the proof model is reviewable and does not touch the user’s permanent environment
- Failure Conditions:
  - proof model requires network package fetches
- Stop Conditions:
  - proof model requires destructive host changes
- Evidence:
  - contract document
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AEIP-T3

- Purpose:
  - add bounded proof support
- Start Conditions:
  - proof model is fixed
- Inputs:
  - proof contract
- Read:
  - ``
- Write:
  - ``
- Do:
  - add the smallest useful helper and contract for editable-install proof
- Output:
  - reviewable proof support
- Acceptance:
  - helper and contract explain the proof route without oral explanation
- Failure Conditions:
  - implementation assumes one shell or one permanent environment
- Stop Conditions:
  - implementation would require registry publishing
- Evidence:
  - code changes and route docs
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AEIP-T4

- Purpose:
  - execute the editable-install proof
- Start Conditions:
  - proof support exists
- Inputs:
  - proof contract and helper
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - create a bounded temporary environment
  - run editable install from the local shelf
  - invoke `aci installed-package-check`
- Output:
  - executed editable-install proof
- Acceptance:
  - `aci` command works in the temporary environment
- Failure Conditions:
  - editable install succeeds only through unstated environment leakage
- Stop Conditions:
  - execution requires changing the permanent user environment
- Evidence:
  - command output summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AEIP-T5

- Purpose:
  - update routes and close
- Start Conditions:
  - execution proof is complete
- Inputs:
  - proof output
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - update reader routes and close the wave
- Output:
  - closure summary and updated routes
- Acceptance:
  - no reviewed inconsistency remains
- Failure Conditions:
  - closure still depends on oral explanation
- Stop Conditions:
  - 5-layer drift appears before closure
- Evidence:
  - updated docs and summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B
