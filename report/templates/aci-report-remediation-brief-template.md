# ACI Report Remediation Brief Template

Status: Active

## Purpose

This is the report-layer home for owner-facing remediation handoff.
It should be read after the generic report contracts, not instead of them.

## Source Of Truth

This file is the canonical report-layer source of truth.

Legacy compatibility path:

- `common/aci/templates/aci-remediation-brief-template.md`

## Report Ownership

This template area owns:

- remediation handoff format
- actor label rendering
- verification result rendering
- deferred item rendering

## Upstream Contract

- `common/aci/report/aci-generic-report-contract.md`
- `common/aci/report/aci-machine-readable-report-contract.md`

This template area must not own:

- runtime trigger behavior
- domain detection vocabulary
- persistence backend details
