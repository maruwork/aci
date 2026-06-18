# ACI CI And Automation Contract

Status: Active

## Purpose

Define the minimum repeatable automation contract for the common `ACI` shelf.

## Automation Command

Use:

```bash
python shared/python/aci_cli.py automation-smoke
```

Fixture drift check:

```bash
python shared/python/aci_cli.py fixture-check
```

Self-audit surface check:

```bash
python shared/python/aci_cli.py self-audit-check
```

Scale and platform check:

```bash
python shared/python/aci_cli.py scale-check --scratch-root workspace/scale-check
```

## What It Verifies

- domain-pack loading for `core-only` and optional domain packs (such as `<domain>` when installed)
- normalized finding emission
- machine-readable sample report structure
- dedicated self-audit scope and ignore-policy semantics
- bounded scale/runtime budgets for synthetic large-repository scenarios
- the continuously verified CI platform matrix

## Output Rule

- output format is compact JSON
- output is intended for machine consumption first
- output includes:
  - command name
  - verification summary
  - mode checks
  - one finding sample
  - sample report validation checks

## Exit Codes

- `0`
  - automation verification passed
- `2`
  - usage or config error
- `3`
  - runtime failure
- `4`
  - contract error
- `5`
  - automation verification failed

## Boundary

This contract does not own:

- CI provider workflow files
- downstream repository wiring
- fixture-suite guarantees beyond the bounded sample checks in this wave
- arbitrary hardware-level performance guarantees
