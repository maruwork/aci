# ACI Compatibility Surface Design

Status: Complete

## CSC-T1

- Purpose:
  - identify legacy compatibility files and their canonical replacements
- Start Conditions:
  - current `ACI` shelf is readable
- Inputs:
  - `templates/`
  - `runtime/`
  - `report/`
  - `persistence/`
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Action:
  - map legacy files to canonical shelves
- Acceptance:
  - each legacy file has a canonical route
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## CSC-T2

- Purpose:
  - create a readable `templates/` entry
- Start Conditions:
  - inventory complete
- Inputs:
  - inventory map
- Read:
  - `templates/`
- Write:
  - `templates/`
- Action:
  - add one entry file explaining scope and canonical route
- Acceptance:
  - first-time reader can tell the shelf is compatibility-only
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## CSC-T3

- Purpose:
  - link canonical shelves from the compatibility entry
- Start Conditions:
  - `templates/README.md` exists
- Inputs:
  - canonical runtime/report/persistence docs
- Read:
  - `runtime/`
  - `report/`
  - `persistence/`
- Write:
  - `templates/`
  - `README.md` if needed
- Action:
  - add direct canonical route references
- Acceptance:
  - canonical route is obvious
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## CSC-T4

- Purpose:
  - verify compatibility surface clarity
- Start Conditions:
  - docs updated
- Inputs:
  - revised compatibility docs
- Read:
  - ``
- Write:
  - `common/refernce/`
- Action:
  - manual review
- Acceptance:
  - legacy shelf no longer feels primary
- Record Destination:
  - summary
- Final Decider:
  - Codex B
