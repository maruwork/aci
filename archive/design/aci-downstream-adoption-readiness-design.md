# ACI Downstream Adoption Readiness Design

Status: Complete

## ADR-T1

- Purpose:
  - identify how downstream adoption language already appears in the common shelf
- Start Conditions:
  - profile execution readiness is complete
- Inputs:
  - `README.md`
  - `DOMAIN_PACK_EXTENSION_GUIDE.md`
  - `runtime/`
  - `templates/`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - inventory current adoption route, copy/customize language, and implied downstream boundaries
- Output:
  - explicit downstream-adoption inventory
- Acceptance:
  - inventory separates current facts from later downstream execution ambitions
- Failure Conditions:
  - inventory assumes one fixed downstream repository shape
- Stop Conditions:
  - adoption meaning depends on project-specific runtime state
- Send-Back Conditions:
  - inventory conflicts with current public docs
- Human Decision Gate:
  - stop if the current docs cannot distinguish common authority from downstream authority
- Evidence:
  - inventory summary with cited source files
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ADR-T2

- Purpose:
  - define the smallest useful downstream adoption model
- Start Conditions:
  - inventory complete
- Inputs:
  - downstream-adoption inventory
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define adoption packet fields such as read order, carry set, customize set, downstream-owned set, and non-carry set
- Output:
  - explicit downstream adoption model
- Acceptance:
  - model fields are generic and bounded
- Failure Conditions:
  - fields start owning project-local runtime or repository decisions
- Stop Conditions:
  - a field belongs to a later project-specific integration wave
- Send-Back Conditions:
  - model cannot explain one existing documented route
- Human Decision Gate:
  - stop if adding a field would make the common shelf prescribe one repository layout
- Evidence:
  - model written as a bounded contract
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ADR-T3

- Purpose:
  - implement the common downstream adoption packet surface
- Start Conditions:
  - adoption model fixed
- Inputs:
  - downstream adoption model
- Read:
  - ``
- Write:
  - ``
- Do:
  - add the downstream adoption packet and a clear entry route to it
- Output:
  - working downstream adoption packet support
- Acceptance:
  - another maintainer can read the packet and know what to carry, customize, and leave downstream
- Failure Conditions:
  - implementation overclaims common ownership of project-local runtime
- Stop Conditions:
  - implementation requires touching downstream repositories
- Send-Back Conditions:
  - packet cannot stay generic without naming one specific project layout
- Human Decision Gate:
  - stop if the packet starts prescribing downstream business workflow
- Evidence:
  - packet text and route updates
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ADR-T4

- Purpose:
  - make downstream boundaries readable
- Start Conditions:
  - packet support exists
- Inputs:
  - implemented adoption packet
- Read:
  - ``
- Write:
  - ``
- Do:
  - document adoption support level, meaning, and ownership boundary
- Output:
  - updated docs
- Acceptance:
  - another maintainer can tell what is common, what is copied, what is customized, and what stays downstream
- Failure Conditions:
  - docs blur common shelf and downstream project authority
- Stop Conditions:
  - docs require unresolved project-specific behavior
- Send-Back Conditions:
  - reader route still depends on oral explanation
- Human Decision Gate:
  - stop if documentation forces a downstream repository decision
- Evidence:
  - updated README and adoption route
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## ADR-T5

- Purpose:
  - verify the reviewed downstream adoption surface
- Start Conditions:
  - docs updated
- Inputs:
  - revised downstream adoption surface
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - run compile-safe checks, route checks, and manual review
- Output:
  - closure summary
- Acceptance:
  - no reviewed inconsistency remains in the downstream adoption surface
- Failure Conditions:
  - adoption support still depends on oral explanation
- Stop Conditions:
  - 5-layer drift appears before closure
- Send-Back Conditions:
  - verification reveals boundary overclaim or route mismatch
- Human Decision Gate:
  - stop if reviewed evidence contradicts the bounded adoption model
- Evidence:
  - route checks and manual review notes
- Record Destination:
  - summary
- Final Decider:
  - Codex B
