# ACI Profile Execution Contract

Status: Active

## Purpose

Define the bounded profile execution catalog that the common `ACI` shelf is allowed to own.

## What This Contract Owns

- profile identity
- profile purpose
- enabled lanes
- default external analyzers
- control lane
- scope mode
- bounded support level
- ownership boundary between common metadata and downstream execution

## What This Contract Does Not Own

- downstream repository path selection
- project-local trigger routing
- provider-specific workflow files
- third-party analyzer installation
- downstream severity overrides
- project-local include/exclude configuration

## Profile Fields

Each catalog entry must carry:

- `profile_id`
- `purpose`
- `enabled_lanes`
- `default_external_analyzers`
- `control_lane`
- `scope_mode`
- `support_level`
- `ownership_boundary`

## Support Levels

### `common-catalog`

Meaning:

- the common shelf can describe the profile and its bounded defaults
- the common shelf can show the profile in the CLI catalog
- the common shelf does not claim that the profile is fully runnable against every downstream repository without local scope and runtime decisions

## Scope Modes

- `project-entry-default`
  - the common shelf knows the profile starts from generic project entry/current/runtime shelves
- `bounded-target-required`
  - the profile expects a bounded target scope rather than a blind full-repository run
- `profile-defined`
  - the profile meaning is fixed at the common shelf level and does not require project-local trigger rules to understand its intent

## Reading Rule

Use this contract together with:

1. `shared/python/aci_profiles.py`
2. `shared/python/aci_profile_catalog.py`
3. `shared/runtime/aci-cli-and-config-contract.md`

## Boundary Rule

If a future addition needs:

- provider-specific job wiring
- runtime shell transport behavior
- downstream repository include/exclude patterns
- project-local authority routing

that addition belongs to a later execution or downstream integration shelf, not this profile execution contract.
