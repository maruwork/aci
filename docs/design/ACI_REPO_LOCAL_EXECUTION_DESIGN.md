# ACI Repo-Local Execution Design

Status: Active

## Purpose

Describe the design that governs repo-local completion work after the
Python-first product boundary has already been fixed.

This document turns the repo-local execution plan into a design body that can
hand consistent assumptions down to later task work without reopening the
completion claim every turn.

## Design Rule

`ACI` repo-local execution should close the bounded Python-first completion
surface by evidence, not by breadth.

The design below therefore optimizes for:

- claim honesty before capability expansion
- evidence-backed precision before detector proliferation
- operator-facing clarity before UI breadth
- packaging/runtime proof before public-completion language
- strict separation between repo-local code quality and owner-gated release
  posture

## 1. Architecture

### System Boundary

This design covers only repo-local execution inside `C:\Users\f_tan\project\aci`.

It does not cover:

- GitHub hosted security enablement
- repository visibility changes
- public-history cleanup decisions
- owner-side release posture decisions

### Major Components

The repo-local execution surface is composed of:

- policy surfaces
  - `docs/roadmap/ACI_COMPLETION_POLICY.md`
  - `shared/core/aci-product-boundary-and-coverage-policy.md`
- planning surfaces
  - `docs/roadmap/ACI_AUDIT_TOOL_COMPLETION_INVENTORY_2026-06-18.md`
  - `docs/roadmap/ACI_REPO_LOCAL_EXECUTION_PLAN.md`
- design surface
  - this document
- implementation surfaces
  - `shared/python/`
  - `shared/core/`
  - `shared/report/`
  - `shared/tests/`
  - `examples/`
- owner-gated evidence surfaces
  - `workspace/owner-gated-release/`

### Runtime Flow

```text
completion policy
  -> inventory interpretation
  -> repo-local execution plan
  -> repo-local design
  -> bounded implementation change
  -> focused verification
  -> inventory/worklist writeback
```

### Option Comparison

| Option | Pros | Cons | Fit |
|---|---|---|---|
| Close claim-critical and should-add in one blended stream | fewer planning documents | reopens scope drift and overclaim risk | low |
| Keep repo-local execution claim-first and evidence-first | preserves Python-first boundary and small-step verification | requires more writeback discipline | high |

### Recommended Direction

- recommendation:
  - keep repo-local execution claim-first and evidence-first
- reason for adoption:
  - it matches the fixed completion policy and prevents language-general or
    owner-gated drift
- rejected alternatives:
  - blended "just improve whatever is next" execution because it obscures what
    is required for the bounded completion claim

## 2. Technology Choices

| Layer | Choice | Reason | Constraints |
|---|---|---|---|
| Product boundary | Python-first native + polyglot text/external evidence | aligns implementation with honest claim | must not drift into language-general native wording |
| Planning | roadmap docs under `docs/roadmap/` | stable repo-local execution surfaces | scratch/stateful evidence stays out of canonical shelves |
| Design | `docs/design/` | project taxonomy declares design shelf here | do not collapse design into task-only notes |
| Runtime implementation | `shared/python/`, `shared/core/`, `shared/report/` | caller-sensitive product surfaces | no archive/workspace spillover |
| Verification | focused pytest + contract/golden tests + packaging checks | evidence must be command- and file-provable | verification must remain bounded and reproducible |
| Owner-gated evidence | `workspace/owner-gated-release/` | external state is real but non-canonical | must not be promoted into product completion by wording alone |

## 3. Data Design

| Entity | Purpose | Key Fields | Constraints |
|---|---|---|---|
| completion claim | defines what may be called complete | boundary, exclusions, evidence rule | must remain Python-first |
| inventory item | records open/resolved work | id, status, rationale, evidence basis | open/resolved labels must not contradict implementation state |
| workstream | groups repo-local execution | objective, order, done rule, proof | should map to bounded repo-local units |
| evidence surface | proves a change | file, command, test, artifact, live-state note | must be nameable before calling done |
| owner-gated residual | records external blockers | blocker id, external state, owner action | must not be hidden inside repo-local completion language |

## 4. Interface Design

