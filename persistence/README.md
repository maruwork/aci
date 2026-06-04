# ACI Persistence Layer

Status: Active

## Purpose

This shelf defines reviewed residual storage and artifact traceability contracts.

## Classification

- generic persistence contract/templates in this shelf are reusable `ACI` authority
- `aci-pier-validation-decision-register.md` is not generic `ACI` authority
- `aci-pier-validation-decision-register.md` is the reviewed residual bridge for the `Pier` domain

## Placement Decision

`persistence/` remains a top-level shelf.
Reason: persistence is an owner boundary for residual and artifact traceability, and should not be folded into runtime ownership.

## Owns

- validation decision register contract
- artifact retention references
- reviewed residual traceability surface

## Must Not Own

- runtime trigger rules
- signal semantics
- report rendering policy

## Canonical Pier Persistence Document

- `aci-pier-validation-decision-register.md`
