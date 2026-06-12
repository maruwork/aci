# ACI Project Boundary Register

Status: Active

## 1. Purpose

Fix the class and authority for each ACI shelf.

## 2. Register

| shelf | class | current canonical? | role | notes |
|---|---|---|---|---|
| `README.md` | `front current surface` | `yes` | repo entry | human-readable primary route |
| `AGENTS.md` / `CLAUDE.md` | `front current surface` | `yes` | delegated AI entry | thin route only |
| `common/` | `support` | `no` | local reusable common rules | copied from `pj-template` |
| `docs/governance/` | `support` | `no` | local governance concretization | project-local adoption rules |
| `docs/release/` | `support` | `no` | release and publication process docs | moved from root 2026-06-09; not public-facing contracts |
| `docs/ACI_DOWNSTREAM_ADOPTION_PACKET.md`, `docs/ACI_SHELF_CLASSIFICATION.md`, `docs/DOMAIN_PACK_EXTENSION_GUIDE.md`, `docs/NON_GOALS.md`, `docs/PUBLIC_RUNTIME_ASSUMPTIONS.md`, `docs/USER_EVALUATION_INDEX.md`, `docs/VERSIONING_POLICY.md` | `visible support` | `no` | public-facing supplementary docs | moved from root 2026-06-10; reader-facing but not canonical runtime |
| `docs/AI_AGENT_RUNTIME_TOKEN_OPTIMIZATION.md` | `visible support` | `no` | token optimization local rule | redirects to canonical shelves |
| `shared/core/`, `shared/python/`, `shared/runtime/`, `shared/report/`, `domains/` | `current canonical` | `yes` | tool runtime and contracts | caller-sensitive |
| `shared/tests/` | `current canonical` | `yes` | verification and sample surfaces | bounded runtime proof |
| `docs/design/`, `docs/roadmap/`, `docs/tasks/` | `support` | `no` | design and planning support | not daily current |
| `.pytest_cache/`, `build/`, `aci.egg-info/`, `workspace/` | `generated` | `no` | residue or scratch | never treated as authority |
| `archive/templates/` | `historical` | `no` | legacy compatibility templates; archived 2026-06-09; canonical copies in `shared/runtime/`, `shared/report/` | use canonical shelves |
| `archive/` | `historical` | `no` | retired topology | no active write by default |
| `.github/` | `support` | `no` | community and repo ops metadata | not runtime authority |

## 3. Reading Rules

- read entry first, then governance route, then the exact runtime shelf under change
- support shelves do not replace canonical runtime or contract shelves
- generated shelves never define package truth or current topology

## 4. Minimum Required Shelves

- entry:
  - `AGENTS.md`
  - `CLAUDE.md`
  - `README.md`
- governance:
  - `docs/governance/`
- runtime:
  - `shared/core/`
  - `shared/python/`
  - `shared/runtime/`
- support:
  - `common/`
  - `docs/design/`
  - `docs/roadmap/`
  - `docs/tasks/`
- generated:
  - `workspace/`
  - `.pytest_cache/`
  - `build/`
  - `aci.egg-info/`
- historical:
  - `archive/`

## 5. Boundary Questions

- public-facing supplementary docs (NON_GOALS, VERSIONING_POLICY, etc.) live in `docs/` as of 2026-06-10; they do not replace canonical runtime contracts in `shared/core/`, `shared/runtime/`, `shared/report/`
- generated residue may exist at root-level shelves but must not receive new canonical writes
- archive remains non-current even if it contains older mappings or proofs
