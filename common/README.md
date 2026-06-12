# PJ Template

Purpose: the canonical shared template shelf for structuring projects.

This shelf does not store any one project's current state or operating results.
It stores only the reusable structure for how a project is organized, guided, decomposed, and advanced.

## Quick Map

```text
pj-template/
|- README.md
|- frameworks/   methods, progression models, and review lenses
|  |- core/
|  |- support/
|  `- review/
|- policies/     reusable rules grouped by enforcement role
|  |- gates/
|  |- operations/
|  |- structure/
|  `- publication/
|- templates/    reusable document starters
|- checklists/   reusable verification lists
`- examples/     small support examples
```

## Shelf Boundary

- `frameworks/`: how to think, decompose, progress, review, and decide
- `policies/`: what must be followed while doing the work, grouped by rule type
- `templates/`: what to start from when creating a document
- `checklists/`: what to verify before calling work done
- `examples/`: support material only, not first-read authority

## Read First

1. `frameworks/core/progression-rule.md`
2. `frameworks/core/integration-audit.md`
3. `frameworks/core/goal-path-checkpoint-design.md`
4. `policies/gates/execution-readiness.md`

Read shelf READMEs only when needed.
Do not start with `ps-suite` or `RISEN` unless they are directly relevant.

## Canonical Terms

Use these labels consistently throughout the template:

- `progression rule`
- `template-side rule`
- `project-specific rule`
- `completion definition`
- `current location`
- `stop reason`
- `writeback destination`

Do not rename the same idea in different places.
When adapting the template into a project, align to these labels first and add local wording only after that.
Write simply. Do not spend time making a simple rule look more complex than it is.

## Three-Layer Split

- `progression rule`: highest shared authority for subject, progression, stop conditions, and re-grounding
- `template-side rule`: shared concretization for applying the higher rule inside projects
- `project-specific rule`: one project's purpose, current state, runtime facts, and owner judgment

Lower layers must not conflict with higher layers.

## Default Root Agent Files

`pj-template` assumes both Codex and Claude Code are first-class targets.

- keep root `AGENTS.md` for the Codex entry route
- keep root `CLAUDE.md` for the Claude Code entry route
- if either file is absent during adoption, install it rather than leaving the route implicit

## Placement Rule

Keep on the template side:

- progression method and completion path
- entry-surface structure
- `current / support / historical / generated` separation
- external-tool placement
- restart, handoff, and publication responsibility
- structure-cleanup expectations

Keep on the project-specific side:

- completion definition
- current canonical surface
- runtime, DB, and caller facts
- owner-only decisions
- project-local paths, shelf names, commands, and constraints

Do not put here:

- any specific project's current state
- any specific project's task state
- any specific project's operating log
- any specific project's register body

## Replace Per Project

- entry-file paths
- file names for viewing the current state
- command names
- shelf names
- root `design/` adoption and exact design-shelf path
- project-local rule names

## Reference Boundary

Use `../reference/` only for history or failure analysis.
Current authority still lives under `pj-template`.

For time-bound judgment calls and audit-wave notes split out of `frameworks/core/integration-audit.md`, read `../reference/pj-template-progression-rule-audit-history-20260608.md`.
