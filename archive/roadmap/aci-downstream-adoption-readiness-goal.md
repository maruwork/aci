# ACI Downstream Adoption Readiness Goal

Status: Complete

## Goal

Give `ACI` a bounded downstream adoption surface that another project maintainer can follow without oral explanation.

## Complete When

- `ACI` has an explicit downstream adoption contract
- the common shelf exposes a downstream adoption packet and reading route
- project-local adoption boundaries are documented
- a maintainer can tell what to copy, what to customize, and what must remain outside the common shelf

## Out of Scope

- modifying downstream repositories directly
- provider-specific CI wiring
- project-local runtime shell transport
- project-specific waiver or suppression content

## Failure Conditions

- adoption docs blur common authority and downstream local authority
- adoption packet implies one fixed repository layout for every downstream project
- adoption route still depends on oral explanation
