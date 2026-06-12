# ACI Report Triage Readiness Design

Status: Complete

## RTR-T1

- Purpose:
  - make the current report surface gaps explicit before changing the contract
- Start Conditions:
  - persistence bridge clarity is complete
- Inputs:
  - `report/aci-generic-report-contract.md`
  - `report/aci-machine-readable-report-contract.md`
  - `report/examples/`
- Read:
  - `report/`
- Write:
  - `common/refernce/`
- Do:
  - inventory current triage-visible fields and note what is missing for generic operator use
- Output:
  - explicit missing-field inventory in the working notes or summary
- Acceptance:
  - missing triage surfaces are named without project-local wording
- Failure Conditions:
  - inventory depends on implicit memory rather than named files
- Stop Conditions:
  - a candidate field clearly belongs outside `report/`
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## RTR-T2

- Purpose:
  - define the smallest generic triage model that improves reuse
- Start Conditions:
  - inventory complete
- Inputs:
  - missing-field inventory
  - current report contracts
- Read:
  - `report/`
  - `core/`
- Write:
  - `report/`
  - `common/refernce/`
- Do:
  - choose the minimum set for confidence, triage state, priority, fixability, and baseline/regression visibility
- Output:
  - fixed triage field set reflected in contract edits
- Acceptance:
  - each new field has a generic meaning and clear location
- Failure Conditions:
  - field set introduces domain-pack-specific names
- Stop Conditions:
  - a proposed field requires runtime authority
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## RTR-T3

- Purpose:
  - make normalized findings capable of carrying the triage fields required by the contracts
- Start Conditions:
  - triage field set fixed
- Inputs:
  - revised triage field set
- Read:
  - `python/aci_findings.py`
  - `python/aci_public_smoke.py`
- Write:
  - `python/`
- Do:
  - update finding dataclass and helper defaults only where the generic report model requires them
- Output:
  - revised normalized finding shape and helper path
- Acceptance:
  - finding helpers can emit the fields that samples and contracts require
- Failure Conditions:
  - helper fields become project-local or runtime-owned
- Stop Conditions:
  - the proposed field belongs in report summary only and not per-finding state
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## RTR-T4

- Purpose:
  - make the human-readable contract triage-complete
- Start Conditions:
  - triage field set fixed
- Inputs:
  - revised triage field set
- Read:
  - `report/aci-generic-report-contract.md`
- Write:
  - `report/aci-generic-report-contract.md`
- Do:
  - update required sections, finding rows, and readability rules
- Output:
  - revised human-readable report contract
- Acceptance:
  - a reader can tell what to fix now, what to review, and what remains residual
- Failure Conditions:
  - contract language becomes project-specific
- Stop Conditions:
  - machine-readable contract cannot mirror the same model
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## RTR-T5

- Purpose:
  - keep the machine-readable contract aligned with the human-readable contract
- Start Conditions:
  - human-readable contract updated
- Inputs:
  - revised human-readable contract
- Read:
  - `report/aci-machine-readable-report-contract.md`
  - `report/aci-generic-report-contract.md`
- Write:
  - `report/aci-machine-readable-report-contract.md`
- Do:
  - add matching fields and summary surfaces without renaming the generic model
- Output:
  - revised machine-readable contract
- Acceptance:
  - top-level, summary, and finding fields match the human-readable contract
- Failure Conditions:
  - machine-readable field names drift from the reading contract
- Stop Conditions:
  - samples cannot represent the new field set cleanly
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## RTR-T6

- Purpose:
  - prove the revised triage contract with neutral examples
- Start Conditions:
  - both contracts updated
- Inputs:
  - revised contracts
  - existing sample reports
- Read:
  - `report/examples/`
- Write:
  - `report/examples/`
- Do:
  - update human and machine sample reports to the new triage model
- Output:
  - revised sample reports
- Acceptance:
  - sample reports demonstrate the new fields without relying on internal migration history
- Failure Conditions:
  - sample fields are not defined by the contracts
- Stop Conditions:
  - a sample requires runtime-only evidence
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## RTR-T7

- Purpose:
  - make the new triage surfaces discoverable from the reader path
- Start Conditions:
  - contracts and samples updated
- Inputs:
  - revised report docs
- Read:
  - `README.md`
  - `USER_EVALUATION_INDEX.md`
  - `report/README.md`
- Write:
  - ``
- Do:
  - update report-facing routes so a new reader knows where triage meaning lives
- Output:
  - revised reading guidance
- Acceptance:
  - reader route to triage docs is explicit
- Failure Conditions:
  - route text competes with maintainer-only docs
- Stop Conditions:
  - root surface would grow in the wrong direction
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## RTR-T8

- Purpose:
  - verify that the revised report surface is generically usable
- Start Conditions:
  - reading guidance updated
- Inputs:
  - revised contracts
  - revised samples
- Read:
  - `report/`
  - `README.md`
- Write:
  - `common/refernce/`
- Do:
  - run manual review and, if needed, bounded validation on sample structure
- Output:
  - closure summary
- Acceptance:
  - no reviewed report surface leaves triage meaning ambiguous
- Failure Conditions:
  - remaining ambiguity blocks generic reuse
- Stop Conditions:
  - 5-layer docs drift from actual edits
- Record Destination:
  - summary
- Final Decider:
  - Codex B
