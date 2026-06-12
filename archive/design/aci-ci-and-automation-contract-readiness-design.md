# ACI CI And Automation Contract Readiness Design

Status: Complete

## CAR-T1

- Purpose:
  - identify what `ACI` already exposes for repeatable automation
- Start Conditions:
  - baseline suppression and waiver readiness is complete
- Inputs:
  - `python/aci_cli.py`
  - `runtime/aci-cli-and-config-contract.md`
  - `report/aci-machine-readable-report-contract.md`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - inventory automation-capable commands, output paths, and exit behavior
- Output:
  - explicit automation inventory
- Acceptance:
  - the inventory separates current facts from desired future behavior
- Failure Conditions:
  - inventory assumes one CI vendor
- Stop Conditions:
  - capability belongs to downstream runtime ownership
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## CAR-T2

- Purpose:
  - define the smallest generic automation contract that market-grade tooling expects
- Start Conditions:
  - automation inventory complete
- Inputs:
  - automation inventory
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define machine-readable output, automation command mode, and exit semantics
- Output:
  - explicit CI/automation contract
- Acceptance:
  - another maintainer can explain how `ACI` should behave in repeatable automation
- Failure Conditions:
  - contract grows into a hosted workflow design
- Stop Conditions:
  - a required feature belongs to the fixture wave
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## CAR-T3

- Purpose:
  - implement the bounded automation-oriented surface
- Start Conditions:
  - generic automation contract fixed
- Inputs:
  - generic automation contract
- Read:
  - `python/`
- Write:
  - `python/`
  - ``
- Do:
  - add only the command behavior needed for common-shelf automation use
- Output:
  - working automation-oriented command path
- Acceptance:
  - `ACI` can run in a repeatable machine-readable mode without downstream project assumptions
- Failure Conditions:
  - implementation duplicates downstream workflow wiring
- Stop Conditions:
  - command behavior needs fixture-wave support first
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## CAR-T4

- Purpose:
  - document the CI-facing contract clearly
- Start Conditions:
  - automation-oriented implementation exists
- Inputs:
  - implemented automation behavior
- Read:
  - ``
- Write:
  - ``
- Do:
  - document automation command usage, output shape, and exit semantics
- Output:
  - updated docs
- Acceptance:
  - another maintainer can wire `ACI` into automation without reverse-engineering code
- Failure Conditions:
  - docs promise behavior the implementation does not have
- Stop Conditions:
  - docs need unresolved fixture-wave guarantees
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## CAR-T5

- Purpose:
  - verify the reviewed automation contract before the fixture wave
- Start Conditions:
  - docs updated
- Inputs:
  - revised automation behavior
  - revised docs
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - run bounded automation checks and manual review
- Output:
  - closure summary
- Acceptance:
  - no reviewed inconsistency remains in the automation-facing surface
- Failure Conditions:
  - automation behavior still depends on oral explanation
- Stop Conditions:
  - 5-layer drift appears before closure
- Record Destination:
  - summary
- Final Decider:
  - Codex B
