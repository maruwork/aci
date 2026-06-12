# ACI Core Sample Report

Status: Active

## Header

- `report_id`: `aci-core-sample-001`
- `tool_id`: `aci_core_smoke`
- `mode`: `aci core only`
- `domain`: `core-only`
- `scan_scope`: `repo-root`
- `generated_at`: `2026-06-04`
- `verification_status`: `executed`

## Summary

- total findings: `1`
- by severity:
  - `medium`: `1`
- by confidence:
  - `medium`: `1`
- by actor label:
  - `ACI-detected`: `1`
- by triage state:
  - `review-first`: `1`
- by priority:
  - `P2`: `1`
- by baseline status:
  - `new`: `1`
- by lifecycle state:
  - `in-review`: `1`
- waived finding count: `0`
- suppressed finding count: `0`
- new finding count: `1`
- existing baseline count: `0`
- blocker present: `no`
- residual present: `no`
- next action summary:
  - review whether the scanner function should be split by ownership boundary

## Highest Severity Findings

| finding_id | ci_id | signal | severity | confidence | actor_label | triage_state | priority | fixability | baseline_status | waiver_status | lifecycle_state | owner_lane | target_file | line | reason | evidence_ref | recommended_action | verification_status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---:|---|---|---|---|---|
| `F-CORE-001` | `CI-04` | `RESPONSIBILITY_SPROUT` | `medium` | `medium` | `ACI-detected` | `review-first` | `P2` | `owner-decision` | `new` | `none` | `in-review` | `human-judgment` | `python/aci_scan.py` | 351 | `Multiple distinct inspection responsibilities are handled within a single scanner function without explicit ownership boundaries.` | `core/aci-code-inspection-execution-spec.md` | split distinct responsibilities into separate modules; each module should own one concern | `executed` |

## Triage View

- `fix-now`
  - none
- `review-first`
  - `F-CORE-001`
- `accepted-residual`
  - none

## Next Actions

- review `python/aci_scan.py` for responsibility boundary
- decide whether the scan function should be split by ownership
