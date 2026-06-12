# ACI Independence Checkpoints

Status: Complete

## CP1 Current Inventory

- Prevents: starting refactor without knowing what is mixed
- Entry: current `epo root` is readable
- Exit: core, Pier-dependent, runtime, report, persistence, and healthcheck-related elements are classified

## CP2 Target Structure

- Prevents: ad hoc moves without a target model
- Entry: CP1 complete
- Exit: target shelf and responsibility split are defined

## CP3 Boundary Rules

- Prevents: runtime/report/persistence/healthcheck concerns mixing again
- Entry: CP2 complete
- Exit: allowed dependency directions and owner boundaries are fixed

## CP4 Domain Pack Rules

- Prevents: Pier extraction becoming one-off and unreusable
- Entry: CP3 complete
- Exit: `Pier` domain shape and future domain promotion rules are fixed

## CP5 Five-Layer ACI Docs

- Prevents: ACI independence depending on external workstream context
- Entry: CP4 complete
- Exit: goal, path, checkpoints, tasks, and design docs exist under `epo root`

## CP6 Shelf Refactor And Verification

- Prevents: design-only closure with no shelf change
- Entry: CP5 complete
- Exit: `epo root` reflects the independence structure and passes minimum consistency checks

## Closure Note

- `ACI independence` closes at CP6
- later generic inspection-item work belongs to a separate hardening wave
