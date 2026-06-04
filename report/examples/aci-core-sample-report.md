# ACI Core Sample Report

Status: Active

## Header

- `report_id`: `aci-core-sample-001`
- `tool_id`: `aci_core_smoke`
- `mode`: `aci core only`
- `domain`: `core-only`
- `scan_scope`: `common/aci`
- `generated_at`: `2026-06-04`
- `verification_status`: `executed`

## Summary

- total findings: `1`
- by severity:
  - `medium`: `1`
- by actor label:
  - `ACI-detected`: `1`
- blocker present: `no`
- residual present: `no`
- next action summary:
  - inspect the reported structure seam and decide whether to close the bridge

## Highest Severity Findings

| finding_id | ci_id | signal | severity | actor_label | owner_lane | target_file | line | reason | evidence_ref | recommended_action | verification_status |
|---|---|---|---|---|---|---:|---|---|---|---|---|
| `F-CORE-001` | `CI-27` | `PATCHWORK_GRAFT` | `medium` | `ACI-detected` | `human-judgment` | `README.md` | 1 | `Temporary bridge language remains visible in the common shelf and needs explicit closure judgment.` | `design/aci-ci27-patchwork-structure-design.md` | close the bridge and leave one clear authority surface | `executed` |

## Next Actions

- read `design/aci-ci27-patchwork-structure-design.md`
- confirm whether the bridge is still intentionally temporary
