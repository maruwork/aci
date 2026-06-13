# ACI Versioning Policy

Status: Active

## Purpose

Make version bump decisions explicit at the common-shelf level.

## Rule

Use semantic versioning intent:

- `MAJOR`
  - incompatible contract or CLI behavior change
- `MINOR`
  - new bounded product capability without breaking existing reviewed routes
- `PATCH`
  - bug fix, wording fix, or bounded implementation correction that preserves reviewed contracts

## Evaluate Changes By Surface

- CLI/config
- report contract
- fixture contract
- automation contract
- core inspection contract
- downstream adoption packet

If one surface changes in a way that breaks existing maintainer expectations, do not call it a patch.

## Not This Policy

This policy does not choose the exact next version number by itself.
It only states what kind of bump the reviewed change implies.

Support-window promises are defined separately in the maintainer release documentation.
