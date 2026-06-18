# ACI Analyzer Execution Contract

Status: Active

## Purpose

Define the bounded analyzer execution model that the common `ACI` shelf is allowed to own.

## What This Contract Owns

- analyzer availability check rule
- analyzer execution support level
- profile-level analyzer execution plan shape
- common CLI surfaces that expose those bounded facts

## What This Contract Does Not Own

- third-party analyzer installation
- provider-specific workflow files
- downstream repository target selection
- project-local analyzer flags
- remote CI environment guarantees

## Execution Model Fields

Each bounded analyzer execution surface must make these visible:

- `analyzer_id`
- `availability_check`
- `availability_state`
- `execution_support_level`
- `default_policy`
- `version_policy`
- `setup_hint`
- `remediation_hint`
- `profile_execution_plan`
- `ownership_boundary`

## Availability Rule

The common shelf may report:

- whether the analyzer executable is visible from the current shell environment
- whether the visible analyzer satisfies the bounded minimum-version check
- whether a profile expects that analyzer by default

The common shelf must not report:

- that the analyzer is correctly configured for every downstream repository
- that all analyzer plugins or rules are installed
- that project-local paths are valid

## Support Levels

### `availability-check-only`

Meaning:

- the common shelf can check whether the executable name is visible from the current shell
- the common shelf can expose minimum-version readiness and setup guidance
- the analyzer stays opt-in or downstream-wired; the common shelf does not claim runnable invocation
- deeper runtime correctness remains downstream

### `execution-ready`

Meaning:

- the common shelf can invoke the analyzer executable against a target path
- the common shelf can capture and normalize analyzer output into bounded finding objects
- the common shelf handles bounded exit-code cases including non-fatal states such as pytest exit 5 (no tests collected)
- deeper output correctness, plugin installation, and project-local analyzer flags remain downstream

## Reading Rule

Use this contract together with:

1. `shared/python/aci_analyzer_execution.py`
2. `shared/python/aci_profile_catalog.py`
3. `shared/python/aci_analyzers.py`
4. `shared/runtime/aci-cli-and-config-contract.md`
5. `aci-product-boundary-and-coverage-policy.md`

This contract explains execution readiness. It does not by itself widen the
product boundary into a claim that every cataloged security analyzer is part of
the completed common executable baseline.
