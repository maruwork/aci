# ACI Analyzer Integration Readiness Goal

Status: Complete

## Goal

Give `ACI` a bounded common-shelf external-analyzer integration surface.

## Complete When

- `ACI` has an explicit analyzer registry contract
- supported analyzer metadata is visible from the common shelf
- analyzer ownership boundaries are documented
- the CLI can show the common analyzer catalog without downstream assumptions

## Out of Scope

- installing third-party analyzers
- provider-specific workflow wiring
- downstream project analyzer configs

## Failure Conditions

- analyzer metadata leaks downstream project assumptions
- analyzer surface implies support that the common shelf cannot actually prove
- analyzer contract becomes a vague wishlist instead of a bounded registry
