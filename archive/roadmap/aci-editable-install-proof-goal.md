# ACI Editable Install Proof Goal

Status: Complete

## Goal

Prove that `ACI` can be installed from the current shelf through a bounded editable-install route and invoked as `aci`.

## Complete When

- a bounded editable-install proof route is explicit
- one temporary environment proof path is documented
- `aci` command invocation is verified from that temporary environment
- reader guidance explains what this proof covers and what remains out of scope

## Out of Scope

- registry publishing
- wheel upload
- cross-platform installer parity
- downstream project rollout

## Failure Conditions

- editable-install proof is claimed without an executed proof path
- temporary-environment proof is mixed with permanent host changes
- verification still depends on oral explanation
