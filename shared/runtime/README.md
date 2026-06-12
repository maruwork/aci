# ACI Runtime Layer

Status: Active

## Purpose

This shelf defines how a project-local runtime binds `ACI core` and an optional domain pack to callers, scopes, outputs, and post-run actions.

## Owns

- trigger matrix
- scan scope binding
- placeholder replacement contract
- post-run action contract
- baseline / waiver / exception connection points
- runtime/operator-facing boundary constants

## Must Not Own

- signal semantics
- domain vocabulary
- residual classification policy

## Canonical Runtime Documents

- `aci-generic-quickstart.md`
- `shared/runtime/templates/aci-runtime-project-local-integration-template.md`
