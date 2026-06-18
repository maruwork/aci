# ACI Analyzer Registry Contract

Status: Active

## Purpose

Define the bounded external-analyzer catalog that the common `ACI` shelf is allowed to own.

## What This Contract Owns

- analyzer identity
- analyzer category
- analyzer purpose
- evidence type
- bounded support level
- which generic ACI profiles reference the analyzer by default
- which `CI-*` patterns usually benefit from that analyzer's evidence
- the ownership boundary between common metadata and downstream execution

## What This Contract Does Not Own

- analyzer installation
- version pinning
- CLI flags for third-party analyzers
- provider-specific workflow files
- downstream repository path selection
- project-local analyzer suppressions or waivers

## Registry Fields

Each catalog entry must carry:

- `analyzer_id`
- `category`
- `purpose`
- `evidence_type`
- `support_level`
- `referenced_by_profiles`
- `typical_ci_ids`
- `ownership_boundary`

## Support Levels

### `profile-default`

Meaning:

- the common shelf knows that one or more ACI profiles reference the analyzer as a default evidence source
- the common shelf may show that metadata in the CLI catalog
- the common shelf does not claim that the analyzer is installed or runnable everywhere

### `opt-in`

Meaning:

- the analyzer is cataloged, but it is not part of the bounded profile defaults
- the common shelf may show it in the catalog and availability surfaces
- downstream maintainers must explicitly decide whether to enable it

## Reading Rule

Use this contract together with:

1. `shared/python/aci_analyzers.py`
2. `shared/python/aci_profiles.py`
3. `shared/runtime/aci-cli-and-config-contract.md`
4. `aci-product-boundary-and-coverage-policy.md`

## Boundary Rule

If a future addition needs:

- provider-specific installation steps
- command-line flags
- version policy
- rule-set tuning
- CI vendor wiring

that addition belongs to a later execution or downstream integration shelf, not this registry contract.

The registry contract also does not override the product boundary: cataloged
opt-in analyzers are visible product surfaces, but they are not automatically
part of the completed common executable baseline.
