# ACI Generic Report Contract

Status: Active

## Purpose

Define a domain-independent, human-readable ACI report format that lets an operator understand:

- what was checked
- what was found
- what is blocked
- what to do next

## Required Header

- `report_id`
- `tool_id`
- `mode`
- `domain`
- `scan_scope`
- `generated_at`
- `verification_status`

## Required Summary

- total findings
- findings by severity
- findings by confidence
- findings by actor label
- findings by triage state
- findings by priority
- findings by baseline status
- findings by lifecycle state
- findings by owner lane
- findings by scope class
- findings split into gated vs advisory-only scope policy buckets
- advisory-only findings by scope class
- waived finding count
- suppressed finding count
- new finding count
- existing baseline count
- resolved baseline count
- blocker present or not
- residual present or not
- next action summary

## Required Finding Row

Each finding should expose:

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
- `owner_lane`
- `scope_class`
- `target_file`
- `line`
- `reason`
- `evidence_ref`
- `recommended_action`
- `verification_status`

## Required Operator Sections

- `Blockers`
- `Advisory-Only Findings`
- `Highest Severity Findings`
- `Triage View`
- `Residuals`
- `Next Actions`

Filtered report views may also include a `Report View` note that shows:

- which `scope_class` / `owner_lane` filters were applied
- how many findings are visible vs hidden
- whether the source scan gate was stricter than the projected view

## Actor Label Rule

Use one of:

- `ACI-detected`
- `manual refinement of ACI output`
- `manual-only gap`

Never blur them together in one row.

## Triage State Rule

Use one of:

- `fix-now`
- `review-first`
- `accepted-residual`
- `monitor`

## Priority Rule

Use one of:

- `P0`
- `P1`
- `P2`
- `P3`

## Fixability Rule

Use one of:

- `direct-fix`
- `owner-decision`
- `design-review`
- `monitor-only`

## Baseline Status Rule

Use one of:

- `new`
- `existing-baseline`

## Waiver Status Rule

Use one of:

- `none`
- `active-waiver`

## Lifecycle State Rule

Use one of:

- `open`
- `in-review`
- `accepted`
- `closed-fixed`
- `closed-no-action`

## Readability Rule

- blocker information must appear before long finding tables
- severity ordering must be descending
- triage information must make `fix-now`, `review-first`, and `accepted-residual` visible without guessing
- advisory-only findings from tests / fixtures / docs / support shelves must be visibly distinct from gated runtime findings
- baseline, suppression, and waiver meaning must not be conflated
- lifecycle meaning must be visible without inferring it from triage or waiver fields
- next action must name the file, owner lane, or next report to read
- one finding row should make owner responsibility visible without requiring the reader to jump to another section
