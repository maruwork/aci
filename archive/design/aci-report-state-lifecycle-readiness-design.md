# ACI Report State Lifecycle Readiness Design

Status: Complete

## RSL-T1

- Purpose:
  - make the current partial state language explicit
- Start Conditions:
  - reliability fixture suite readiness is complete
- Inputs:
  - `report/aci-generic-report-contract.md`
  - `report/examples/`
  - `python/aci_findings.py`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - inventory current uses of verification, triage, residual, waiver, and baseline language
- Output:
  - explicit current-state inventory
- Acceptance:
  - the inventory separates distinct concepts instead of collapsing them
- Failure Conditions:
  - inventory treats baseline and lifecycle as one concept
- Stop Conditions:
  - a state concept requires downstream storage first
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## RSL-T2

- Purpose:
  - define the minimum generic state lifecycle
- Start Conditions:
  - current-state inventory complete
- Inputs:
  - current-state inventory
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define stable states and transitions for visible `ACI` findings
- Output:
  - explicit lifecycle model
- Acceptance:
  - states are non-overlapping and generic
- Failure Conditions:
  - states duplicate waiver or baseline semantics
- Stop Conditions:
  - a state needs workflow tooling outside the common shelf
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## RSL-T3

- Purpose:
  - make contracts and examples speak the lifecycle consistently
- Start Conditions:
  - lifecycle model fixed
- Inputs:
  - lifecycle model
- Read:
  - `python/`
  - `report/`
- Write:
  - `python/`
  - `report/`
- Do:
  - add the lifecycle fields and revise examples
- Output:
  - revised code/docs/examples
- Acceptance:
  - repeated-state meaning is visible in finding rows and summaries
- Failure Conditions:
  - examples contradict the lifecycle model
- Stop Conditions:
  - contract updates require downstream persistence
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## RSL-T4

- Purpose:
  - make the lifecycle readable to maintainers and evaluators
- Start Conditions:
  - code/docs/examples updated
- Inputs:
  - revised lifecycle surfaces
- Read:
  - `README.md`
  - `report/`
  - `core/`
- Write:
  - ``
- Do:
  - update reader routes and lifecycle guidance
- Output:
  - updated docs
- Acceptance:
  - another maintainer can explain finding lifecycle states without oral context
- Failure Conditions:
  - docs mix lifecycle with waiver/baseline language
- Stop Conditions:
  - root surface grows in the wrong direction
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## RSL-T5

- Purpose:
  - verify the lifecycle surface
- Start Conditions:
  - reader guidance updated
- Inputs:
  - revised lifecycle model
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
  - no reviewed ambiguity remains in the lifecycle surface
- Failure Conditions:
  - lifecycle still depends on oral explanation
- Stop Conditions:
  - 5-layer drift appears before closure
- Record Destination:
  - summary
- Final Decider:
  - Codex B
