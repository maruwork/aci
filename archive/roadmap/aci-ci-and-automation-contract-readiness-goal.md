# ACI CI And Automation Contract Readiness Goal

Status: Complete

## Goal

Define and implement the minimum generic CI and automation contract for `ACI`.

## Complete When

- `ACI` has a bounded automation-oriented command surface
- CI-facing exit behavior is explicit
- machine-readable output is sufficient for automation consumption
- docs explain how to use the common shelf in repeatable automation

## Out of Scope

- organization-specific CI provider setup
- downstream repository workflow files
- hosted dashboards

## Failure Conditions

- CI contract depends on one vendor workflow
- automation surface duplicates downstream runtime ownership
- exit behavior stays ambiguous
