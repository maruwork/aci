# ACI Report Layer

Status: Active

## Purpose

This shelf defines human-readable and owner-facing ACI reporting contracts.

## Placement Decision

`shared/report/` is collected under the `shared/` shelf alongside `shared/core/` and `shared/python/`.
Reason: report is an owner boundary that consumes normalized findings after runtime, and should not be treated as a runtime subfeature.

## Owns

- remediation handoff format
- actor label rendering contract
- triage rendering contract
- verification rendering contract
- deferred-item rendering contract
- generic human-readable report contract
- machine-readable report contract

## Must Not Own

- runtime trigger rules
- storage engine details
- domain detection rules

## Canonical Documents

- `aci-generic-report-contract.md`
- `aci-machine-readable-report-contract.md`
- `shared/report/templates/aci-report-remediation-brief-template.md`

## Public Samples

- `shared/report/examples/aci-core-sample-report.md`
- `shared/report/examples/aci-core-sample-report.json`

Use these before reading downstream project reports if you only want to evaluate the common ACI output shape.

Domain-specific samples live in their respective domain pack:

- `domains/<domain>/examples/` — domain-pack-specific sample reports (when a domain pack is installed)

## Triage Surface

The generic report surface now makes these visible without project-local vocabulary:

- confidence
- triage state
- priority
- fixability
- baseline status
- waiver status

Repeated-operation meaning is split this way:

- baseline
  - visible old debt vs new regression
- waiver
  - visible approved exception on a finding
- suppression
  - narrow filtered noise, counted but not shown as an active finding row

- lifecycle
  - the current visible handling state of a finding
