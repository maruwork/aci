# ACI Domain Pack Boundary Design

Status: Complete

## DPB-T1

- Purpose:
  - enumerate every file that shapes the current domain-pack reading route
- Start Conditions:
  - current public-facing waves are closed
- Inputs:
  - `domains/`
  - `ACI_SHELF_CLASSIFICATION.md`
  - `README.md`
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- No-Touch:
  - downstream project shelves
- Action:
  - inventory domain-pack surfaces and route references
- Output:
  - stable rewrite target list
- Acceptance:
  - every domain-pack facing route is explicit
- Failure Conditions:
  - a referenced domain surface is missed
- Stop Conditions:
  - inventory reveals an authority conflict requiring owner decision
- Evidence:
  - updated task progress
- Record Destination:
  - task board and summary
- Final Decider:
  - Codex B

## DPB-T2

- Purpose:
  - document what belongs in common, domain, and bridge surfaces
- Start Conditions:
  - inventory complete
- Inputs:
  - inventory results
- Read:
  - ``
- Write:
  - ``
- No-Touch:
  - signal/report contracts unless needed for boundary wording only
- Action:
  - write the boundary rule in the most relevant existing surfaces
- Output:
  - updated boundary wording
- Acceptance:
  - common, domain, and bridge responsibilities are separable by reading docs alone
- Failure Conditions:
  - wording still leaves ambiguous ownership
- Stop Conditions:
  - boundary clarification requires changing current contracts
- Evidence:
  - updated docs
- Record Destination:
  - task board and summary
- Final Decider:
  - Codex B

## DPB-T3

- Purpose:
  - make `domains/` readable as an entry surface
- Start Conditions:
  - boundary rule defined
- Inputs:
  - `domains/` inventory
- Read:
  - `domains/`
- Write:
  - `domains/`
- No-Touch:
  - domain rule python unless entry wording requires no code change
- Action:
  - add or refine `domains/` entry doc
- Output:
  - readable `domains/` route
- Acceptance:
  - a first-time reader can tell what optional domain packs are and how to read them
- Failure Conditions:
  - route still depends on scattered README hunting
- Stop Conditions:
  - domain entry needs a larger structural move
- Evidence:
  - updated entry docs
- Record Destination:
  - task board and summary
- Final Decider:
  - Codex B

## DPB-T4

- Purpose:
  - align the `Pier` bridge route with the boundary rule
- Start Conditions:
  - domain entry route exists
- Inputs:
  - `domains/pier/`
  - `persistence/aci-pier-validation-decision-register.md`
- Read:
  - `domains/pier/`
  - `persistence/`
- Write:
  - same shelves
- No-Touch:
  - downstream `pier` project shelves
- Action:
  - clarify how `Pier` bridge docs should be read from the common side
- Output:
  - aligned bridge route
- Acceptance:
  - `Pier` bridge docs no longer feel mixed into common generic guidance
- Failure Conditions:
  - bridge and common route still compete
- Stop Conditions:
  - route conflict requires moving files across shelves
- Evidence:
  - updated bridge docs
- Record Destination:
  - task board and summary
- Final Decider:
  - Codex B

## DPB-T5

- Purpose:
  - verify the domain-pack boundary end to end
- Start Conditions:
  - doc updates complete
- Inputs:
  - revised README, domain docs, bridge docs
- Read:
  - ``
- Write:
  - `common/refernce/`
- No-Touch:
  - downstream projects
- Action:
  - perform manual review and close the wave
- Output:
  - completion judgment
- Acceptance:
  - no domain-pack route ambiguity remains in reviewed surfaces
- Failure Conditions:
  - reviewed docs still blur common and domain boundaries
- Stop Conditions:
  - a newly found issue requires a larger wave
- Evidence:
  - summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B
