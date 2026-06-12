# ACI Generic Hardening Design

Status: Complete

## Theme

`ACI generic hardening`

## Current Scope

- `CI-27 Patchwork Structure`
- sample artifact follow-up for the current report contract

## Start Conditions

- `ACI independence` is complete
- generic / domain-bridge boundaries are already fixed

## Readable Locations

- `core/`
- `design/`
- `python/`
- `report/`
- `common/refernce/`

## Writable Locations

- `epo root`
- `common/refernce`

## Must Not Touch

- `Pier` current-spec mainline
- downstream runtime rollout

## Acceptance

- `CI-27` is aligned across spec, design, report, and tool surfaces
- sample artifacts follow the current contract

## Current Judgment

- acceptance achieved
- blocker `none`

## Failure Conditions

- `CI-27` is collapsed back into `CI-03`
- sample artifacts drift from the current report contract again

## Stop Conditions

- a required `CI-27` emit path would need runtime-owner judgment outside the common shelf

## Record Destination

- `epo root` official authority
- `common/refernce` working mirror

## Final Decider

- this thread's `Codex B`
