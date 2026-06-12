# ACI Analyzer Execution Readiness Goal

Status: Complete

## Goal

Give `ACI` a bounded common-shelf analyzer execution surface.

## Complete When

- `ACI` has an explicit analyzer execution contract
- the common shelf can show a bounded execution plan for each supported profile
- the CLI can show analyzer availability checks without downstream assumptions
- analyzer execution boundaries are documented clearly

## Out of Scope

- installing third-party analyzers
- provider-specific workflow wiring
- downstream repository scope selection
- full project-local analyzer flag configuration

## Failure Conditions

- analyzer execution surface implies support the common shelf cannot actually prove
- execution plan starts owning downstream repository wiring
- availability checks depend on project-local oral explanation
