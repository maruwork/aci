# ACI Healthcheck Integration

Status: Active

## Purpose

This shelf is the bounded connection surface between `ACI` and a healthcheck-capable caller or observer.

## Owns

- healthcheck connection contract
- what healthcheck may read from ACI outputs
- what blocked or missing ACI outputs mean at integration time

## Must Not Own

- core signal definitions
- domain vocabulary
- report classification semantics
- persistence schema ownership

## Design Rule

Healthcheck integration may consume runtime/report/persistence outputs, but it must not redefine ACI owner boundaries.

## Contract

- `healthcheck_contract.md`
