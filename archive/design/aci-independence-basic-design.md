# ACI Independence Basic Design

Status: Complete

## 1. Architecture

```text
ACI Core
  -> Domain Pack (optional)
  -> Runtime Binding
  -> Report Surface
  -> Persistence Surface
  -> Optional Integration Surface
```

## 2. Recommended Direction

- Keep generic signal semantics in `core`
- Move Pier-specific investigation vocabulary into `domains/pier`
- Separate runtime, report, persistence, and integration documentation and adapters
- Keep project-local absolute paths and output locations out of both `core` and `domains`
- In this standalone-project state, keep `python` as the approved physical home of `ACI` core Python, while exposing `core` as the concept shelf
- Keep `examples` as the canonical home of domain-independent core example packs
- Keep `report/` and `persistence/` as top-level shelves because they are owner boundaries, not runtime subfeatures

## 3. Component Roles

| Component | Role | Must Not Own |
|---|---|---|
| `core` | generic signals, profiles, wording, examples | Pier-only vocabulary |
| `domains/pier` | Pier investigation vocabulary and exclusions | project-local paths |
| `runtime` | trigger/scope/binding contract | signal semantics |
| `report` | handoff and human-readable finding contract | trigger behavior |
| `persistence` | residual and artifact record contract | detection logic |
| `integrations/healthcheck` | bounded healthcheck connection | core semantics |

## 4. Interface Direction

- `core` is loaded first
- one domain pack may be added
- runtime binds project-local placeholders
- report and persistence consume normalized findings
- integrations may read outputs but may not redefine owners
- domain selection may be expressed through a bounded helper layer rather than ad hoc imports

## 5. Open Design Questions

- whether a future `python/` -> `core/python/` move has enough benefit to justify compatibility work
- when legacy `templates/` can be removed after downstream migration proves canonical shelves are adopted
