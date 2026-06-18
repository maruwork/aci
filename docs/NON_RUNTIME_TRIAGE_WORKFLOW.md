# ACI Non-Runtime Triage Workflow

Status: Active

## Purpose

Make `full-repo` findings operationally useful without treating every
fixture/docs/support hit as a release blocker.

## Core Rule

In `full-repo`, blocker and gate decisions stay limited to `runtime-source`.
Everything else is advisory until a maintainer explicitly promotes it into
runtime work.

## First Split

Start from filtered views:

```bash
aci emit-github-summary --report workspace/full-repo-report.json --report-scope-class tests
aci emit-github-summary --report workspace/full-repo-report.json --report-scope-class fixtures
aci emit-github-summary --report workspace/full-repo-report.json --report-scope-class docs-evidence --report-scope-class roadmap-evidence
aci emit-github-summary --report workspace/full-repo-report.json --report-scope-class maintainer-probes --report-scope-class support
```

## Triage By Scope Class

- `tests`
  - fix when the test code itself is rotting or masking behavior
  - promote to runtime work only when the finding demonstrates a live product defect
- `fixtures`
  - keep visible when they are realistic replay evidence
  - baseline or suppress narrowly when duplication/noise is intentional and non-runtime
- `docs-evidence` and `roadmap-evidence`
  - treat as advisory wording/evidence work unless the finding points to live code or live config drift
- `maintainer-probes`
  - preserve them as evidence shelves, but do not let them impersonate runtime blockers
- `support`
  - fix if the support shelf is actively confusing operators; otherwise route as maintainer cleanup

## Allowed Outcomes

- fix now
- baseline as accepted existing debt
- waive as visible accepted residual
- suppress when the finding is intentionally non-actionable noise
- promote to runtime follow-up when the advisory finding exposes a real product defect

## Escalation Rule

If an advisory finding requires a production code change, create or link the
runtime work item and then re-check the corresponding `runtime-source` view.
