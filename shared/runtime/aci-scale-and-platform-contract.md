# ACI Scale And Platform Contract

Status: Active

## Purpose

Define the bounded common-shelf proof surface for large-repository scan budgets
and continuous multi-OS verification.

## Scale Check Command

Use:

```bash
python shared/python/aci_cli.py scale-check --scratch-root workspace/scale-check
```

The emitted JSON records:

- synthetic repository scenarios
- scan runtime budgets per scenario
- measured elapsed time per scenario
- analyzer runtime budgets
- current analyzer availability snapshot
- the CI platform matrix ACI continuously verifies

## Current Scan Budgets

- `medium-python-repo`
  - `250` files
  - budget: `8.0` seconds
- `large-python-repo`
  - `1000` files
  - budget: `35.0` seconds

These are bounded maintainer budgets for the common shelf's native scan lane
with external analyzers disabled.

## Current Analyzer Runtime Budgets

- `ruff`: `10.0` seconds
- `pyflakes`: `10.0` seconds
- `mypy`: `45.0` seconds
- `pytest`: `60.0` seconds
- `semgrep`: `45.0` seconds
- `eslint`: `30.0` seconds
- `tsc`: `45.0` seconds
- `shellcheck`: `20.0` seconds
- `sqlfluff`: `20.0` seconds

These budgets are explicit operator expectations for common CI-sized targets.
They are recorded even when a given analyzer is unavailable on the current host.

## Continuous Platform Matrix

The common shelf is continuously verified on:

- `ubuntu-latest`
- `windows-latest`
- `macos-latest`

Current Python matrix:

- Linux: `3.11`, `3.12`
- Windows: `3.11`
- macOS: `3.11`

## Boundary

This contract does not claim:

- a guarantee for every repository shape or every file count below the hard cap
- identical runtime on all hardware classes
- external-analyzer performance parity when downstream projects add custom rules