| Interface | Input | Output | Error Behavior |
|---|---|---|---|
| completion policy -> inventory | bounded completion rules | interpretation rule for open/resolved items | stop if a "should-add" item is being treated as claim-critical without justification |
| inventory -> execution plan | current open/resolved register | ordered repo-local workstreams | stop if owner-gated work is mixed into repo-local execution |
| execution plan -> design | workstream objectives and done rules | coherent execution design | stop if task detail starts replacing design boundary decisions |
| design -> implementation | bounded change request | code/doc/test update | stop if the change widens the product claim |
| implementation -> verification | changed surfaces | focused evidence | fail if no command/file/test can prove the change |
| verification -> writeback | evidence result | inventory/worklist status update | stop if evidence is ambiguous or stale |

### Related Decisions

| Decision | Status | Note |
|---|---|---|
| Python-first boundary | accepted | fixed in product-boundary docs |
| human-judgment-only CI-08/11/24 | accepted | not an omission claim |
| opt-in security analyzers stay catalog-visible | accepted | not execution-ready baseline claims |
| owner-gated/public-release separation | accepted | tracked outside repo-local completion |

## 5. Path And Checkpoint Design

### Path

Repo-local execution should proceed in this order:

1. confirm the bounded completion claim
2. select one repo-local workstream
3. make one bounded implementation or policy change
4. run focused verification
5. write back status/evidence

### Checkpoints

| Checkpoint | Prevents | Before Passing | After Passing |
|---|---|---|---|
| CP1 claim alignment | accidental scope drift | boundary and out-of-scope areas are explicit | the subject of completion is fixed |
| CP2 bounded change selection | local thrash and overreach | one workstream and one bounded unit are chosen | execution scope is small and provable |
| CP3 evidence-backed implementation | false-complete changes | code/doc/test changes and verification surface are explicit | implementation can be judged by evidence |
| CP4 writeback alignment | stale inventory/worklist state | evidence exists and status impact is known | docs and implementation remain synchronized |

## 6. Execution Surface Design

### Allowed Read Surfaces

- `README.md`
- `docs/roadmap/`
- `docs/design/`
- `docs/CI_REFERENCE.md`
- `shared/core/`
- `shared/python/`
- `shared/report/`
- `shared/tests/`
- `examples/`
- `workspace/owner-gated-release/` for owner-gated state only

### Allowed Write Surfaces

- `docs/roadmap/`
- `docs/design/`
- `docs/`
- `shared/core/`
- `shared/python/`
- `shared/report/`
- `shared/tests/`
- `examples/`

### Must-Not-Touch Surfaces

- `archive/`
- `.pytest_cache/`
- `build/`
- `aci.egg-info/`

## 7. Verification Design

### Required Evidence Types

- focused tests for runtime changes
- contract/golden tests for operator-facing output changes
- packaging/install checks for distribution-surface changes
- explicit document writeback for boundary/plan/status changes

### Verification Rule

Each repo-local unit must define its proof shape before execution:

- command
- test
- file state
- artifact
- or documented external-state note

### Fail-Close Rule

Do not mark a repo-local unit complete when:

- evidence is missing
- inventory status is stale
- the implementation widens the public claim without a boundary decision
- owner-gated residual is being silently absorbed into repo-local success

## 8. Security And Operations

- Authentication / authorization:
  - none added by this design; owner-gated hosted controls remain external
- Secret handling:
  - no new secret-bearing flow is introduced here
- Logging and monitoring:
  - operator-facing outputs must stay explicit about advisory-only vs gated
    findings
- Backup / recovery:
  - canonical writeback remains in versioned docs/code; scratch evidence stays
    in `workspace/`
- Performance target:
  - keep work units small enough for focused verification rather than full
    all-tree revalidation on every turn

## 9. Stop And Failure Conditions

### Stop Conditions

Stop and realign if work would:

- weaken the Python-first boundary
- change owner-gated/public-release meaning
- promote a low-confidence/advisory signal into a hard blocker without evidence
- create a new completion claim without naming the proof surface
- promote temporary `workspace/` material into canonical authority without a
  placement decision

### Failure Conditions

This design is failing if:

- the inventory and implementation drift apart again
- repo-local work starts expanding into language-general native ambition
- operator-facing outputs lose the gated/advisory distinction
- evidence claims rely on prose where tests or artifacts should exist

## 10. Open Issues

Any open issue without an owner or due date is a stop gate.

| Question | Owner | Due |
|---|---|---|
| whether to add a separate recall-label workflow beyond current precision review | repo-local maintainer lane | before making any broader public recall claim |
| whether replay/challenge-pack growth beyond current coverage is still high-value | repo-local maintainer lane | when item `10` is next in scope |
| how far CI-22 should continue expanding before the remaining non-local limit becomes the stable stop line | repo-local maintainer lane | when item `13` is reconsidered |
