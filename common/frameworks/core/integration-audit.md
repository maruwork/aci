# Project Progression Rule Integration Audit

This table centers `progression-rule.md` and summarizes what role each framework, policy, and checklist plays.
Its purpose is to let a reader explain the existing placement before adding any new rule.

## 0. Read First

1. [progression-rule.md](progression-rule.md)
2. [integration-audit.md](integration-audit.md)
3. [goal-path-checkpoint-design.md](goal-path-checkpoint-design.md)
4. [../../policies/gates/execution-readiness.md](../../policies/gates/execution-readiness.md)

## 1. Verdict Classes

- `KEEP`
  - the role is clear and the file stays live
- `LATER`
  - keep it for now as reference or support

## 2. Framework Roles

| file | primary role | verdict | notes |
|---|---|---|---|
| `progression-rule.md` | top progression rule | `KEEP` | canonical authority for progression, stopping, and re-grounding |
| `goal-path-checkpoint-design.md` | five-layer breakdown | `KEEP` | skeleton for task design |
| `workflow-spine.md` | progression spine | `KEEP` | flow from design through execution |
| `../support/ps-suite-guide.md` | support toolkit guide | `LATER` | support only, not core |
| `../support/selection-guide.md` | framework selection support | `KEEP` | live support guide |
| `../support/prompt-improvement-cycle.md` | prompt-improvement support | `KEEP` | live support framework |
| `../review/decision-implementation-review.md` | consistency review | `KEEP` | live review lens |

## 3. Policy Roles

| file | primary role | verdict | notes |
|---|---|---|---|
| `../../policies/gates/execution-readiness.md` | pre-start check | `KEEP` | concretizes the conditions for proceeding |
| `../../policies/operations/agent-workflow.md` | day-to-day operating flow | `KEEP` | next action, continuation, delegation |
| `../../policies/operations/task-realtime.md` | `current` and task-state operation | `KEEP` | current-canonical operation |
| `../../policies/structure/entry-guide-reference.md` | entry / guide / reference split | `KEEP` | prevents route mixing |
| `../../policies/operations/verification-retry.md` | verify / retry | `KEEP` | how to proceed after failure |
| `../../policies/structure/file-operations.md` | file and shelf operations | `KEEP` | placement, move, archive |
| `../../policies/structure/naming-shelf.md` | naming and shelf responsibility | `KEEP` | naming and shelf semantics |
| `../../policies/gates/template-installation.md` | template-installation gate | `KEEP` | stop conditions before installation |
| `../../policies/gates/adoption-completion.md` | adoption completion | `KEEP` | completion condition for adoption |

## 4. Checklist Roles

- `implementation-audit-checklist.md`
  - post-implementation audit
- `design-spec-completion-checklist.md`
  - design-spec completion check
- `ai-agent-runtime-bootstrap-checklist.md`
  - AI runtime bootstrap
- `unit-test-checklist.md`
  - unit-test viewpoints
- `integration-test-checklist.md`
  - integration-test viewpoints
- `security-review-checklist.md`
  - security-review viewpoints

## 5. Conclusion

- replacement targets are limited; most files remain `KEEP`
- absorb project differences into template-side branch decisions before adding a new type
- move time-dependent deliberation records down into `../../reference/`
