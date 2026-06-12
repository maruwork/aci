# ACI governance entry point

**Last updated**: 2026-06-11

This file is the root stop-rule surface for delegated work inside this repository.

## Scope

- Applies only to `C:\Users\f_tan\project\aci`.
- Root entry for delegated AI is this file, then the canonical ACI route below.

## First Read

1. `README.md`
2. `common/README.md`
3. `docs/governance/project-template-adoption-packet.md`
4. `docs/AI_AGENT_RUNTIME_TOKEN_OPTIMIZATION.md`
5. `docs/USER_EVALUATION_INDEX.md`
6. `shared/runtime/aci-generic-quickstart.md`

## Current Authority

Current canonical shelves:

- `common/` is the local reusable common rule shelf
- `shared/core/`
- `shared/python/`
- `shared/report/`
- `shared/runtime/`
- `domains/`
- `shared/tests/`

Current no-touch historical or generated shelves in this checkout:

- `archive/`
- `.pytest_cache/`
- `build/`
- `aci.egg-info/` as current checkout-generated packaging residue

If ACI is used as an external tool under another repository, the corresponding packaging residue belongs under that tool checkout or other approved local tool path, not by rule at the consuming repository root.

## Distribution Model

- ACI is distributed via `pip install aci` (standard install)
- `shared/python/` maps to the `aci` package and is what reaches end users (via site-packages)
- `shared/core/`, `shared/report/`, `docs/`, `common/`, and all other shelves are developer-only; they are not packaged
- source-embed or editable-install layouts are project-local variants; they do not define a general path rule

## Stop Rule

Stop immediately if work would:

- start from `archive/`
- move, delete, or restore anything under `archive/`
- treat `.pytest_cache/`, `build/`, or checkout-generated residue such as `aci.egg-info/` as canonical authority
- replace root public-facing contracts with governance notes
- rename or move `shared/`, or `domains/` without owner approval

## Current Live Restart Rule

- Treat `docs/governance/project-template-adoption-packet.md` as the local governance route.
- Treat this project as `no-current-canonical` for daily bundle tracking at this time.
- Use `README.md`, `docs/USER_EVALUATION_INDEX.md`, and `shared/runtime/aci-generic-quickstart.md` as the bounded restart route for active understanding.
