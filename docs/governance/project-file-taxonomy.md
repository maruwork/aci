# ACI Project File Taxonomy

Status: Active

## 1. Purpose

Fix the canonical shelf for each ACI file type; prevent public-facing contracts from mixing with support files or residue.

## 2. Entry Rule

- delegated AI entry:
  - `AGENTS.md`
- human entry:
  - `README.md`
- governance entry:
  - `docs/governance/project-template-adoption-packet.md`

## 3. Placement Matrix

| file type | canonical shelf | examples | notes / enforcement |
|---|---|---|---|
| `current canonical docs` | repo root, `shared/core/`, `shared/runtime/`, `shared/report/` | `README.md`, release contracts | public-facing docs may stay at root |
| `governance / policy` | `docs/governance/`, `common/policies/` | adoption packet, taxonomy, boundary register | project-local governance goes under `docs/governance/` |
| `design / architecture` | `docs/design/` | readiness design docs | support, not daily current |
| `task / work tracking` | `docs/tasks/`, `docs/roadmap/` | task boards, goal/path/checkpoints | support, not canonical current |
| `runtime / tool code` | `shared/python/`, `shared/core/`, `shared/runtime/`, `domains/` | CLI, contracts, domain packs | caller-sensitive |
| `tests` | `shared/tests/` | pytest files, expected contract fixtures | runtime-adjacent verification |
| `config / schema` | repo root | `pyproject.toml`, `aci.example.toml` | caller-sensitive root config |
| `templates / reusable assets` | `shared/runtime/templates/`, `shared/report/templates/`, `common/templates/` | canonical templates | legacy `templates/` archived 2026-06-09 |
| `workspace / scratch` | `workspace/` | one-off review files | not canonical |
| `generated reports or residue` | `workspace/`, `.pytest_cache/`, `build/`, `aci.egg-info/` | test cache, package residue | not authoritative |
| `archive / historical` | `archive/` | retired mappings | no active write without owner decision |
| `entry / guide surface` | repo root, `docs/` | `AGENTS.md`, `CLAUDE.md`, token optimization note | keep thin |
| `reference shelf` | `shared/report/examples/`, `domains/{domain}/examples/` | sample reports, domain samples | not daily current; root `examples/` designated for e2e packs (pending T39-restore) |

## 4. Root Rule

- root keeps GitHub community files (README, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, SUPPORT, CHANGELOG, AGENTS, CLAUDE), package metadata (`pyproject.toml`, `aci.example*.toml`), and hidden config (`.gitignore`, `.claudeignore`)
- public-facing supplementary docs (NON_GOALS, VERSIONING_POLICY, ACI_SHELF_CLASSIFICATION, etc.) live in `docs/` as of 2026-06-10
- new root support docs should be avoided when an existing shelf can explain the role
- governance-local additions should go to `docs/governance/`

## 5. Workspace Rule

- active workspace is `workspace/`
- generated residue under `.pytest_cache/`, `build/`, and `aci.egg-info/` is not a new canonical write target
- `aci.egg-info/` is regenerated at the repo root by `pip install -e .` whenever `pyproject.toml` is present at the root; standard Python packaging behavior; cannot be moved or deleted; registered in `.gitignore`
- scratch files must not be promoted without updating governance docs

## 6. Archive Rule

- archive over delete
- `archive/` remains historical only
- archive contents do not define current topology
