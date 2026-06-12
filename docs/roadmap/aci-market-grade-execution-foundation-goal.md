# ACI Market-Grade Execution Foundation Goal

Status: Active

## Goal

Reduce the current market-grade gap inventory for `ACI` from a missing-capability list into an execution-ready foundation that can be implemented without re-deciding product structure mid-flight.

## Complete When

- every currently identified missing or weak market-grade surface is assigned to one concrete implementation stream
- each implementation stream has a defined product boundary, output shape, and failure rule
- each implementation stream has explicit pass/fail checkpoints
- the implementation order is fixed strongly enough that coding can begin without reopening major architecture questions

## Streams Covered

- real scan engine
- native detector runtime
- external analyzer runtime
- report generation and schema validation
- baseline / suppression / waiver runtime
- scope control and ignore policy
- security taxonomy expansion
- secrets / dependency / IaC / container strategy
- SARIF and hosted integration
- quality gates
- verification hardening
- test expansion
- performance and safety hardening
- CI and release hardening

## Out Of Scope

- public release execution
- hosted SaaS product design
- commercial packaging or pricing

## Failure Conditions

- any market-grade gap remains unassigned to a stream
- streams overlap so heavily that implementation order is ambiguous
- the work is described as aspiration instead of verifiable product behavior
