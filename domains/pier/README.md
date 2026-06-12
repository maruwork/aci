# ACI Pier Domain Pack

Status: Active

## Purpose

This shelf contains investigation vocabulary and rule inputs that are meaningful for `Pier`, but are not part of domain-independent `ACI core`.

## Classification

This shelf is `Pier`-specific.
It is not generic `ACI` authority.
Files here are bridge documents for `aci + pier domain`.

## Owns

- Pier state-plane terms
- Pier persistence vocabulary
- Pier authority-risk vocabulary
- Pier shelf-boundary vocabulary
- Pier-specific exclusions and safe contexts

## Must Not Own

- project-local absolute paths
- project-local output locations
- runtime trigger schedules
- report rendering rules
- persistence backend implementation

## Load Position

`ACI core` loads first.
This domain pack is added when running `aci + pier domain`.

## Reading Route

1. `../README.md`
2. `README.md`
3. `aci-pier-integration-spec.md`
4. `aci-trigger-read-spec.md`
5. `aci-trigger-routing-spec.md`
6. `python/pier_domain_rules.py`

## Bridge Rule

- this shelf may explain how `Pier` reads and routes `ACI`
- this shelf must not redefine generic `ACI` contracts
- domain-specific bridge documents (e.g. validation decision registers) live here in `domains/pier/`
- generic ACI contracts stay in `shared/core/`, `shared/runtime/`, and `shared/report/`

## Canonical Pier Domain Documents

- `aci-pier-integration-spec.md`
- `aci-trigger-read-spec.md`
- `aci-trigger-routing-spec.md`
- `python/pier_domain_rules.py`
- `aci-pier-validation-decision-register.md` (reviewed residual bridge; moved from `persistence/` 2026-06-10)

## Sample Outputs

Pier-specific sample reports live here to keep pier content out of the core `report/` shelf:

- `examples/aci-pier-sample-report.md`
- `examples/aci-pier-sample-report.json`
