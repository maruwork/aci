# ACI Baseline Suppression And Waiver Readiness Design

Status: Complete

## BSW-T1

- Purpose:
  - identify the current partial language before formalizing a reusable model
- Start Conditions:
  - CLI and config readiness is complete
- Inputs:
  - `core/aci-autonomous-code-inspection-tool-contract.md`
  - `report/`
  - `python/aci_findings.py`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - inventory where baseline, suppression, waiver, and residual language already appears
- Output:
  - explicit current-language inventory
- Acceptance:
  - the inventory separates facts from planned behavior
- Failure Conditions:
  - the inventory merges residual with waiver or suppression
- Stop Conditions:
  - the language depends on downstream-only storage
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## BSW-T2

- Purpose:
  - define the minimum generic repeated-operation model
- Start Conditions:
  - inventory complete
- Inputs:
  - current-language inventory
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define baseline, suppression, waiver, and new/existing distinction as narrow generic concepts
- Output:
  - explicit generic model
- Acceptance:
  - each concept is reviewable and non-overlapping
- Failure Conditions:
  - a concept becomes a policy placeholder rather than a tool concept
- Stop Conditions:
  - a concept requires business-specific approval rules
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## BSW-T3

- Purpose:
  - decide how the common shelf represents the new model
- Start Conditions:
  - generic model fixed
- Inputs:
  - generic model
- Read:
  - ``
- Write:
  - ``
- Do:
  - define the smallest artifact shape or contract surface that expresses the model
- Output:
  - fixed common-shelf artifact shape
- Acceptance:
  - the artifact shape is generic and bounded
- Failure Conditions:
  - the shape leaks downstream persistence decisions
- Stop Conditions:
  - one artifact would incorrectly mix baseline, suppression, and waiver authority
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## BSW-T4

- Purpose:
  - make findings, reports, and examples speak the new model
- Start Conditions:
  - artifact shape fixed
- Inputs:
  - generic model
  - artifact shape
- Read:
  - `python/`
  - `report/`
- Write:
  - `python/`
  - `report/`
- Do:
  - update contract surfaces and examples to distinguish new, baseline, suppression, and waiver handling
- Output:
  - revised code and docs
- Acceptance:
  - repeated-operation meaning is visible in the reviewed output shape
- Failure Conditions:
  - contract changes outrun the chosen artifact shape
- Stop Conditions:
  - later state-lifecycle concerns must be separated into the final wave
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## BSW-T5

- Purpose:
  - make the repeated-operation model readable to users
- Start Conditions:
  - code and contract updates complete
- Inputs:
  - revised baseline/suppression/waiver surfaces
- Read:
  - `README.md`
  - `report/`
  - `core/`
- Write:
  - ``
- Do:
  - update reader routes and guidance
- Output:
  - revised reading guidance
- Acceptance:
  - a new maintainer can explain what baseline, suppression, and waiver mean in `ACI`
- Failure Conditions:
  - docs hide the difference between residual and waiver
- Stop Conditions:
  - root surface grows in the wrong direction
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## BSW-T6

- Purpose:
  - verify the repeated-operation model before the CI wave
- Start Conditions:
  - reading guidance updated
- Inputs:
  - revised model
  - revised code/docs/examples
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - run bounded verification and manual review
- Output:
  - closure summary
- Acceptance:
  - no reviewed ambiguity remains around baseline, suppression, and waiver
- Failure Conditions:
  - repeated-operation meaning still depends on oral explanation
- Stop Conditions:
  - 5-layer drift appears before closure
- Record Destination:
  - summary
- Final Decider:
  - Codex B
