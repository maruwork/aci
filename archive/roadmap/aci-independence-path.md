# ACI Independence Path

Status: Complete

## Path

1. inventory the current `epo root` shelf and classify mixed concerns
2. define the target `core + domain + runtime/report/persistence/integration` structure
3. define explicit dependency and ownership boundaries
4. define the domain-pack model using `Pier` as the first extracted option
5. establish ACI's own five-layer documents inside `epo root`
6. refactor shelf structure and authority files to match the design
7. verify the refactor without reintroducing Pier-only dependency into core

## Planned Stop Points

- before destructive rename or large move
- before non-compatible import path change
- before changing meaning of current authority files without a compatibility note

## Dependencies

- inventory before architecture
- architecture before task-level refactor
- boundary rules before file moves
- domain-pack rules before Pier extraction
- five-layer docs before declaring the workstream closed
