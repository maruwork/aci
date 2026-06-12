# ACI CLI And Config Readiness Goal

Status: Complete

## Goal

Give `ACI` a product-grade local invocation surface with:

- an explicit CLI entry
- a small stable config schema
- documented exit-code behavior
- updated reader guidance

## Complete When

- `ACI` has an explicit CLI entrypoint in the common shelf
- a bounded config file format is defined and documented
- quickstart and README use the CLI as the first-class execution route
- exit code behavior is explicit enough for repeated local and CI use
- a new user can run `ACI` without reverse-engineering Python modules

## Out of Scope

- analyzer orchestration beyond the current smoke surface
- downstream project-local runtime wiring
- baseline/suppression/waiver persistence

## Failure Conditions

- CLI becomes a thin alias with no stable contract
- config fields leak project-local runtime concerns into common authority
- documentation and implementation drift
