# Shared Templates

This shelf stores reusable document starters for use across projects.

Read [PJ Template README](../README.md) first, then the purpose section of the exact template you need.

Keep prose in clear shared English.
Exact English should remain where tooling depends on it, such as `Status`, `ID`, `PASS / FAIL`, schema keys, or field names tied to external tools.

Label tokens clearly so a reader can tell whether something is prose, a fixed value, or a code name:

- plain descriptive terms stay plain prose
- fixed values such as `ACTIVE`, `DONE`, `PASS`, or `FAIL` should be described as status or verdict values
- code-level names such as `field_name` or `variable_name` should stay in backticks and be identified by type
- command names, options, and policy names should also be labeled by type

## Open These Templates First

- project structure: [project-structure-governance-starter-pack.md](./project-structure-governance-starter-pack.md), [project-file-taxonomy-template.md](./project-file-taxonomy-template.md), [project-boundary-register-template.md](./project-boundary-register-template.md), [project-workspace-and-artifact-policy-template.md](./project-workspace-and-artifact-policy-template.md)
- entry: [navigation-template.md](./navigation-template.md)
- adoption: [project-template-adoption-packet-template.md](./project-template-adoption-packet-template.md)
- design: [requirements-template.md](./requirements-template.md), [basic-design-template.md](./basic-design-template.md), [implementation-plan-template.md](./implementation-plan-template.md)
- judgment: [decision-packet-template.md](./decision-packet-template.md), [evaluation-verdict-template.md](./evaluation-verdict-template.md)
- task: [task-spec-template.md](./task-spec-template.md), [task-checklist-template.md](./task-checklist-template.md)

There are additional templates in this shelf, but the list above is enough for the first pass.

## Detailed Templates

- do not overload the entry README with merged or retired sub-items; check history and audit notes only when needed
- these are reusable starters that can be carried into other projects
- when extracting from a project-specific source document, move only the portable part into the shared template and keep the source project's canonical version in its original shelf

## First-Use Entry Order

Follow `../README.md` first.
Then choose only the one template that directly matches the current need.

1. if you are entering through project structure work:
   - [project-structure-governance-starter-pack.md](./project-structure-governance-starter-pack.md)
2. if you are writing a project entry or guide surface:
   - [navigation-template.md](./navigation-template.md)
3. if you need task, design, or judgment document starters:
   - open only the exact template you need

You do not need to read the whole template shelf in order.
If unsure, return to `../README.md`.

## Keep As-Is Versus Replace

- keep as-is: section structure, fill-in viewpoint, owner-judgment capture
- replace per project: paths, file names for the current view, validator or healthcheck names, command names, and project-specific shelf names
