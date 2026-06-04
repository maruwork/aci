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

## Canonical Pier Domain Documents

- `aci-pier-integration-spec.md`
- `aci-trigger-read-spec.md`
- `aci-trigger-routing-spec.md`
- `python/pier_domain_rules.py`
