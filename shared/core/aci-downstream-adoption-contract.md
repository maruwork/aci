# ACI Downstream Adoption Contract

Status: Active

## Purpose

Define the bounded downstream adoption model that the common `ACI` shelf is allowed to own.

## What This Contract Owns

- downstream reading order
- carry set from the common shelf
- customize set that downstream maintainers must replace locally
- downstream-owned set that must remain outside the common shelf
- non-carry set that should not be promoted as downstream canonical runtime content

## What This Contract Does Not Own

- one fixed downstream repository layout
- project-local runtime paths
- downstream CI provider wiring
- project-specific waiver, suppression, or baseline content
- project-specific approval workflow

## Adoption Model Fields

Each downstream adoption packet must make these visible:

- `read_first`
- `carry_from_common`
- `customize_downstream`
- `keep_downstream_only`
- `do_not_promote_as_runtime_authority`
- `verify_after_adoption`

## Boundary Rule

The common shelf may explain:

- what generic ACI artifacts exist
- which generic artifacts are intended to be copied or referenced
- which surfaces require local replacement

The common shelf must not decide:

- downstream repository path structure
- project-local trigger rules
- downstream runtime command transport
- project-specific owner routing
- whether a downstream project may honestly claim broader native language coverage than the Python-first boundary defined by the common shelf

Downstream adopters should read `aci-product-boundary-and-coverage-policy.md`
before advertising language coverage, CI-19 completion, or CI-14 supply-chain
breadth to their own users.

## Reading Rule

Use this contract together with:

1. `docs/ACI_DOWNSTREAM_ADOPTION_PACKET.md`
2. `README.md`
3. `shared/runtime/aci-generic-quickstart.md`
