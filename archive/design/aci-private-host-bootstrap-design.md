# ACI Private Host Bootstrap Design

Status: Complete

## Theme

`ACI private host bootstrap`

## Scope

- private repository bootstrap only
- carried files and private-repository setup order
- pre-public verification order
- explicit hold line before public release

## Start Conditions

- `ACI publishable hold` is complete with repository-side preparation remaining
- host target is fixed as `fumimaruwork/aci`
- initial visibility is fixed as `private`

## Shared Execution Rules

- readable locations:
  - `epo root`
  - `common/refernce`
- writable locations:
  - `epo root`
  - `common/refernce`
- must not touch:
  - live public visibility
  - public announcement surfaces
  - downstream project-local integrations

## ACI-PHB-T1 Private Boundary

1. Task ID
   - `ACI-PHB-T1`
2. Parent Theme
   - `ACI private host bootstrap`
3. Parent Checkpoint
   - `ACI-PHB-CP1 Private Boundary Fixed`
4. Purpose
   - separate private bootstrap from public-release actions
5. Why This Task Is Needed
   - the user explicitly does not want publication yet
6. Start Conditions
   - publication packet exists
7. Input
   - `docs/release/PUBLIC_GO_LIVE_SEQUENCE_DRAFT.md`
   - `docs/release/REPO_EXPORT_GUIDE.md`
   - `docs/governance/OWNER_DECISION_PACKET.md`
8. Readable Locations
   - `epo root`
9. Writable Locations
   - bootstrap records
10. Must Not Touch
   - live repository visibility
11. Actions
   - identify private-only actions
   - identify public-release actions to exclude
12. Expected Output
   - private boundary rule
13. Acceptance Criteria
   - another operator can tell where private preparation stops
14. Failure Conditions
   - public-release actions remain mixed into private bootstrap
15. Stop Conditions
   - private boundary depends on repository operations already performed
16. Send-Back Conditions
   - publication documents are missing required repository detail
17. Human Decision Gate
   - escalate only if visibility policy changes
18. Evidence
   - updated bootstrap docs
19. Record Destination
   - bootstrap records
20. Final Decider
   - `Codex B`

## ACI-PHB-T2 Private Carry Set

1. Task ID
   - `ACI-PHB-T2`
2. Parent Theme
   - `ACI private host bootstrap`
3. Parent Checkpoint
   - `ACI-PHB-CP2 Carry Set Fixed`
4. Purpose
   - define the carried file set for the private repository
5. Why This Task Is Needed
   - repository preparation fails if carried files are ambiguous
6. Start Conditions
   - `ACI-PHB-T1` boundary rule exists
7. Input
   - `docs/release/REPO_EXPORT_GUIDE.md`
   - `docs/release/REPO_EXPORT_CHECKLIST.md`
8. Readable Locations
   - `epo root`
9. Writable Locations
   - export/bootstrap docs
10. Must Not Touch
   - live remote repository contents
11. Actions
   - define carried files for the private repository
   - define internal-only files that stay behind
12. Expected Output
   - private carry set
13. Acceptance Criteria
   - another operator can prepare the private repository contents without guessing
14. Failure Conditions
   - carry set still conflicts with exclusions
15. Stop Conditions
   - carry set requires changing generic ACI shelf structure
16. Send-Back Conditions
   - a public-only file is still required by private bootstrap
17. Human Decision Gate
   - escalate only if private repository scope expands beyond the current packet
18. Evidence
   - updated export/bootstrap docs
19. Record Destination
   - bootstrap records
20. Final Decider
   - `Codex B`

## ACI-PHB-T3 Private Repository Setup

1. Task ID
   - `ACI-PHB-T3`
2. Parent Theme
   - `ACI private host bootstrap`
3. Parent Checkpoint
   - `ACI-PHB-CP3 Private Repository Setup Order Fixed`
4. Purpose
   - define the order of private repository creation and preparation
