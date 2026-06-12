# ACI Core

Status: Active

## Purpose

This shelf names the domain-independent core of ACI.

## Current Physical Mapping

In this standalone repository, the core is represented by:

- `shared/python/`
  - core Python authority
- `shared/report/examples/`
  - domain-independent core example packs

## Rule

- new domain-independent core design decisions should point back to this shelf
- physical Python files for the core live under `shared/python/`
- domain-independent example packs live under `shared/report/examples/`

## Canonical Core Documents

- `aci-autonomous-code-inspection-tool-contract.md`
- `aci-code-inspection-execution-spec.md`
