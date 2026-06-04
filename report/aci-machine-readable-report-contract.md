# ACI Machine-Readable Report Contract

Status: Active

## Purpose

Define the minimum stable field set for machine-readable ACI output.

## Minimum Top-Level Fields

- `report_id`
- `tool_id`
- `mode`
- `domain`
- `scan_scope`
- `generated_at`
- `verification_status`
- `summary`
- `findings`
- `blockers`
- `residuals`
- `next_actions`

## Summary Fields

- `total_findings`
- `by_severity`
- `by_actor_label`
- `blocker_count`
- `residual_count`

## Finding Fields

- `finding_id`
- `ci_id`
- `signal`
- `severity`
- `actor_label`
- `target_file`
- `line`
- `excerpt`
- `reason`
- `evidence_ref`
- `recommended_action`
- `owner_lane`
- `verification_status`

## Blocker Fields

- `blocker_id`
- `reason`
- `required_decision`
- `resume_condition`

## Residual Fields

- `residual_id`
- `classification`
- `reason`
- `next_wave`

## Stability Rule

- field names must be stable across domains
- domain-specific wording belongs in values, not in field names
