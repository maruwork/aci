# ACI Pier Sample Report

Status: Active

## Header

- `report_id`: `aci-pier-sample-001`
- `tool_id`: `aci_core_smoke`
- `mode`: `aci + pier domain`
- `domain`: `pier`
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
  - `manual refinement of ACI output`: `1`
- by triage state:
  - `accepted-residual`: `1`
- by priority:
  - `P3`: `1`
- by baseline status:
  - `existing-baseline`: `1`
- by lifecycle state:
  - `accepted`: `1`
- waived finding count: `1`
- suppressed finding count: `0`
- new finding count: `0`
- existing baseline count: `1`
- blocker present: `no`
- residual present: `yes`
- next action summary:
  - review whether pier domain rules should be split by responsibility

## Highest Severity Findings

| finding_id | ci_id | signal | severity | confidence | actor_label | triage_state | priority | fixability | baseline_status | waiver_status | lifecycle_state | owner_lane | target_file | line | reason | evidence_ref | recommended_action | verification_status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---:|---|---|---|---|---|
| `F-PIER-001` | `CI-04` | `RESPONSIBILITY_SPROUT` | `medium` | `medium` | `manual refinement of ACI output` | `accepted-residual` | `P3` | `monitor-only` | `existing-baseline` | `active-waiver` | `accepted` | `human-judgment` | `domains/pier/python/pier_domain_rules.py` | 1 | `The pier domain rules file handles both vocabulary configuration and domain registration responsibilities in the same module.` | `core/aci-code-inspection-execution-spec.md` | split distinct responsibilities into separate modules; each module should own one concern | `executed` |

## Triage View

- `fix-now`
  - none
- `review-first`
  - none
- `accepted-residual`
  - `F-PIER-001`

## Residuals

- `R-001`
  - classification: `structural-debt`
  - reason:
    - optional domain guidance can grow faster than the common entry if it is not reviewed
  - next wave:
    - `bounded domain-pack review`

## Next Actions

- review `domains/pier/python/pier_domain_rules.py` for responsibility boundary
- consider splitting vocabulary config from domain registration
- recheck waiver when pier module scope expands
