# ACI Legacy Template Sunset Rule

Status: Active

## Purpose

Define when `templates/` may stop existing as a legacy compatibility shelf.

## Legacy Shelf Scope

- `aci-project-local-integration-template.md`
- `aci-remediation-brief-template.md`
- `aci-validation-decision-register-template.md`

## Removal Preconditions

All must be true:

1. canonical shelves under `runtime/`, `report/`, and `persistence/` remain stable
2. downstream references have been updated to canonical shelves
3. no supported runtime copy still depends on `templates/` as the primary path
4. removal note is added to `README.md`

## Until Then

- legacy templates remain read-only compatibility surfaces
- canonical shelves remain the primary reading and adoption surfaces
- new ownership or placement rules must be written in canonical shelves first
