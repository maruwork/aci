# ACI Built Wheel Install Proof Design

Status: Complete

## ABWIP-T1

- Purpose:
  - define the bounded built-wheel proof scope
- Start Conditions:
  - editable-install proof is complete
- Inputs:
  - `runtime/aci-editable-install-proof-contract.md`
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
  - proof scope does not overclaim registry or publishing completion
- Failure Conditions:
  - scope silently assumes editable-install equivalence
- Stop Conditions:
  - proof boundary depends on unstated tool behavior
- Evidence:
  - scope note in summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ABWIP-T2

- Purpose:
  - define the temporary-environment wheel proof model
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
  - define how to build a wheel locally, install it into a bounded temporary environment, and discard that environment
- Output:
  - explicit proof contract
- Acceptance:
  - the proof model is reviewable and does not touch the user's permanent environment
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

## ABWIP-T3

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
  - add the smallest useful helper and route updates for built-wheel proof
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

## ABWIP-T4

- Purpose:
  - execute the built-wheel proof
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
  - build a local wheel from the current shelf
  - install that wheel into the temporary environment
  - invoke `aci installed-package-check`
  - invoke `aci smoke`
- Output:
  - executed built-wheel proof
- Acceptance:
  - `aci` command works from the wheel-installed environment
- Failure Conditions:
  - wheel install succeeds only through unstated environment leakage
- Stop Conditions:
  - execution requires changing the permanent user environment
- Evidence:
  - command output summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ABWIP-T5

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
