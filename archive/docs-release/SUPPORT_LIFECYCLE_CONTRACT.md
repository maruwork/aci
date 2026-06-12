# ACI Support Lifecycle Contract

Status: Active

## Purpose

Define what `ACI` maintainers support, for how long, and which cases sit outside the generic tool boundary.

## Supported Scope

- latest reviewed release line
- packaged CLI and documented commands
- documented report contracts
- bundled fixtures and package proofs
- optional domain pack surfaces explicitly listed in `domains/README.md`

## Not Supported As Generic ACI

- downstream repository-specific fixes
- unpublished local experiments
- custom forks without their own maintenance owner
- undocumented analyzer integrations
- oral-only operating rules

## Support Windows

- `Current`
  - latest reviewed release line
  - receives bug fixes, contract clarifications, and packaging corrections
- `Previous`
  - immediately previous reviewed release line
  - receives bounded clarification or migration guidance only when the current line already defines the route
- `Older`
  - historical reference only
  - no new fixes are promised at the generic shelf level

## Required Intake Fields

- version or release tag
- install mode
  - repo-local
  - editable install
  - built wheel install
  - source distribution install
- command used
- expected behavior
- actual behavior
- smallest useful evidence excerpt

## Version Transition Rule

When a new reviewed release line becomes `Current`, the former `Current` line becomes `Previous`.

When a line falls outside `Previous`, it becomes `Older` and must not be described as actively supported.

## Fail-Close Rule

Do not claim support for a version, install mode, or analyzer route that is not explicitly covered by reviewed contracts and proof documents.
