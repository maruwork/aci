# ACI Package Layout Migration Design

Status: Complete

## APM-T1

- Purpose:
  - identify the minimum layout changes required for package-safe imports and assets
- Start Conditions:
  - packaging readiness is complete
- Inputs:
  - `docs/release/PACKAGING_BLOCKERS.md`
  - `docs/release/PACKAGE_LAYOUT_TARGET.md`
  - `python/aci_cli.py`
  - `python/aci_domain_loader.py`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - inventory the concrete blockers between current repo-local execution and package-safe loading
- Output:
  - explicit migration inventory
- Acceptance:
  - inventory separates current facts from later optional refinements
- Failure Conditions:
  - inventory assumes a package layout that still does not exist
- Stop Conditions:
  - migration meaning depends on unstated filesystem behavior
- Evidence:
  - blocker summary with cited source files
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## APM-T2

- Purpose:
  - define the smallest useful migration model
- Start Conditions:
  - inventory complete
- Inputs:
  - migration inventory
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- Do:
  - define package metadata, import path, and asset-loading expectations at a bounded level
- Output:
  - explicit migration model
- Acceptance:
  - model is bounded and does not overclaim full packaging completion
- Failure Conditions:
  - model starts deciding optional future structure work before review
- Stop Conditions:
  - model requires destructive tree edits outside the current shelf
- Evidence:
  - bounded migration contract
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## APM-T3

- Purpose:
  - implement package metadata and loading changes
- Start Conditions:
  - migration model fixed
- Inputs:
  - migration model
- Read:
  - ``
- Write:
  - ``
- Do:
  - add package metadata and package-safe loading changes without breaking current reviewed routes
- Output:
  - migrated package-safe surface
- Acceptance:
  - reviewed CLI/report/sample routes still work and package-safe rules are explicit
- Failure Conditions:
  - implementation breaks current reviewed commands or docs
- Stop Conditions:
  - implementation would require provider-specific install behavior
- Evidence:
  - package metadata, code changes, and verification output
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## APM-T4

- Purpose:
  - update routes and packaging docs
- Start Conditions:
  - implementation exists
- Inputs:
  - migrated surface
- Read:
  - ``
- Write:
  - ``
- Do:
  - update README, export, and packaging guidance to reflect the migrated surface
- Output:
  - updated reader routes
- Acceptance:
  - maintainers can understand the migrated surface without oral explanation
- Failure Conditions:
  - routes blur repo-local and package-safe execution
- Stop Conditions:
  - route depends on unresolved future migration work
- Evidence:
  - updated route docs
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## APM-T5

- Purpose:
  - verify the reviewed migrated surface
- Start Conditions:
  - docs updated
- Inputs:
  - revised migrated surface
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - run compile-safe checks, CLI checks, and manual review
- Output:
  - closure summary
- Acceptance:
  - no reviewed inconsistency remains in the migrated surface
- Failure Conditions:
  - migrated surface still depends on oral explanation
- Stop Conditions:
  - 5-layer drift appears before closure
- Evidence:
  - verification output and review notes
- Record Destination:
  - summary
- Final Decider:
  - Codex B
