# ACI Profile Execution Readiness Design

Status: Complete

## APR-T1

- Purpose:
  - identify how profile language already appears in the common shelf
- Start Conditions:
  - analyzer integration readiness is complete
- Inputs:
  - `python/aci_profiles.py`
  - `core/aci-autonomous-code-inspection-tool-contract.md`
  - `runtime/aci-cli-and-config-contract.md`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - inventory current profile ids, scope language, lane meaning, and analyzer defaults
- Output:
  - explicit profile-language inventory
- Acceptance:
  - inventory separates current facts from later execution ambitions
- Failure Conditions:
  - inventory assumes runtime support that is not documented
- Stop Conditions:
  - profile meaning depends on downstream runtime state
- Send-Back Conditions:
  - inventory conflicts with current public CLI behavior
- Human Decision Gate:
  - stop if a profile name itself encodes downstream-only workflow language
- Evidence:
  - inventory summary with cited source files
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## APR-T2

- Purpose:
  - define the smallest useful common profile execution model
- Start Conditions:
  - inventory complete
- Inputs:
  - profile-language inventory
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define model fields such as profile id, lanes, analyzer defaults, scope mode, control lane, and support level
- Output:
  - explicit profile execution model
- Acceptance:
  - profile fields are generic and bounded
- Failure Conditions:
  - fields start owning downstream runtime or trigger logic
- Stop Conditions:
  - a field belongs to a later downstream adoption wave
- Send-Back Conditions:
  - model cannot explain one existing supported profile
- Human Decision Gate:
  - stop if adding a field would make the common shelf claim non-generic execution guarantees
- Evidence:
  - model written as a bounded contract
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## APR-T3

- Purpose:
  - implement the common-shelf profile catalog surface
- Start Conditions:
  - profile model fixed
- Inputs:
  - profile execution model
- Read:
  - `python/`
- Write:
  - `python/`
  - ``
- Do:
  - add the profile registry and a CLI view of it
- Output:
  - working profile catalog support
- Acceptance:
  - the common shelf can show its profile catalog without downstream assumptions
- Failure Conditions:
  - implementation overclaims runtime execution support
- Stop Conditions:
  - implementation requires provider-specific tooling
- Send-Back Conditions:
  - CLI output cannot stay stable without project-local config
- Human Decision Gate:
  - stop if implementation starts owning full runner behavior
- Evidence:
  - CLI output and compile proof
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## APR-T4

- Purpose:
  - make profile boundaries readable
- Start Conditions:
  - catalog support exists
- Inputs:
  - implemented profile registry
- Read:
  - ``
- Write:
  - ``
- Do:
  - document profile support level, meaning, and ownership boundary
- Output:
  - updated docs
- Acceptance:
  - another maintainer can tell what is cataloged, what is executed in the common shelf, and what remains downstream
- Failure Conditions:
  - docs blur profile catalog support and full repository execution support
- Stop Conditions:
  - docs require unresolved downstream behavior
- Send-Back Conditions:
  - reader route still depends on oral explanation
- Human Decision Gate:
  - stop if documentation forces a decision that belongs to project-local integration
- Evidence:
  - updated README and contract route
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## APR-T5

- Purpose:
  - verify the reviewed profile surface
- Start Conditions:
  - docs updated
- Inputs:
  - revised profile surface
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - run compile checks, CLI checks, and manual review
- Output:
  - closure summary
- Acceptance:
  - no reviewed inconsistency remains in the profile surface
- Failure Conditions:
  - profile support still depends on oral explanation
- Stop Conditions:
  - 5-layer drift appears before closure
- Send-Back Conditions:
  - verification reveals boundary overclaim or CLI mismatch
- Human Decision Gate:
  - stop if reviewed evidence contradicts the bounded support model
- Evidence:
  - compile output, CLI output, and manual review notes
- Record Destination:
  - summary
- Final Decider:
  - Codex B
