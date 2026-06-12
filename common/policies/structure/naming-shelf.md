# Naming and Shelf Policy

**Purpose**: Define the minimum reusable naming and shelf rules that any project should fix before local exceptions are added.

> **Canonical relationship**: This file is the shared baseline. Project-specific naming rules may extend it, but should not weaken the minimum readability rules defined here.

This policy covers:

- file naming
- folder naming
- shelf entry naming
- when a new shelf may be introduced
- when an existing name should be renamed instead of tolerated

This policy mainly targets long-lived documents, governance files, and shared reusable assets.
Source files, toolchain-managed files, vendor material, and imported files may follow stronger local or tool-specific conventions.

- For file moves, archiving, and disposal rules, see `file-operations.md`
- For separation between entry, guide, and reference reading surfaces, see `entry-guide-reference.md`

## 1. Core Goal

Names are not cosmetic.
They are part of operational control.

The minimum target is:

1. a first-time reader can roughly tell what something is without opening it
2. a human or AI can distinguish active, support, generated, and historical material without guessing
3. the repository does not depend on author memory to explain file and shelf roles

## 2. Minimum File Naming Rule

For active long-lived files, prefer names that communicate, when it improves readability, at least:

1. `group`
2. `subject`
3. `form`

In practice, use one of these shapes when it helps readability and no stronger shelf convention exists:

- `subject-form`
- `group-subject-form`

Examples:

- `database-structure-map.md`
- `task-state-model.yaml`
- `design-review-checklist.md`
- `ops-authentication-runbook.md`

### 2.1 What the parts mean

- `group`: which family or operating lane the file belongs to
  - examples: `setup`, `ops`, `test`, `design`, `reference`, `historical`
- `subject`: what the file is about
  - examples: `governance-db`, `notification`, `task-state`
- `form`: how the file is used
  - examples: `overview`, `guide`, `manual`, `policy`, `rules`, `register`, `inventory`, `map`, `matrix`, `checklist`, `runbook`, `template`, `packet`

The exact vocabulary may vary by project.
The important rule is that the name must carry meaning, not just look organized.

## 3. Low-Information Names Are Not Enough

Avoid active names that force the reader to open the file before they can tell what it is.

Weak patterns include:

- `manual-<topic>`
- `guide-<topic>` when the group is still unclear
- `note-<topic>`
- `misc-<topic>`
- `temp-<topic>`
- `new-<topic>`
- `final-<topic>`
- `latest-<topic>`

These are weak when the file's group or role is still unclear.
They may exist in imported, historical, or temporary material, but should not become the default naming style for active canonical files.

## 4. Date and Time Rule

- Do not add dates to active canonical document names.
- Dates or timestamps may be used for:
  - generated outputs
  - logs
  - snapshots
  - exports
  - archived items
  - historical evidence

This keeps active names stable and prevents false distinctions such as `latest`, `v2`, or date-based drift.

## 5. Language and Case

- Use lowercase kebab-case for new reusable document names unless a stronger local convention exists.
- Let code and config filenames follow the norms of their language or toolchain.
- Mixed-language filenames may remain for imported or legacy material, but avoid them for new reusable assets.

## 6. Prefix and ID Rule

Use ID prefixes only when the numbering system itself has meaning in that shelf.

Good use:

- `decision-042-auth-model.md`
- `design-214-runtime-boundary.md`

Bad use:

- adding uppercase prefixes to ordinary shared documents when the number carries no real shelf meaning

If a shelf does not need a numbering system, do not invent one just to make names look formal.

## 7. Minimum Folder Naming Rule

- Use lowercase kebab-case for new long-lived folders unless a stronger project convention exists.
- Folder names should describe role, not author intent.
- Avoid folder names such as:
  - `misc`
  - `temp`
  - `new`
  - `other`
  - `test2`
  - `draft2`

Archive, intake, imported, and legacy groups may keep older names when preserving traceability is more important than normalization.

## 8. Shelf Entry Rule

- Use `README.md` as the default shelf entry file.
- Allow `INDEX.md` only when a compatibility, imported, or legacy reason requires it.

The entry file should make the shelf readable in one pass:

- what belongs here
- what does not belong here
- whether the shelf is current, support, generated, or historical
- where to return for live current authority

## 9. New Shelf Rule

Before adding a new shelf, check whether an existing shelf already explains the same role.

Add a new shelf only when all of the following are true:

1. the role is genuinely different
2. the distinction matters to a reader or operator
3. the shelf can be explained in one entry file or register
4. the project can say whether it is current, support, generated, or historical

If two shelves serve the same reader role, treat them as merge, rename, or archive candidates first.

## 10. Rename Rule

Before renaming an existing file or folder, check:

1. callers
2. records
3. manuals
4. generated outputs
5. hooks
6. tests
7. databases or registries

Rename when the current name creates more misread cost than change cost.
After a rename, recheck the nearest callers, entry surfaces, and references before treating the change as complete.

Typical rename triggers:

- the name does not reveal role
- the shelf now uses a different naming grammar
- current and historical items are mixed under one naming style
- AI or first-time readers repeatedly misread the file's purpose

## 11. Minimum Shelf Classification Rule

Before creating a new file or shelf, classify it into one of these roles:

- `entry`
- `guide`
- `reference`
- `canonical`
- `generated`
- `evidence`
- `archive`
- `temporary`

If it cannot be classified, do not place it in a canonical shelf.

## 12. Anti-Bloat Rule

- When adding a file or folder, also check for removable duplicates, stale explanations, and unnecessary route notes.
- Do not keep multiple names for the same role without an explicit reason.
- Keep every long-lived shelf readable enough that a reader can tell from the shelf entry alone what belongs there and what does not.
