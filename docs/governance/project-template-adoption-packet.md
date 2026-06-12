# ACI Project Template Adoption Packet

Status: Active

## 1. Purpose

Fix local rules for applying `pj-template` to `aci`.

## 2. Reading Route

1. `AGENTS.md`
2. `common/README.md`
3. `docs/governance/project-template-adoption-packet.md`
4. `README.md`
5. `docs/USER_EVALUATION_INDEX.md`
6. `shared/runtime/aci-generic-quickstart.md`
7. `shared/python/`
8. `shared/core/`

### 2.1 Entry Split

- overall understanding entry:
  - `README.md`
- current work entry:
  - `none`
- design entry:
  - `docs/USER_EVALUATION_INDEX.md`
  - `docs/design/`
- execution surface entry:
  - `shared/python/`
  - `shared/runtime/`
  - `shared/core/`
  - `shared/report/`

## 3. Governance Shelf

- governance shelf:
  - `docs/governance/`
- governance shelf entry:
  - `docs/governance/project-template-adoption-packet.md`
- common shelf:
  - `common/`
- common entry:
  - `common/README.md`

### 3.5 Template Branch Decisions

- current ownership:
  - `no-current-canonical`
- restart aid:
  - `restart-aid-none`
- publication mode:
  - `publication-planned`
- structure weight:
  - `standard`
- runtime placement:
  - `runtime-local`

### 3.6 Branch Consequence Record

- current ownership consequence:
  - `none`
- restart aid consequence:
  - `none`
- publication consequence:
  - `archive/docs-release/RELEASE_PREP_INDEX.md`
- runtime consequence:
  - `shared/core/`
  - `shared/python/`
  - `shared/runtime/`
  - `shared/report/`
  - `domains/`

### 3.7 Rule Ownership Split

- what the shared progression rule determines:
  - common principles for project progression, stop, and writeback
- what the template-side branches determine:
  - no-current-canonical
  - publication-planned
  - runtime-local
- what remains truly project-specific:
  - ACI public contract surface
  - package and release documentation
  - domain pack boundaries

### 3.8 Bundle Adoption

- bundle declaration surface:
  - `none`
- continue check surface:
  - `none`
- close / residual split adoption:
  - `no`
- template version status:
  - `upgraded-template scaffold`

## 4. Read / Write / No-Touch

### Read

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `common/`
- `docs/`
- `shared/core/`
- `shared/python/`
- `shared/runtime/`
- `shared/report/`
- `domains/`
- `shared/tests/`
- root release and publication contracts

### Write

- `common/`
- `docs/governance/`
- `docs/`
- `docs/design/`
- `docs/roadmap/`
- `docs/tasks/`

### No-Touch

- `archive/`
- `.pytest_cache/`
- `build/`
- `aci.egg-info/`

## 5. Current Shelf Classification

- current canonical:
  - `README.md`
  - `shared/core/`
  - `shared/python/`
  - `shared/runtime/`
  - `shared/report/`
  - `domains/`
  - `shared/tests/`
  - root public contract and release files
- no-local-current:
  - `no`
- no-current-canonical:
  - `yes`
  - this project does not currently keep a daily current board as its canonical route
- restart aid / handoff only:
  - `none`
- support:
  - `common/`
  - `docs/governance/`
  - `docs/AI_AGENT_RUNTIME_TOKEN_OPTIMIZATION.md`
  - `docs/design/`
  - `docs/roadmap/`
  - `docs/tasks/`
- generated / workspace:
  - `workspace/`
  - `.pytest_cache/`
  - `build/`
  - `aci.egg-info/`
- historical / archive:
  - `archive/`
- hidden active or ignored assets:
  - `.github/`

## 6. Runtime And Caller-Sensitive Paths

- runtime-sensitive paths:
  - `shared/core/`
  - `shared/python/`
  - `shared/runtime/`
  - `shared/report/`
  - `domains/`
- caller-sensitive rename / move:
  - `shared/core/`
  - `shared/python/`
  - `shared/runtime/`
  - `shared/report/`
  - `domains/`
  - `pyproject.toml`

## 7. Expected Local Deliverables

- `common/README.md`
- `common/frameworks/project-progression-rule.md`
- `docs/governance/project-template-adoption-packet.md`
- `docs/governance/project-file-taxonomy.md`
- `docs/governance/project-boundary-register.md`
- `docs/governance/project-workspace-and-artifact-policy.md`

## 8. Output And Reporting

- generated / scratch work:
  - `workspace/`
- governance decision writeback:
  - `docs/governance/`
- generated residue is not canonical
- helper compression surfaces remain non-authoritative

## 8.5 Project-Specific Exception Register

| exception | reason template could not absorb it | related branches | owner decision | keep path |
|---|---|---|---|---|
| root public contracts remain at repo root | public-facing release and packaging docs already use root placement | `publication-planned`, `runtime-local` | no | `README.md` and root contract files |

## 9. Owner-Only Decisions

- archive / restore / delete
- moving or renaming runtime-sensitive shelves
- reclassifying root public docs into archive or support
- final publication go / no-go decisions

## 10. Stop Conditions

- a new top-level shelf becomes necessary
- generated residue appears to become canonical without review
- runtime-sensitive paths would need rename or move
- root public contract placement would need replacement rather than coexistence

## 11. Completion Rule

- governance route is explicit
- local common shelf is explicit
- no-current-canonical status is explicit
- runtime-sensitive paths are explicit
- generated residue is separated from canonical shelves
- owner-only decisions remain owner-only
