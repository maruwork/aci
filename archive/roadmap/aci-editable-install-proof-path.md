# ACI Editable Install Proof Path

Status: Complete

## Path

1. define the bounded editable-install proof scope
2. define the temporary-environment proof model
3. add verification contract and helper
4. execute editable-install proof in a temporary environment
5. update reader routes and close

## Stop When

- proof would require changing the user’s permanent Python environment
- proof depends on external package registry access
- one proof step would break the reviewed CLI surface without a bounded replacement
