# ACI Analyzer Integration Readiness Design

Status: Complete

## AIR-T1

- Purpose:
  - identify how analyzer language already appears in the common shelf
- Start Conditions:
  - report state lifecycle readiness is complete
- Inputs:
  - `core/aci-autonomous-code-inspection-tool-contract.md`
  - `core/aci-code-inspection-execution-spec.md`
  - `runtime/aci-ci-and-automation-contract.md`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - inventory current analyzer mentions and implied ownership
- Output:
  - explicit analyzer-language inventory
- Acceptance:
  - inventory separates current facts from later execution ambitions
- Failure Conditions:
  - inventory assumes analyzer support that is not documented
- Stop Conditions:
  - analyzer meaning depends on downstream runtime state
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AIR-T2

- Purpose:
  - define the smallest useful common analyzer registry
- Start Conditions:
  - inventory complete
- Inputs:
  - analyzer-language inventory
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define registry fields such as analyzer id, lane, purpose, evidence type, and support level
- Output:
  - explicit analyzer registry model
- Acceptance:
  - registry fields are generic and bounded
- Failure Conditions:
  - registry fields start owning downstream config or workflow logic
- Stop Conditions:
  - a field belongs to a later profile-execution wave
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AIR-T3

- Purpose:
  - implement the common-shelf analyzer catalog surface
- Start Conditions:
  - registry model fixed
- Inputs:
  - analyzer registry model
- Read:
  - `python/`
- Write:
  - `python/`
  - ``
- Do:
  - add the analyzer registry and a CLI view of it
- Output:
  - working analyzer catalog support
- Acceptance:
  - the common shelf can show its analyzer catalog without downstream assumptions
- Failure Conditions:
  - implementation overclaims runtime execution support
- Stop Conditions:
  - implementation requires provider-specific tooling
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AIR-T4

- Purpose:
  - make analyzer boundaries readable
- Start Conditions:
  - catalog support exists
- Inputs:
  - implemented analyzer registry
- Read:
  - ``
- Write:
  - ``
- Do:
  - document analyzer support level, purpose, and boundary
- Output:
  - updated docs
- Acceptance:
  - another maintainer can tell what is cataloged, what is executed, and what remains downstream
- Failure Conditions:
  - docs blur catalog support and full execution support
- Stop Conditions:
  - docs require unresolved profile behavior
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AIR-T5

- Purpose:
  - verify the reviewed analyzer surface
- Start Conditions:
  - docs updated
- Inputs:
  - revised analyzer surface
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - run compile checks, CLI checks, and manual review
- Output:
  - closure summary
- Acceptance:
  - no reviewed inconsistency remains in the analyzer surface
- Failure Conditions:
  - analyzer support still depends on oral explanation
- Stop Conditions:
  - 5-layer drift appears before closure
- Record Destination:
  - summary
- Final Decider:
  - Codex B
