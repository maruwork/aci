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

Files under `domains/<domain>/` belong to that domain pack. They are not generic `ACI` authority.

Each domain pack owns:
- domain vocabulary and detection rules (`python/<domain>_domain_rules.py`)
- domain-specific bridge documents and integration specs
- domain-specific sample reports and validation registers

Use `domains/custom-template/` as the starting point for a new domain pack.

## Reading Rule

1. Read `shared/core/`, `shared/python/`, `shared/runtime/`, and `shared/report/` first for generic `ACI`.
2. Read `domains/<domain>/` only when that domain pack is selected.
3. Domain-specific validation registers in `domains/<domain>/` are reviewed residual bridge material for that domain only.

## Must Not Misread

- a domain bridge document is not a generic `ACI` contract
- a reviewed persistence register is not `ACI core`
- project-local current spec remains outside this shelf
