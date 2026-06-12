# ACI Installed Package Verification Design

Status: Complete

## AIPV-T1

- Purpose:
  - define the minimum installed-package verification scope
- Start Conditions:
  - package layout migration is complete
- Inputs:
  - `pyproject.toml`
  - `docs/release/PACKAGING_BLOCKERS.md`
  - `docs/release/PACKAGE_LAYOUT_TARGET.md`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - state what this wave will prove and what it will not prove
- Output:
  - explicit verification scope
- Acceptance:
  - repo-local proof and installed-package proof are not conflated
- Failure Conditions:
  - scope silently assumes publishing or registry access
- Stop Conditions:
  - the proof boundary depends on unstated tooling behavior
- Evidence:
  - scope note in summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AIPV-T2

- Purpose:
  - define the bounded proof model
- Start Conditions:
  - scope is explicit
- Inputs:
  - verification scope
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - separate editable-install proof from built-artifact proof at a bounded contract level
- Output:
  - explicit proof model
- Acceptance:
  - proof model is reviewable without oral explanation
- Failure Conditions:
  - proof model overclaims distribution completion
- Stop Conditions:
  - proof requires external publishing infrastructure
- Evidence:
  - verification contract
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AIPV-T3

- Purpose:
  - implement bounded verification support
- Start Conditions:
  - proof model is fixed
- Inputs:
  - verification contract
- Read:
  - ``
- Write:
  - ``
- Do:
  - add the smallest useful verification helper and CLI surface
- Output:
  - reviewable verification implementation
- Acceptance:
  - helper proves the bounded installed-package route without breaking current commands
- Failure Conditions:
  - implementation hardcodes one environment in an unstated way
- Stop Conditions:
  - implementation would require registry publishing
- Evidence:
  - code changes and verification output
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AIPV-T4

- Purpose:
  - update reader routes
- Start Conditions:
  - implementation exists
- Inputs:
  - verification implementation
- Read:
  - ``
- Write:
  - ``
- Do:
  - update packaging and release-prep routes to explain the new proof surface
- Output:
  - updated reader guidance
- Acceptance:
  - readers can understand what is proven and what remains out of scope
- Failure Conditions:
  - docs blur package layout migration and installed verification
- Stop Conditions:
  - docs depend on future unpublished steps
- Evidence:
  - updated route docs
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AIPV-T5

- Purpose:
  - verify and close
- Start Conditions:
  - docs are updated
- Inputs:
  - revised verification surface
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - run bounded verification and close the wave
- Output:
  - closure summary
- Acceptance:
  - no reviewed inconsistency remains in this verification surface
- Failure Conditions:
  - closure still depends on oral explanation
- Stop Conditions:
  - 5-layer drift appears before closure
- Evidence:
  - verification output and summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B
