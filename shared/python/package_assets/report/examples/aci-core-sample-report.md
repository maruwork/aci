# ACI Core Sample Report

Status: Active

## Header

- `report_id`: `aci-core-sample-001`
- `tool_id`: `aci_scan`
- `mode`: `aci runtime scan`
- `profile_id`: `full`
- `domain`: `core-only`
- `scan_scope`: `repo-root`
- `generated_at`: `2026-06-18T00:00:00Z`
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
- by owner lane:
  - `native-static`: `1`
- by scope class:
  - `runtime-source`: `1`
- by scope policy:
  - `gated`: `1`
  - `advisory`: `0`
- waived finding count: `0`
- suppressed finding count: `0`
- new finding count: `1`
- existing baseline count: `0`
- resolved baseline count: `0`
- blocker present: `no`
- residual present: `no`

## Highest Severity Findings

| finding_id | ci_id | signal | severity | confidence | owner_lane | scope_class | target_file | line | reason |
|---|---|---|---|---|---|---|---|---:|---|
| `F-CORE-001` | `CI-04` | `CI04_GOD_CLASS` | `medium` | `medium` | `native-static` | `runtime-source` | `shared/python/aci_scan.py` | 222 | `Class ScanSession has 16 methods across 3 responsibility clusters (LCOM >= 0.67).` |

## Advisory-Only Findings

- none

## Known Limits

- `KL-ACI-CI05-STRUCTURE-EXACT`
- `KL-ACI-CI07-COMPILED-EXTENSIONS`
- `KL-ACI-CI14-SUPPLY-CHAIN-SCOPE`
- `KL-ACI-CI22-NONLOCAL-LIFECYCLE`
- `KL-ACI-CI14-CI25-IMPORT-ALIAS`
- `KL-ACI-CI14-TAINT-INTRAPROCEDURAL`

## Next Actions

- review `shared/python/aci_scan.py:222` for god-class refactoring opportunity
- split `ScanSession` by responsibility cluster if coupling is not intentional
