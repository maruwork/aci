# ACI Report State Lifecycle Contract

Status: Active

## Purpose

Define the minimum visible lifecycle for repeated `ACI` findings.

## State Meanings

- `open`
  - newly visible and not yet accepted, waived, or closed
- `in-review`
  - under active human review or design decision
- `accepted`
  - intentionally kept visible as accepted residual work
- `closed-fixed`
  - previously visible and now considered fixed
- `closed-no-action`
  - previously visible and intentionally closed without further work

## Boundary

- baseline answers whether a finding is old or new
- waiver answers whether a visible exception is approved
- lifecycle answers the current visible handling state

These three concepts must not be collapsed into one field.
