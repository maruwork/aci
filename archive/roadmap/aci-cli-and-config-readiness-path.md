# ACI CLI And Config Readiness Path

Status: Complete

## Path

1. define the minimum CLI surface
2. define the minimum config schema
3. implement the CLI entry and config loader
4. document exit-code behavior
5. update quickstart and entry docs
6. verify smoke execution through the new CLI

## Stop Conditions

- the proposed CLI requires downstream project context
- the config schema starts owning baseline/suppression concerns
- exit-code behavior cannot stay generic
