# Common Work Session Handoff

## Scope

This handoff is for the `common` cleanup and template-governance work.
It is not for the `veil` review work.

Primary source to continue from:

- `C:\Users\f_tan\project\common`

Local mirrored copy currently visible in this session:

- `C:\Users\f_tan\project\aci\common`

## Current Direction

The goal is to keep `common`, especially `pj-template`, generic, readable, and light without deleting meaning.

Use these defaults:

- write simply first
- do not spend time making a simple rule look more complex than it is
- keep only what is needed
- postpone exceptions
- if unsure, choose the shorter path with fewer branches

This is simplification work, not abstraction-for-its-own-sake work.

## Decisions Already Made

1. `pj-template` is a generic shared template for both Codex and Claude Code.
2. During `pj-template` adoption, root `AGENTS.md` and `CLAUDE.md` must both exist. If either is missing, install it.
3. Root `design/` is allowed when the project declares it as the design / architecture shelf.
4. `ps-suite` and `RISEN` were not split out, but they were demoted in reading priority. They are support material, not the default starting point.
5. `common` should not mix generic guidance with domain-specific material.
6. `common` documents were being trimmed for readability across the whole shelf, not file by file in isolation.
7. The cleanup rule is not "delete aggressively." The rule is "remove avoidable complexity while keeping meaning clear."
8. English is the default for tool-facing and system-facing files. Japanese may still be acceptable for reference notes, imported Japanese material, and rough local memos.

## Important Content Changes Reflected In The Template

- `README.md` now explicitly says to write simply and not complicate simple rules.
- Root-rule wording was softened so `design/` can live at project root when declared.
- External-tool placement was made generic. Do not reintroduce concrete path prescriptions such as `fgn-tools/...` or `workspace/<tool-name>/` into the shared template unless a new explicit decision is made.
- Template text was being shortened by removing repeated warnings, repeated role explanations, and avoidable branching.

## Guardrails

Do not do these in `common` work:

- do not let domain-specific files sit in generic shared shelves
- do not smuggle project-specific operating state into `pj-template`
- do not make a rule more layered or more conditional unless that extra structure is necessary
- do not create new folders when an existing shelf already fits
- do not turn the repo root into a dumping ground
- do not treat temporary handoff notes as template authority

## Where To Reopen First

Start here:

1. `C:\Users\f_tan\project\common\pj-template\README.md`
2. `C:\Users\f_tan\project\common\pj-template\frameworks\core\progression-rule.md`
3. `C:\Users\f_tan\project\common\pj-template\frameworks\core\integration-audit.md`
4. `C:\Users\f_tan\project\common\pj-template\templates\project-file-taxonomy-template.md`
5. `C:\Users\f_tan\project\common\pj-template\policies\structure\external-tool-placement.md`

Then scan the rest of `pj-template` for:

- wording that is still thicker than necessary
- repeated role warnings
- generic / domain mixing
- rules that are technically correct but harder to read than needed

## If The Next Session Continues Editing

Use this order:

1. re-audit `C:\Users\f_tan\project\common\pj-template` as one system
2. fix only real readability, consistency, or scope problems
3. keep wording simple
4. only after that, propagate the updated template into project-local `common` copies if needed

## Output Style Expected In The Next Session

- point only
- no over-explaining
- no contrived findings
- prefer concrete inconsistencies over taste-based comments
- if a statement is uncertain, say so directly

## Note

This handoff is only a restart memo.
Authority stays in the actual files under `C:\Users\f_tan\project\common`.
