# ACI Pier Sample Report

Status: Active

## Header

- `report_id`: `aci-pier-sample-001`
- `tool_id`: `aci_core_smoke`
- `mode`: `aci + pier domain`
- `domain`: `pier`
- `scan_scope`: `common/aci`
- `generated_at`: `2026-06-04`
- `verification_status`: `executed`

## Summary

- total findings: `1`
- by severity:
  - `medium`: `1`
- by actor label:
  - `manual refinement of ACI output`: `1`
- blocker present: `no`
- residual present: `yes`
- next action summary:
  - keep official authority in `common/aci` and run mirror sync checks

## Highest Severity Findings

| finding_id | ci_id | signal | severity | actor_label | owner_lane | target_file | line | reason | evidence_ref | recommended_action | verification_status |
|---|---|---|---|---|---|---:|---|---|---|---|---|
| `F-PIER-001` | `CI-27` | `PATCHWORK_GRAFT` | `medium` | `manual refinement of ACI output` | `human-judgment` | `python/aci_working_mirror_sync.py` | 1 | `Working mirror drift remains possible if sync checks are skipped.` | `python/aci_working_mirror_sync.py` | run the bounded sync helper after official five-layer changes | `executed` |

## Residuals

- `R-001`
  - classification: `structural-debt`
  - reason:
    - the working mirror still exists by design
  - next wave:
    - `closed under ACI mirror governance`

## Next Actions

- read `python/aci_working_mirror_sync.py`
- run the bounded sync helper after official five-layer changes
