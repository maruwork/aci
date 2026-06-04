# ACI Generic Quickstart

**Role**: common quickstart for `ACI`.
**Out of Scope**: project-local trigger wiring, caller-proof, validation authority, and project-local current state.

## Reading Rule

This quickstart covers only the shortest scan path for generic `ACI`.
Project-specific trigger, caller-proof, and validation register belong to each project-local integration shelf.

## Quick Evaluation Modes

Use one of these mental modes first:

- `aci core only`
  - confirm generic catalog, finding normalization, and report contract
- `aci + pier domain`
  - confirm optional domain-pack loading and bridge separation

Reusable shelves:

- templates: `templates/`
- examples: `examples/`
- common code: `python/`

Project-local runtime copies may execute the command, but generic code authority remains in the common shelf.

## Fastest Smoke Check

If you only want to see that the common shelf works, use this instead of a downstream runtime command:

```bash
python python/aci_public_smoke.py
```

Expected result:

- `core_only_domain=core-only`
- `pier_domain=pier`
- one normalized finding carrying `ci_id=CI-27`
- mirror sync result

## Project-Local Runtime Note

Project-local runtime commands intentionally do not appear in this common quickstart.
Once you move from `aci core only` to a downstream integration, use that project's runtime shelf for:

- concrete scanner entrypoints
- profile-to-command mapping
- persist/writeback rules
- project-local trigger and caller proof

## First Read Order

1. `inspection_status`
2. `top_level_signals`
3. `ranked_findings`
4. rerun / remediation planning if needed

## Sample Outputs

See:

- `report/examples/aci-core-sample-report.md`
- `report/examples/aci-core-sample-report.json`
- `report/examples/aci-pier-sample-report.md`
- `report/examples/aci-pier-sample-report.json`

## Local Integration Boundary

Use each project-local integration shelf for:

- current trigger wiring
- caller proof
- validation authority
- local current state and projection surfaces
