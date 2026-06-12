# ACI CLI And Config Readiness Design

Status: Complete

## CCR-T1

- Purpose:
  - fix the smallest useful CLI surface before implementation
- Start Conditions:
  - market-grade readiness is complete
- Inputs:
  - `README.md`
  - `runtime/aci-generic-quickstart.md`
  - `python/aci_public_smoke.py`
- Read:
  - ``
- Write:
  - `common/refernce/`
  - ``
- Do:
  - define the minimum generic commands and flags
- Output:
  - fixed CLI surface
- Acceptance:
  - another maintainer can name the supported commands without inferring them
- Failure Conditions:
  - CLI surface overlaps downstream runtime ownership
- Stop Conditions:
  - command scope grows beyond common authority
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## CCR-T2

- Purpose:
  - define a bounded common config schema
- Start Conditions:
  - CLI surface fixed
- Inputs:
  - CLI surface
  - `NON_GOALS.md`
  - `PUBLIC_RUNTIME_ASSUMPTIONS.md`
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define config fields for common-shelf execution only
- Output:
  - fixed config schema
- Acceptance:
  - config fields are generic and bounded
- Failure Conditions:
  - config starts owning project-local trigger or persistence concerns
- Stop Conditions:
  - a field belongs to a later baseline/suppression wave
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## CCR-T3

- Purpose:
  - implement the new CLI/config surface
- Start Conditions:
  - CLI surface and config schema fixed
- Inputs:
  - fixed CLI surface
  - fixed config schema
- Read:
  - `python/`
- Write:
  - `python/`
  - ``
- Do:
  - add the CLI entry and bounded config loader
- Output:
  - working CLI implementation
- Acceptance:
  - common-shelf smoke execution runs through the CLI
- Failure Conditions:
  - implementation bypasses the declared config contract
- Stop Conditions:
  - a required capability belongs to a later wave
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## CCR-T4

- Purpose:
  - make the CLI/config contract explicit
- Start Conditions:
  - implementation exists
- Inputs:
  - implemented CLI/config surface
- Read:
  - ``
- Write:
  - ``
- Do:
  - document config schema and exit-code behavior
- Output:
  - explicit CLI/config contract docs
- Acceptance:
  - another maintainer can predict normal exit behavior and config boundaries
- Failure Conditions:
  - docs describe behavior not present in code
- Stop Conditions:
  - docs require unresolved baseline/suppression policy
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## CCR-T5

- Purpose:
  - move first-time readers onto the new product surface
- Start Conditions:
  - CLI/config contract documented
- Inputs:
  - revised CLI/config docs
- Read:
  - `README.md`
  - `runtime/aci-generic-quickstart.md`
  - `USER_EVALUATION_INDEX.md`
- Write:
  - ``
- Do:
  - update the reader path to use the CLI as the primary invocation surface
- Output:
  - revised entry docs
- Acceptance:
  - user-facing docs no longer require module-level execution as the first route
- Failure Conditions:
  - reader route becomes heavier than before
- Stop Conditions:
  - root surface grows in the wrong direction
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## CCR-T6

- Purpose:
  - verify the new CLI/config surface end to end
- Start Conditions:
  - reader docs updated
- Inputs:
  - revised CLI/config implementation
  - revised docs
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - run compile checks, CLI smoke checks, and manual review
- Output:
  - closure summary
- Acceptance:
  - no reviewed inconsistency remains in the new CLI/config surface
- Failure Conditions:
  - docs, implementation, and smoke output disagree
- Stop Conditions:
  - 5-layer drift appears before closure
- Record Destination:
  - summary
- Final Decider:
  - Codex B
