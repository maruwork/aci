# Shared Templates

This shelf stores reusable document starters for use across projects.
Open only the exact template that matches the document you are creating.
Use this shelf when you need a starting structure, not when you need the current truth for one project.

Keep prose in clear shared English.
Exact English should remain where tooling depends on it, such as `Status`, `ID`, `PASS / FAIL`, schema keys, or field names tied to external tools.

Label tokens clearly so a reader can tell whether something is prose, a fixed value, or a code name:

- plain descriptive terms stay plain prose
- fixed values such as `ACTIVE`, `DONE`, `PASS`, or `FAIL` should be described as status or verdict values
- code-level names such as `field_name` or `variable_name` should stay in backticks and be identified by type
- command names, options, and policy names should also be labeled by type

## Open First

- project structure: [project-structure-governance-starter-pack.md](./project-structure-governance-starter-pack.md), [project-file-taxonomy-template.md](./project-file-taxonomy-template.md), [project-boundary-register-template.md](./project-boundary-register-template.md), [project-workspace-and-artifact-policy-template.md](./project-workspace-and-artifact-policy-template.md)
- entry: [navigation-template.md](./navigation-template.md)
- adoption: [project-template-adoption-packet-template.md](./project-template-adoption-packet-template.md)
- design: [requirements-template.md](./requirements-template.md), [basic-design-template.md](./basic-design-template.md), [implementation-plan-template.md](./implementation-plan-template.md)
- judgment: [decision-packet-template.md](./decision-packet-template.md), [evaluation-verdict-template.md](./evaluation-verdict-template.md)
- task: [task-spec-template.md](./task-spec-template.md), [task-checklist-template.md](./task-checklist-template.md)

There are additional templates in this shelf, but the list above is enough for the first pass.

## Boundary

Do not use this shelf as the canonical home for a project's live status, operating log, or runtime facts.

## Open Later

- additional templates only when the first-pass list is not enough
- `../README.md` only if you need the shelf map
- do not read the whole template shelf in order

## Keep As-Is Versus Replace

- keep as-is: section structure, fill-in viewpoint, owner-judgment capture
- replace per project: paths, file names for the current view, validator or healthcheck names, command names, and project-specific shelf names

Move only portable structure into this shelf.
Keep each project's canonical content on that project's own shelf.
