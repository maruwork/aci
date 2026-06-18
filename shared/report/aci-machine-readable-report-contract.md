# ACI Machine-Readable Report Contract

Status: Active

## Purpose

Define the minimum stable field set for machine-readable ACI output.

## Minimum Top-Level Fields

- `report_format_version`
- `report_id`
- `tool_id`
- `tool_version`
- `mode`
- `domain`
- `scan_scope`
- `generated_at`
- `verification_status`
- `gate`
- `summary`
- `findings`
- `blockers`
- `residuals`
- `resolved_baseline_entries`
- `next_actions`

## Summary Fields

- `total_findings`
- `by_severity`
- `by_confidence`
- `by_actor_label`
- `by_triage_state`
- `by_priority`
- `by_baseline_status`
- `by_lifecycle_state`
- `by_owner_lane`
- `by_scope_class`
- `by_scope_policy`
- `advisory_by_scope_class`
- `waived_count`
- `suppressed_count`
- `new_count`
- `existing_baseline_count`
- `blocker_count`
- `residual_count`
- `resolved_baseline_count`

## Finding Fields

- `finding_id`
- `ci_id`
- `signal`
- `severity`
- `confidence`
- `actor_label`
- `triage_state`
- `priority`
- `fixability`
- `baseline_status`
- `waiver_status`
- `lifecycle_state`
- `target_file`
- `line`
- `excerpt`
- `reason`
- `evidence_ref`
- `recommended_action`
- `owner_lane`
- `scope_class`
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

## Optional View Fields

- `report_view`
  - filter metadata for `scope_class` / `owner_lane` projected views
  - source vs visible finding counts
  - source gate decision note when a filtered view is emitted

## Known-Limit Fields

- `known_limits`
  - machine-readable blind spots, recall limits, and explicit coverage boundaries
  - each entry should name the affected CI-ID or signal family and the operator impact

## Stability Rule

- field names must be stable across domains
- domain-specific wording belongs in values, not in field names
