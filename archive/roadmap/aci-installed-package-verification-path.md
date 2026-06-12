# ACI Installed Package Verification Path

Status: Complete

## Path

1. define the bounded installed-package verification scope
2. separate editable-install proof from built-artifact proof
3. add verification helper and contract
4. update reader routes and packaging guidance
5. verify and close

## Stop When

- verification would require publishing outside the current shelf
- proof depends on unstated environment assumptions
- one verification step would break the reviewed CLI surface without a bounded replacement
