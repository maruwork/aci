# ACI Market-Grade Readiness Design

Status: Complete

## MGR-T1

- Purpose:
  - make the current `ACI` product surface explicit before judging it against market tools
- Start Conditions:
  - report triage readiness is complete
- Inputs:
  - `README.md`
  - `USER_EVALUATION_INDEX.md`
  - `runtime/aci-generic-quickstart.md`
  - `report/`
  - `core/`
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - inventory how `ACI` currently supports first-time use, repeated use, report handling, and release preparation
- Output:
  - explicit current-surface inventory
- Acceptance:
  - the inventory is specific enough to show what exists and what does not
- Failure Conditions:
  - inventory blends current facts with planned futures
- Stop Conditions:
  - discovered gaps belong outside the tool body
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## MGR-T2

- Purpose:
  - define what market-grade evaluation means for this tool
- Start Conditions:
  - current-surface inventory complete
- Inputs:
  - current-surface inventory
  - existing public/release docs
- Read:
  - ``
  - `common/refernce/aci-evolution-log-20260605.md`
- Write:
  - `common/refernce/`
  - ``
- Do:
  - define stable evaluation axes such as install/setup, operation, triage/state, CI, and trust
- Output:
  - explicit market-grade evaluation axes
- Acceptance:
  - axes are concrete enough to classify missing work
- Failure Conditions:
  - axes collapse into vague quality language
- Stop Conditions:
  - an axis is not actionable within `ACI`
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## MGR-T3

- Purpose:
  - turn high-level dissatisfaction into bounded product lanes
- Start Conditions:
  - evaluation axes fixed
- Inputs:
  - current-surface inventory
  - evaluation axes
- Read:
  - ``
- Write:
  - `common/refernce/`
- Do:
  - classify the missing capabilities under stable product lanes
- Output:
  - gap-by-lane classification
- Acceptance:
  - each gap sits in one product lane and is not duplicated across lanes
- Failure Conditions:
  - closed shelf work is reintroduced as a fake product gap
- Stop Conditions:
  - a lane grows too broad to execute
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## MGR-T4

- Purpose:
  - decompose each lane into implementation-scale themes
- Start Conditions:
  - gap classification complete
- Inputs:
  - gap-by-lane classification
- Read:
  - ``
- Write:
  - `common/refernce/`
  - ``
- Do:
  - split the lanes into concrete themes such as CLI/config, baseline/suppression, CI contract, fixture suite, and state model
- Output:
  - implementation-theme breakdown
- Acceptance:
  - each theme is small enough to become its own next wave
- Failure Conditions:
  - one theme still contains multiple unrelated product concerns
- Stop Conditions:
  - a theme needs owner/business decisions first
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## MGR-T5

- Purpose:
  - turn the implementation themes into an explicit next-wave map
- Start Conditions:
  - implementation-theme breakdown complete
- Inputs:
  - implementation-theme breakdown
- Read:
  - `common/refernce/`
  - `roadmap/`
- Write:
  - `common/refernce/`
  - `roadmap/`
- Do:
  - define the next waves that will move `ACI` toward market-grade quality
- Output:
  - next-wave map
- Acceptance:
  - another maintainer can see the execution order without reconstructing strategy
- Failure Conditions:
  - next-wave map depends on implicit priorities
- Stop Conditions:
  - 5-layer drift appears before closure
- Record Destination:
  - summary
- Final Decider:
  - Codex B

## MGR-T6

- Purpose:
  - verify that the remaining product road is explicit and executable
- Start Conditions:
  - next-wave map complete
- Inputs:
  - current-surface inventory
  - gap classification
  - next-wave map
- Read:
  - `common/refernce/`
  - ``
- Write:
  - `common/refernce/`
- Do:
  - run manual review and close
- Output:
  - closure summary
- Acceptance:
  - no major market-grade gap remains unnamed in the reviewed scope
- Failure Conditions:
  - product-grade expectations are still hidden behind general wording
- Stop Conditions:
  - another prerequisite wave is discovered and not recorded
- Record Destination:
  - summary
- Final Decider:
  - Codex B
