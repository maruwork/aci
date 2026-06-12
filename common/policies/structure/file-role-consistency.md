# File Role Consistency Policy

**Purpose**: Define a portable rule for editing long-lived documents without letting the filename, opening declaration, and actual reader role drift apart.

> **Canonical relationship**: This file is the shared baseline for role-consistent file editing. Project-specific document labels, opening metadata, and lint commands may extend it, but should not weaken the minimum anti-misread rules defined here.

This policy mainly targets long-lived documents, governance files, and shared reusable assets.
For naming rules, see `naming-shelf.md`.
For entry / guide / reference separation, see `entry-guide-reference.md`.

## 1. Decide the Expected Role from the Name First

Before editing the body, decide what role the file name and path already claim.

Common role labels include:

- `manual`
- `guide`
- `runbook`
- `checklist`
- `template`
- `packet`
- `quickstart`
- `bridge`

Project-local prefixes may also imply role or operating lane, such as `ops-`, `test-`, `rollout-`, or `quickstart-`.

Do not start by rewriting the whole body.
Start by fixing the role the file is supposed to serve.

## 2. Read Only the Opening Surface First

Before broader edits, read only the opening surface and compare it with the expected role from the name.

Check at least:

- title
- explicit `Role` or equivalent opening declaration
- reading position or usage statement
- entry or related links near the top

If the filename and the opening surface disagree, treat that as the first correction target.

## 3. Keep the Role Markers Aligned

For role-bearing documents, keep these four signals aligned:

1. filename
2. title and opening role declaration
3. reading-position statement
4. related-link framing

If one says `checklist` while another behaves like `manual`, fix the mismatch before refining detail.
AI readers misread role drift earlier than humans do.

## 4. State What the File Is Not

When a file is easy to misread, state its negative boundary near the top.

Typical examples:

- this is not the current truth
- this is not the task board
- this is the template itself, not a working copy
- this is a reading bridge, not the canonical rule

Use only the minimum negative boundary needed to stop likely misreads.

## 5. Separate Nearby Files by Job

When similar files live in the same shelf, make their differences explicit.

Examples:

- one file gives sequence only
- another gives detailed procedure
- another gives quick verification only

Do not let nearby files compete for the same reader job without a stated difference.

## 6. Edit in This Order

Use this order unless a stronger local rule exists:

1. filename and expected role
2. opening surface and boundary lines
3. difference from nearby files
4. body detail
5. links, references, and verification

This keeps anti-misread corrections ahead of prose polishing.

## 7. Verify After Editing

After role-related edits, recheck:

- links and related references
- nearby documents that name this file
- entry or guide surfaces that route readers here
- any project-provided lint or consistency checks

If the repository provides them, run a diff check, a reference-link lint, and a strict document-consistency lint before closing the change.
