# Shared Policies

This shelf stores reusable operating rules that can be applied across projects.

The documents here are shared concretizations under `project-progression-rule.md`.
Their strength order is:

1. `project-progression-rule.md`
2. each shared rule under `policies/`
3. project-specific rules

Project-specific rules may concretize these shared rules, but must not contradict higher authority.

Keep prose in clear shared English.
File names, status values, classification codes, schema keys, and CLI options should stay in the exact English form needed by tooling.

Treat this shelf as the shared concretization layer under `project-progression-rule.md`.
Follow the first-read order in `../README.md`.

[execution-readiness-gate-policy.md](./execution-readiness-gate-policy.md) is the first pre-start gate.

Do not claim `ready to proceed`, `ready to execute`, `ready to handoff`, or `planning/spec complete` before that gate is passed.

If you need the top-level five-layer model first, read [../frameworks/goal-path-checkpoint-task-design-framework.md](../frameworks/goal-path-checkpoint-task-design-framework.md).

## Baseline For Reuse

- use the five-layer body from the framework shelf directly
- use this shelf for pre-start checks and required work-design rules
- replace paths, file names, and command names per project
- return to `../README.md` if unsure

This is not a shelf for accumulating project-specific rules.
Add only shared concretizations that help projects apply the higher rule.

## Open These Policies First

1. [execution-readiness-gate-policy.md](./execution-readiness-gate-policy.md)
2. [verification-and-retry-policy.md](./verification-and-retry-policy.md)
3. [entry-guide-reference-separation-policy.md](./entry-guide-reference-separation-policy.md)
4. [file-operation-policy.md](./file-operation-policy.md)
5. [naming-and-shelf-policy.md](./naming-and-shelf-policy.md)
6. [external-tool-placement-policy.md](./external-tool-placement-policy.md)
7. [project-template-installation-gate-policy.md](./project-template-installation-gate-policy.md)
8. [project-publication-responsibility-policy.md](./project-publication-responsibility-policy.md)
9. [context-management-policy.md](./context-management-policy.md)

Open agent detail, task detail, and adoption detail only when needed.
Open [external-tool-placement-policy.md](./external-tool-placement-policy.md) before introducing a new external helper, adapter, memory tool, or AI-facing local file.
Treat overlapping policies as later consolidation candidates.
