# ACI Shelf Classification

Status: Active

## Purpose

This file separates domain-independent `ACI` authority from domain-specific bridge documents.

## Generic ACI Authority

These shelves define reusable `ACI` contracts and must stay domain-independent.

- `shared/core/`
- `shared/python/`
- `shared/report/`
- `shared/runtime/`

## Domain-Specific ACI Documents

These files belong to a selected domain pack or its reviewed persistence bridge.
They are not generic `ACI` authority.

### Pier Domain Pack Bridge

- `domains/pier/aci-pier-integration-spec.md`
- `domains/pier/aci-trigger-read-spec.md`
- `domains/pier/aci-trigger-routing-spec.md`
- `domains/pier/python/pier_domain_rules.py`

### Pier Persistence Bridge

- `domains/pier/aci-pier-validation-decision-register.md`

## Reading Rule

1. Read `shared/core/`, `shared/python/`, `shared/runtime/`, and `shared/report/` first for generic `ACI`.
2. Read `domains/<domain>/` only when that domain pack is selected.
3. Read domain-specific validation registers in `domains/<domain>/` only as reviewed residual bridge material for that domain.

## Must Not Misread

- a domain bridge document is not a generic `ACI` contract
- a reviewed persistence register is not `ACI core`
- project-local current spec remains outside this shelf
