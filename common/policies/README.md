# Shared Policies

This shelf stores reusable operating rules that can be applied across projects.
Frameworks tell you how to structure work. Policies tell you what is required while doing it.
Use this shelf when you need a gate, placement rule, workflow constraint, or required check.

## Role Map

- `gates/`: start or completion conditions
- `operations/`: day-to-day operating rules
- `structure/`: placement, naming, and reference-boundary rules
- `publication/`: outward-facing responsibility rules

Keep prose in clear shared English.
File names, status values, classification codes, schema keys, and CLI options should stay in the exact English form needed by tooling.

Authority order:

1. `../frameworks/core/progression-rule.md`
2. shared rules under `policies/`
3. project-specific rules

Project-specific rules may concretize these shared rules, but must not contradict higher authority.

## Boundary

Do not use this shelf for thinking models, document starters, or project-specific current-state management.

[gates/execution-readiness.md](./gates/execution-readiness.md) is the first pre-start gate.

Do not claim `ready to proceed`, `ready to execute`, `ready to handoff`, or `planning/spec complete` before that gate is passed.

## Open First

1. [gates/execution-readiness.md](./gates/execution-readiness.md)
2. then open one file per role as needed:
   - operations: [operations/verification-retry.md](./operations/verification-retry.md)
   - structure: [structure/entry-guide-reference.md](./structure/entry-guide-reference.md)
   - publication: [publication/publication-responsibility.md](./publication/publication-responsibility.md)
3. for additional gate work, open [gates/template-installation.md](./gates/template-installation.md)
4. for additional structure work, open [structure/file-operations.md](./structure/file-operations.md), [structure/naming-shelf.md](./structure/naming-shelf.md), [structure/file-role-consistency.md](./structure/file-role-consistency.md), and [structure/external-tool-placement.md](./structure/external-tool-placement.md)
5. for additional operations work, open [operations/context-management.md](./operations/context-management.md)

## Open Later

- agent detail, task detail, and adoption detail only when needed
- use the five-layer body from the framework shelf when you need the higher-level model
- open [structure/external-tool-placement.md](./structure/external-tool-placement.md) before introducing a new external helper, adapter, memory tool, or AI-facing local file
- replace paths, file names, and command names per project
- return to `../README.md` if unsure about shelf boundaries
- treat overlapping policies as later consolidation candidates
