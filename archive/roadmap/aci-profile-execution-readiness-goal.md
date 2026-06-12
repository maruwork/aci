# ACI Profile Execution Readiness Goal

Status: Complete

## Goal

Give `ACI` a bounded common-shelf profile execution surface.

## Complete When

- `ACI` has an explicit profile execution contract
- supported profiles are visible from the common shelf with lane, scope, and analyzer defaults
- the CLI can show the bounded profile catalog without downstream assumptions
- profile boundaries make it clear what the common shelf owns and what still belongs downstream

## Out of Scope

- full downstream repository path selection
- provider-specific workflow orchestration
- project-local trigger routing
- analyzer installation or version management

## Failure Conditions

- profile metadata leaks downstream project assumptions
- profile surface implies execution support that the common shelf cannot actually prove
- profile contract becomes a vague wishlist instead of a bounded execution catalog
