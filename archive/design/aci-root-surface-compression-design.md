# ACI Root Surface Compression Design

Status: Complete

## RSC-T1

- Purpose:
  - classify every root document into the smallest useful reading group
- Start Conditions:
  - current public surface polish is complete
- Inputs:
  - root file inventory
  - current README
- Read:
  - ``
- Write:
  - ``
  - `common/refernce/`
- No-Touch:
  - downstream project shelves
- Action:
  - group root docs into user / maintainer / release-prep
- Output:
  - stable grouping map
- Acceptance:
  - every long-list root doc in README has a group
- Failure Conditions:
  - grouping leaves ambiguous files without owner meaning
- Stop Conditions:
  - grouping requires changing document authority
- Evidence:
  - updated task progress
- Record Destination:
  - task board and summary
- Final Decider:
  - Codex B

## RSC-T2

- Purpose:
  - create one index for maintainer history docs
- Start Conditions:
  - grouping map complete
- Inputs:
  - roadmap / tasks / design reading routes
- Read:
  - `roadmap/`
  - `tasks/`
  - `design/`
- Write:
  - ``
- No-Touch:
  - existing history docs content
- Action:
  - create a single maintainer-history index file
- Output:
  - new index
- Acceptance:
  - README can link to one file instead of many history routes
- Failure Conditions:
  - index duplicates conflicting route definitions
- Stop Conditions:
  - index requires rewriting history docs
- Evidence:
  - created index
- Record Destination:
  - task board and summary
- Final Decider:
  - Codex B

## RSC-T3

- Purpose:
  - create one index for release-prep docs
- Start Conditions:
  - grouping map complete
- Inputs:
  - release-prep root docs
- Read:
  - ``
- Write:
  - ``
- No-Touch:
  - underlying release-prep docs content
- Action:
  - create a single release-prep index file
- Output:
  - new index
- Acceptance:
  - README can link to one file instead of many release-prep docs
- Failure Conditions:
  - release-prep index hides required user docs
- Stop Conditions:
  - some release-prep doc is actually user-facing
- Evidence:
  - created index
- Record Destination:
  - task board and summary
- Final Decider:
  - Codex B

## RSC-T4

- Purpose:
  - compress README and keep user route short
- Start Conditions:
  - both indexes exist
- Inputs:
  - README
  - index files
- Read:
  - `README.md`
- Write:
  - `README.md`
- No-Touch:
  - core/runtime/report contracts
- Action:
  - replace long flat lists with grouped index links
- Output:
  - compressed README
- Acceptance:
  - root route is shorter and easier to scan
- Failure Conditions:
  - README loses required public guidance
- Stop Conditions:
  - grouped links create ambiguity
- Evidence:
  - updated README
- Record Destination:
  - task board and summary
- Final Decider:
  - Codex B

## RSC-T5

- Purpose:
  - verify compressed root route
- Start Conditions:
  - README and indexes updated
- Inputs:
  - revised root docs
- Read:
  - ``
- Write:
  - `common/refernce/`
- No-Touch:
  - downstream projects
- Action:
  - manual read review of root route
- Output:
  - completion judgment
- Acceptance:
  - user route stays short and self-contained
- Failure Conditions:
  - root still overwhelms first-time readers
- Stop Conditions:
  - newly found issue requires a different wave
- Evidence:
  - summary
- Record Destination:
  - summary
- Final Decider:
  - Codex B
