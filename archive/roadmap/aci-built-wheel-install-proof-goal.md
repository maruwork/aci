# ACI Built Wheel Install Proof Goal

Status: Complete

## Goal

Prove that `ACI` can be built as a wheel from the current shelf, installed into a bounded temporary environment, and invoked as `aci`.

## Complete When

- a bounded built-wheel proof route is explicit
- one local wheel-build path is documented
- one local wheel-install path is executed successfully in a temporary environment
- reader guidance explains what this proof covers and what remains out of scope

## Out of Scope

- registry publishing
- wheel signing
- cross-platform installer parity
- downstream project rollout

## Failure Conditions

- built-wheel proof is claimed without an executed wheel-install route
- wheel proof silently depends on the editable-install route
- verification still depends on oral explanation
