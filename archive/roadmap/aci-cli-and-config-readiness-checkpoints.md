# ACI CLI And Config Readiness Checkpoints

Status: Complete

## CCR-CP1 CLI Surface

Pass when:
- the minimum supported commands are fixed

## CCR-CP2 Config Schema

Pass when:
- the minimum config file schema is fixed
- config boundaries are explicit

## CCR-CP3 Implementation

Pass when:
- CLI entry and config loader exist and run in the common shelf

## CCR-CP4 Documentation

Pass when:
- quickstart, README, and CLI/config contract agree on usage

## CCR-CP5 Verification

Pass when:
- CLI smoke execution passes
- compile checks pass
- no reviewed inconsistency remains in the new CLI/config surface
