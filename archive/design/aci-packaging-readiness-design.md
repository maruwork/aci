# ACI Packaging Readiness Design

Status: Complete

## APK-T1

- Purpose:
  - identify why current repo-local execution is not yet the same as packaged execution
- Start Conditions:
  - analyzer execution readiness is complete
- Inputs:
  - `python/aci_cli.py`
  - `python/aci_domain_loader.py`
  - `README.md`
  - `docs/release/REPO_EXPORT_GUIDE.md`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - inventory current entrypoint, file-path, and asset-layout assumptions
- Output:
  - explicit packaging-blocker inventory
- Acceptance:
  - inventory separates current facts from later migration ideas
- Failure Conditions:
  - inventory assumes a package layout that does not exist
- Stop Conditions:
  - packaging meaning depends on unstated filesystem magic
- Evidence:
  - blocker summary with cited source files
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## APK-T2

- Purpose:
  - define the smallest useful packaging model
- Start Conditions:
  - inventory complete
- Inputs:
  - packaging-blocker inventory
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define package entrypoint, layout, and bundled-asset expectations at a bounded contract level
- Output:
  - explicit packaging model
- Acceptance:
  - model is generic and does not overclaim current installability
- Failure Conditions:
  - model starts deciding a full tree migration before review
- Stop Conditions:
  - model requires destructive layout edits in this wave
- Evidence:
  - bounded packaging contract
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## APK-T3

- Purpose:
  - document packaging rules
- Start Conditions:
  - model fixed
- Inputs:
  - packaging model
- Read:
  - ``
- Write:
  - ``
- Do:
  - add packaging guidance and explicit blockers
- Output:
  - packaging rule documents
- Acceptance:
  - another maintainer can tell what must change before safe packaging work starts
- Failure Conditions:
  - docs imply packaging already works when it does not
- Stop Conditions:
  - docs require a tree rewrite in this wave
- Evidence:
  - rule docs and route updates
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## APK-T4

- Purpose:
  - make packaging boundaries readable
- Start Conditions:
  - documentation exists
- Inputs:
  - packaging rule docs
- Read:
  - ``
- Write:
  - ``
- Do:
  - connect packaging guidance to README and release-prep route
- Output:
  - updated reader route
- Acceptance:
  - packaging preparation is readable without oral explanation
- Failure Conditions:
  - reader route blurs repo-local and packaged execution
- Stop Conditions:
  - route requires unresolved migration decisions
- Evidence:
  - updated route docs
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## APK-T5

- Purpose:
  - verify the reviewed packaging readiness surface
- Start Conditions:
  - routes updated
- Inputs:
  - revised packaging readiness surface
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - run manual review and compile-safe checks
- Output:
  - closure summary
- Acceptance:
  - no reviewed inconsistency remains in the packaging readiness surface
- Failure Conditions:
  - packaging readiness still depends on oral explanation
- Stop Conditions:
  - 5-layer drift appears before closure
- Evidence:
  - review notes and compile-safe proof
- Record Destination:
  - summary
- Final Decider:
  - Codex B