5. Why This Task Is Needed
   - repository preparation should be executable without rediscovery
6. Start Conditions
   - `ACI-PHB-T2` carry set exists
7. Input
   - `docs/release/PUBLIC_GO_LIVE_SEQUENCE_DRAFT.md`
   - `docs/governance/OWNER_DECISION_PACKET.md`
8. Readable Locations
   - `epo root`
9. Writable Locations
   - runbook/bootstrap docs
10. Must Not Touch
   - live public release actions
11. Actions
   - define repository creation order
   - define file placement and license placement order
   - define draft promotion order for the private repository copy
12. Expected Output
   - private repository setup order
13. Acceptance Criteria
   - another operator can create the private repository and prepare it in order
14. Failure Conditions
   - setup order still depends on hidden repository knowledge
15. Stop Conditions
   - setup order requires public release actions
16. Send-Back Conditions
   - required repository step is missing from the packet
17. Human Decision Gate
   - escalate only if repository target changes
18. Evidence
   - updated runbook/bootstrap docs
19. Record Destination
   - bootstrap records
20. Final Decider
   - `Codex B`

## ACI-PHB-T4 Private Verification

1. Task ID
   - `ACI-PHB-T4`
2. Parent Theme
   - `ACI private host bootstrap`
3. Parent Checkpoint
   - `ACI-PHB-CP4 Private Verification Fixed`
4. Purpose
   - define the verification sequence before any public action
5. Why This Task Is Needed
   - the private repository still needs a reproducible acceptance path
6. Start Conditions
   - `ACI-PHB-T3` setup order exists
7. Input
   - `docs/release/PUBLIC_RELEASE_CHECKLIST.md`
   - `runtime/aci-generic-quickstart.md`
8. Readable Locations
   - `epo root`
9. Writable Locations
   - verification/bootstrap docs
10. Must Not Touch
   - live CI systems
11. Actions
   - define the private verification order
   - define the pass condition before any public action
12. Expected Output
   - private verification order
13. Acceptance Criteria
   - another operator can verify the private repository candidate without guessing
14. Failure Conditions
   - verification still depends on monorepo-only assumptions
15. Stop Conditions
   - verification requires public repository state
16. Send-Back Conditions
   - repository setup order and verification order disagree
17. Human Decision Gate
   - escalate only if private verification scope changes the chosen CI posture
18. Evidence
   - updated verification/bootstrap docs
19. Record Destination
   - bootstrap records
20. Final Decider
   - `Codex B`

## ACI-PHB-T5 Hold Line

1. Task ID
   - `ACI-PHB-T5`
2. Parent Theme
   - `ACI private host bootstrap`
3. Parent Checkpoint
   - `ACI-PHB-CP5 Hold Point Fixed`
4. Purpose
   - define the explicit stop line before public release
5. Why This Task Is Needed
   - private preparation must not accidentally roll into publication
6. Start Conditions
   - `ACI-PHB-T4` verification order exists
7. Input
   - all bootstrap outputs
8. Readable Locations
   - `epo root`
   - bootstrap records
9. Writable Locations
   - hold/bootstrap docs
10. Must Not Touch
   - public visibility
11. Actions
   - state the last allowed private step
   - state the first forbidden public step
12. Expected Output
   - explicit hold line
13. Acceptance Criteria
   - another operator can stop cleanly before publication
14. Failure Conditions
   - hold line still allows ambiguous public action
15. Stop Conditions
   - hold line requires actual repository creation to define
16. Send-Back Conditions
   - earlier bootstrap tasks are incomplete
17. Human Decision Gate
   - escalate only if the user changes the no-public rule
18. Evidence
   - updated hold/bootstrap docs
19. Record Destination
   - bootstrap records
20. Final Decider
   - `Codex B`

## Latest Result

- complete
- the design is sufficient for another operator to prepare `fumimaruwork/aci` in a private state and stop before public release
