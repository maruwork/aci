# ACI W3 B1 Detailed Implementation Spec

Status: Active
Parent task: `ACI-W3`
Active bundle: `ACI-W3-B1`

## Purpose

Define the execution boundary for the current repo-local CI-22 hardening wave
tightly enough that completion can be proven from bounded detector, fixture,
and documentation evidence rather than from general intent.

This document governs the active `ACI-W3-B1` implementation wave after `W1`
closure. It does not reopen the broader product boundary.

## Read Order

1. `docs/roadmap/ACI_COMPLETION_POLICY.md`
2. `docs/roadmap/ACI_REPO_LOCAL_EXECUTION_PLAN.md`
3. `docs/roadmap/ACI_REPO_LOCAL_CHECKPOINTS.md`
4. `docs/tasks/ACI_REPO_LOCAL_TASK_BREAKDOWN.md`
5. `docs/tasks/ACI_TASK_W3_CI22_BOUNDED_HARDENING.md`
6. `docs/tasks/ACI_W3_B1_IMPLEMENTATION_PLAN.md`
7. this file

## 1. Success Subject

The success subject for `ACI-W3-B1` is not "better CI-22 coverage" in general.

It is the narrower claim that the next repo-local wave should:

- target one local, explainable safe-management pattern at a time
- pair every recognition rule with a detector fixture
- keep the known-limit boundary explicit in docs and inventory
- stop before non-local ownership reasoning or lifecycle inference sprawl

If a candidate change cannot be described within those four points, it is
outside this bundle.

## 2. Non-Negotiable Semantics

- `CI-22` remains a bounded local reasoning detector
- local safe-management wins are allowed
- non-local helper ownership transfer claims are out of scope
- every detector rule change must carry a focused fixture and doc writeback
- inventory wording must continue to describe the remaining limitation honestly

## 3. Target Surface

Only these files are in the primary change window for this bundle:

| File | Status | Allowed Change |
|---|---|---|
| `shared/python/detectors/ci_22.py` | primary | local safe-management recognition only |
| `shared/tests/test_aci_detector_fixtures.py` | primary | focused CI-22 fixture coverage |
| `docs/CI_REFERENCE.md` | primary | CI-22 boundary wording |
| `docs/roadmap/ACI_AUDIT_TOOL_COMPLETION_INVENTORY_2026-06-18.md` | writeback-only | status/evidence wording when behavior meaning changes |

## 4. Non-Target Surface

These surfaces are read-only for `ACI-W3-B1` unless contradiction makes
progress impossible:

| File | Why non-target |
|---|---|
| `shared/python/aci_scan.py` | scan orchestration is not the bottleneck here |
| `shared/python/aci_report_view.py` | report semantics were already closed in W1-adjacent work |
| `docs/PRECISION_REVIEW_WORKFLOW.md` | precision workflow is not being changed by this bundle |
| `shared/tools/` | maintainer harnesses are not the subject of CI-22 hardening |

## 5. Required Change Pattern

Every `ACI-W3-B1` implementation must follow this order:

1. name one candidate local-safe-management pattern
2. confirm it is local, explainable, and fixture-testable
3. add the detector rule
4. add the focused fixture
5. update `docs/CI_REFERENCE.md`
6. update inventory wording only if the known-limit statement changed

## 6. Allowed Refactor Boundary

The implementation may:

- add small detector helpers inside `ci_22.py`
- extend existing fixture coverage
- sharpen CI-22 limitation wording

The implementation may not:

- introduce broad dataflow claims
- change CI-22 into a correctness-proof blocker
- widen work into unrelated detectors
- treat W4 writeback as the main active bundle

## 7. Completion Evidence

This detailed spec is satisfied only when:

- the active bundle remains `ACI-W3-B1`
- the implemented `CI-22` changes remain bounded to local same-function
  safe-management reasoning
- focused `CI-22` fixture verification passes for the bounded pattern wave
- the wider detector-fixture file still passes without `CI-22` regression
- `docs/CI_REFERENCE.md` and inventory wording describe the same bounded
  limitation honestly
