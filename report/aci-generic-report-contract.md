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
- findings by actor label
- blocker present or not
- residual present or not
- next action summary

## Required Finding Row

Each finding should expose:

- `finding_id`
- `ci_id`
- `signal`
- `severity`
- `actor_label`
- `owner_lane`
- `target_file`
- `line`
- `reason`
- `evidence_ref`
- `recommended_action`
- `verification_status`

## Required Operator Sections

- `Blockers`
- `Highest Severity Findings`
- `Residuals`
- `Next Actions`

## Actor Label Rule

Use one of:

- `ACI-detected`
- `manual refinement of ACI output`
- `manual-only gap`

Never blur them together in one row.

## Readability Rule

- blocker information must appear before long finding tables
- severity ordering must be descending
- next action must name the file, owner lane, or next report to read
- one finding row should make owner responsibility visible without requiring the reader to jump to another section
