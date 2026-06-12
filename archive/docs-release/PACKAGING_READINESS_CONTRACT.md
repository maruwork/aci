# ACI Packaging Readiness Contract

Status: Active

## Purpose

Define the bounded packaging model that the common `ACI` shelf is allowed to own before full package layout work begins.

## What This Contract Owns

- package entrypoint expectation
- layout blocker inventory
- bundled-asset expectation
- repo-local execution vs packaged execution boundary

## What This Contract Does Not Own

- final package migration
- registry publishing
- live release/tag actions
- host-specific release steps

## Packaging Model

The common shelf may define:

- the intended package entrypoint
- which files must remain reachable as packaged assets
- which current layout assumptions block safe packaging work

The common shelf must not claim:

- that `ACI` is already safely installable as a package
- that current relative file loading is package-safe
- that all current repo-local commands work unchanged after packaging

## Required Packaging Surfaces

- CLI entrypoint
- domain-pack loading
- sample report assets
- fixture assets
- documentation indices needed by maintainers

## Reading Rule

Use this contract together with:

1. `PACKAGING_BLOCKERS.md`
2. `PACKAGE_LAYOUT_TARGET.md`
3. `REPO_EXPORT_GUIDE.md`
4. `RELEASE_DISCIPLINE_PACKET.md`
