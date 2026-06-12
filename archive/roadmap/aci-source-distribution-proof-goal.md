# ACI Source Distribution Proof Goal

Status: Complete

## Goal

Prove that `ACI` can be built as a source distribution from the current shelf, installed into a bounded temporary environment, and invoked as `aci`.

## Complete When

- a bounded source-distribution proof route is explicit
- one local source-distribution build path is documented
- one local source-distribution install path is executed successfully in a temporary environment
- reader guidance explains what this proof covers and what remains out of scope

## Out of Scope

- registry publishing
- signed release artifacts
- cross-platform installer parity
- downstream project rollout

## Failure Conditions

- source-distribution proof is claimed without an executed install route
- source-distribution proof silently depends on wheel-only behavior
- verification still depends on oral explanation
