# ACI Baseline Suppression And Waiver Readiness Goal

Status: Complete

## Goal

Define and implement the minimum generic operating model for:

- baseline
- suppression
- waiver
- new vs existing finding separation

so `ACI` can be used repeatedly without treating all findings as brand-new every run.

## Complete When

- `ACI` has an explicit baseline/suppression/waiver contract
- the model stays generic and does not depend on downstream storage
- finding and report surfaces can distinguish new findings from existing baseline findings
- suppression and waiver are narrow and reviewable concepts, not vague ignore buckets

## Out of Scope

- downstream database persistence
- organization-specific approval workflow
- hosted exception management UI

## Failure Conditions

- suppression becomes a broad catch-all for discomfort
- waiver has no owner/review condition
- baseline is described but cannot be represented in the common shelf
