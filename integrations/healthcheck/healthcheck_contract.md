# ACI Healthcheck Contract

Status: Active

## Purpose

Define the bounded contract between `ACI` outputs and a healthcheck-capable caller or observer.

## Reads Allowed

- runtime execution status
- report existence status
- persistence artifact existence status
- blocked / missing / stale markers produced by the owning layer

## Reads Not Allowed

- raw rewriting of core signal meaning
- domain-pack vocabulary mutation
- direct reinterpretation of owner-lane semantics

## Expected Health States

- `healthy`
  - required runtime/report/persistence surfaces exist
  - no blocking prerequisite is active
- `degraded`
  - outputs exist but one or more bounded prerequisites are missing
  - review or retry is needed
- `blocked`
  - ACI run cannot continue because a prerequisite or gate is unmet
- `unknown`
  - integration surface cannot determine state from bounded outputs

## Ownership Rule

- runtime owns execution readiness
- report owns reporting completeness
- persistence owns traceability presence
- healthcheck integration may summarize those states, but may not redefine them
