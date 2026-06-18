# ACI Downstream Adoption Packet

Status: Active

## Purpose

Give a downstream maintainer one bounded packet that explains how to adopt `ACI` without confusing common authority and local project authority.

## Read First

1. `README.md`
2. `shared/core/aci-autonomous-code-inspection-tool-contract.md`
3. `shared/core/aci-code-inspection-execution-spec.md`
4. `shared/core/aci-product-boundary-and-coverage-policy.md`
5. `shared/core/aci-downstream-adoption-contract.md`
6. `shared/runtime/aci-generic-quickstart.md`
7. `domains/README.md`

## Carry From Common

Downstream maintainers should carry or reference these generic surfaces:

- `shared/core/`
- `shared/python/`
- `shared/runtime/`
- `shared/report/`
- `domains/` only for the domain pack they actually use
- `shared/core/aci-baseline-suppression-waiver-contract.md`
- `shared/core/aci-analyzer-registry-contract.md`
- `shared/core/aci-profile-execution-contract.md`
- `shared/report/aci-generic-report-contract.md`
- `shared/report/aci-machine-readable-report-contract.md`

## Customize Downstream

Downstream maintainers must replace or decide these locally:

- target repository scope
- include/exclude paths
- project-local trigger routing
- project-local runtime command transport
- analyzer installation and command flags
- local baseline / waiver / suppression content
- downstream output location and persistence wiring

## Keep Downstream Only

These belong to the downstream repository and must not be treated as common-shelf authority:

- current project state
- local runtime owner rules
- project-specific approval logic
- project-specific CI workflow files
- project-specific validation registers
- project-local operator manuals

## Do Not Promote As Runtime Authority

These common-shelf surfaces are reference or compatibility material, not downstream runtime authority by themselves:

- `examples/`
- maintainer history documents
- private/public release-prep documents
- bridge documents for domains that the downstream project does not use

## Verify After Adoption

After local adoption, verify at minimum:

1. the selected domain pack loads
2. `python .../aci_cli.py smoke` still works in the local bounded setup
3. report samples and machine-readable outputs match the downstream-selected contract
4. local baseline / waiver / suppression policy is explicit
5. project-local runtime and CI wiring are documented outside the common shelf
