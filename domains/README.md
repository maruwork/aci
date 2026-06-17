# ACI Domain Packs

Status: Active

## Purpose

Entry point for `ACI` optional domain packs.

## Boundary Rule

- `common` canonical shelf:
  - `shared/core/`
  - `shared/python/`
  - `shared/runtime/`
  - `shared/report/`
- `domain pack`:
  - domain-specific vocabulary
  - domain-specific exclusions
  - domain-specific bridge reading docs
- `bridge docs`:
  - bridge layer for reading domain-specific integration from the common side
  - must not redefine generic `ACI` contracts

## Reading Rule

1. read generic `ACI` from `README.md` and `docs/USER_EVALUATION_INDEX.md`
2. read `domains/` only when using a domain pack
3. for a selected domain, trace bridge docs from that domain pack's README

## Available Packs

- `custom-template/`
  - starting point for creating a new domain pack; copy and fill in `REPLACE_ME` placeholders
