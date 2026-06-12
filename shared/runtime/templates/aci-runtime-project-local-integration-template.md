# ACI Runtime Project-Local Integration Template

Status: Active

## Purpose

This is the runtime-layer home for project-local trigger, scope, output, and post-run binding.

## Source Of Truth

This file is the canonical runtime-layer source of truth.

Legacy compatibility path:

- `templates/aci-project-local-integration-template.md`

## Runtime Ownership

This template area owns:

- trigger matrix
- caller and timing binding
- scan scope binding
- report output surface binding
- baseline / waiver / exception connection points

This template area must not own:

- core signal definitions
- domain vocabulary definitions
- residual storage schema
- human-facing report classification semantics
