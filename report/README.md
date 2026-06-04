# ACI Report Layer

Status: Active

## Purpose

This shelf defines human-readable and owner-facing ACI reporting contracts.

## Placement Decision

`report/` remains a top-level shelf.
Reason: report is an owner boundary that consumes normalized findings after runtime, and should not be treated as a runtime subfeature.

## Owns

- remediation handoff format
- actor label rendering contract
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
- `templates/aci-report-remediation-brief-template.md`

## Public Samples

- `examples/aci-core-sample-report.md`
- `examples/aci-core-sample-report.json`
- `examples/aci-pier-sample-report.md`
- `examples/aci-pier-sample-report.json`

Use these before reading downstream project reports if you only want to evaluate the common ACI output shape.
