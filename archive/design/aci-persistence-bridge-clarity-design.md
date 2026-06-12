# ACI Persistence Bridge Clarity Design

Status: Complete

## PBC-T1

- Purpose:
  - identify how persistence is currently introduced and where bridge material is referenced
- Start Conditions:
  - compatibility surface is complete
- Inputs:
  - `README.md`
  - `persistence/README.md`
  - `ACI_SHELF_CLASSIFICATION.md`
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Action:
  - inventory persistence route references
- Acceptance:
  - all persistence-facing routes are explicit
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## PBC-T2

- Purpose:
  - make generic persistence authority the obvious first read
- Start Conditions:
  - inventory complete
- Inputs:
  - persistence route inventory
- Read:
  - `persistence/`
- Write:
  - `persistence/`
- Action:
  - refine reading rule and shelf description
- Acceptance:
  - generic persistence authority is unmistakable
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## PBC-T3

- Purpose:
  - make bridge material readable without competing with generic authority
- Start Conditions:
  - persistence reading rule refined
- Inputs:
  - `aci-pier-validation-decision-register.md`
- Read:
  - `persistence/`
- Write:
  - `persistence/`
- Action:
  - add one small bridge index or route section if needed
- Acceptance:
  - `Pier` bridge is easy to find but clearly secondary
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## PBC-T4

- Purpose:
  - verify the persistence bridge boundary
- Start Conditions:
  - doc updates complete
- Inputs:
  - revised persistence docs
- Read:
  - ``
- Write:
  - `common/refernce/`
- Action:
  - manual review
- Acceptance:
  - no reviewed persistence surface blurs generic and bridge roles
- Record Destination:
  - summary
- Final Decider:
  - Codex B
