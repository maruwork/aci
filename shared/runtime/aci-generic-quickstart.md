# ACI Generic Quickstart

Status: Active

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

- templates: `shared/runtime/templates/`, `shared/report/templates/`
- common code: `shared/python/`

Project-local runtime copies may execute the command, but generic code authority remains in the common shelf.

## Fastest Smoke Check

If you only want to see that the common shelf works, use this instead of a downstream runtime command:

```bash
python shared/python/aci_cli.py smoke
```

Expected result:

- `core_only_domain=core-only`
- `pier_domain=pier` — only present when the pier domain pack is installed
- one normalized finding (active CI pattern, e.g. `ci_id=CI-04`)
- repository layout marker
  - monorepo layout includes `mirror_sync`
  - standalone layout intentionally skips working-mirror validation

Config example:

```bash
python shared/python/aci_cli.py --config aci.example.toml smoke
```

See:

- `shared/runtime/aci-cli-and-config-contract.md`
- `shared/runtime/aci-ci-and-automation-contract.md`
- `aci.example.toml`

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

- `shared/report/examples/aci-core-sample-report.md`
- `shared/report/examples/aci-core-sample-report.json`
- `domains/pier/examples/aci-pier-sample-report.md` (pier domain pack)
- `domains/pier/examples/aci-pier-sample-report.json` (pier domain pack)

## Local Integration Boundary

Use each project-local integration shelf for:

- current trigger wiring
- caller proof
- validation authority
- local current state and projection surfaces
