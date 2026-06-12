# ACI Analyzer Execution Readiness Design

Status: Complete

## AER-T1

- Purpose:
  - identify how analyzer execution language already appears in the common shelf
- Start Conditions:
  - release discipline readiness is complete
- Inputs:
  - `core/aci-analyzer-registry-contract.md`
  - `core/aci-profile-execution-contract.md`
  - `python/aci_analyzers.py`
  - `python/aci_profile_catalog.py`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - inventory current analyzer execution claims, profile defaults, and availability assumptions
- Output:
  - explicit analyzer-execution inventory
- Acceptance:
  - inventory separates current facts from future downstream execution ambitions
- Failure Conditions:
  - inventory assumes installed analyzers that are not part of the common contract
- Stop Conditions:
  - analyzer execution meaning depends on project-local runtime state
- Send-Back Conditions:
  - inventory conflicts with current CLI or contract behavior
- Human Decision Gate:
  - stop if the current shelf cannot distinguish catalog support from execution support
- Evidence:
  - inventory summary with cited source files
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AER-T2

- Purpose:
  - define the smallest useful analyzer execution model
- Start Conditions:
  - inventory complete
- Inputs:
  - analyzer-execution inventory
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define model fields such as analyzer id, invocation surface, availability check rule, and profile execution plan shape
- Output:
  - explicit analyzer execution model
- Acceptance:
  - model fields are generic and bounded
- Failure Conditions:
  - fields start owning downstream repository or CI wiring
- Stop Conditions:
  - a field belongs to a later downstream integration wave
- Send-Back Conditions:
  - model cannot explain one supported analyzer
- Human Decision Gate:
  - stop if adding a field would make the common shelf claim provider-specific execution support
- Evidence:
  - model written as a bounded contract
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AER-T3

- Purpose:
  - implement the common analyzer execution surface
- Start Conditions:
  - execution model fixed
- Inputs:
  - analyzer execution model
- Read:
  - `python/`
- Write:
  - `python/`
  - ``
- Do:
  - add execution-plan and availability helpers plus CLI views
- Output:
  - working analyzer execution support
- Acceptance:
  - the common shelf can show analyzer execution plans and bounded availability checks without downstream assumptions
- Failure Conditions:
  - implementation overclaims actual downstream repository execution support
- Stop Conditions:
  - implementation requires external installation or provider tooling
- Send-Back Conditions:
  - CLI output cannot stay stable without local repository context
- Human Decision Gate:
  - stop if implementation starts owning full analyzer flag orchestration
- Evidence:
  - CLI output and compile proof
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AER-T4

- Purpose:
  - make analyzer execution boundaries readable
- Start Conditions:
  - execution support exists
- Inputs:
  - implemented analyzer execution support
- Read:
  - ``
- Write:
  - ``
- Do:
  - document execution support level, meaning, and ownership boundary
- Output:
  - updated docs
- Acceptance:
  - another maintainer can tell what is checked locally, what is only planned, and what stays downstream
- Failure Conditions:
  - docs blur common execution planning and downstream runtime ownership
- Stop Conditions:
  - docs require unresolved provider-specific behavior
- Send-Back Conditions:
  - reader route still depends on oral explanation
- Human Decision Gate:
  - stop if documentation forces downstream repository decisions
- Evidence:
  - updated README and contract route
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## AER-T5

- Purpose:
  - verify the reviewed analyzer execution surface
- Start Conditions:
  - docs updated
- Inputs:
  - revised analyzer execution surface
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - run compile checks, CLI checks, and manual review
- Output:
  - closure summary
- Acceptance:
  - no reviewed inconsistency remains in the analyzer execution surface
- Failure Conditions:
  - analyzer execution support still depends on oral explanation
- Stop Conditions:
  - 5-layer drift appears before closure
- Send-Back Conditions:
  - verification reveals boundary overclaim or CLI mismatch
- Human Decision Gate:
  - stop if reviewed evidence contradicts the bounded execution model
- Evidence:
  - compile output, CLI output, and manual review notes
- Record Destination:
  - summary
- Final Decider:
  - Codex B
