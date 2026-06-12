# ACI Baseline Suppression Waiver Contract

Status: Active

## Purpose

Define the minimum repeated-operation model for `ACI`.

## Concepts

### Baseline

- meaning:
  - a known finding fingerprint that separates old debt from new regression
- effect:
  - a finding may still appear in a report
  - its `baseline_status` becomes `existing-baseline`

### Suppression

- meaning:
  - a narrow filter for noise or intentionally unsupported signals
- effect:
  - the suppressed finding does not appear as an active finding row
  - suppression must still be explainable and countable

### Waiver

- meaning:
  - an approved exception for a visible finding
- effect:
  - the finding remains visible
  - the finding carries a waiver status
  - the waiver must name owner, reason, and review condition

## Common-Shelf Artifact Shape

Use one bounded TOML file with three tables:

- `[baseline]`
- `[suppression]`
- `[waiver]`

The common shelf defines the shape only.
It does not define downstream storage location or approval workflow.

## Minimum Fields

### Baseline Entry

- `fingerprint`
- `ci_id`
- `reason`
- `first_seen`

### Suppression Entry

- `suppression_id`
- `match`
- `reason`
- `reviewer`

### Waiver Entry

- `waiver_id`
- `fingerprint`
- `owner`
- `reason`
- `review_condition`

## Report Contract Effects

- finding rows must distinguish `new` from `existing-baseline`
- finding rows may distinguish `none` from `active-waiver`
- report summary must expose:
  - new finding count
  - existing baseline count
  - waived finding count
  - suppressed finding count

## Boundary

This contract does not own:

- downstream approval policy
- database persistence
- organization-specific exception review workflow
