# ACI Report Triage Readiness Path

Status: Complete

## Path

1. inventory the current report contract and identify missing triage fields
2. define the minimum generic triage field set
3. update finding helpers and normalized finding shape where the contract requires it
4. update the human-readable report contract
5. update the machine-readable report contract
6. update sample reports to the new contract
7. update reading guidance for report consumers
8. run manual and smoke-level review on the revised report surface

## Stop Conditions

- a required field would force project-local vocabulary into the common contract
- a new field belongs in runtime or persistence rather than report
- sample reports require a new finding helper field that is not yet designed
- the normalized finding shape would drift from the report contracts

## Dependency Rule

- do not edit sample reports before the triage field set is fixed
- do not close the wave until both contracts and samples match
