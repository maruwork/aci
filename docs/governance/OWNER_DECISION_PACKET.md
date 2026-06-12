# ACI Owner Decision Packet

Status: Active

## Purpose

Collect the minimum owner decisions required to move from publishable hold to actual publication, in one execution-grade authority surface.

## Blocking Decisions

Each decision must be filled before actual publication.

## Owner Answer Format

Every blocking decision must be recorded with the following fields:

- `state`: `open` / `chosen`
- `owner answer`: the chosen value
- `owner rationale`: why that value was chosen
- `downstream action target`: which publication step/doc must change because of the answer
- `blocking`: whether publication must stop until this answer exists

### License Decision

- state: chosen
- blocking: yes
- owner answer:
  - chosen license: `MIT`
- owner rationale:
  - why this license matches ACI reuse posture: permissive reuse is appropriate for a generic inspection tool and lowers friction for first public evaluation
- downstream action target:
  - `LICENSE` file in the standalone repository
  - contribution/publication wording that depends on the chosen license
- source note: `PRE_PUBLICATION_DECISIONS.md`
- owner must decide:
  - chosen license
  - confirmation that downstream reuse posture matches that license
- downstream effect:
  - license file added during export/go-live
  - contribution expectations must remain compatible with the chosen license

### Repository Host Decision

- state: chosen
- blocking: yes
- owner answer:
  - GitHub owner/org: `fumimaruwork`
  - repository name: `aci`
  - initial visibility: `private`
- owner rationale:
  - why this host/owner/visibility combination is appropriate: private-first creation preserves a final verification window before public release while keeping the target public owner fixed
- downstream action target:
  - standalone repository creation target
  - publication runbook repository/visibility steps
- source note: `PRE_PUBLICATION_DECISIONS.md`
- owner must decide:
  - GitHub owner/org
  - repository name
  - initial visibility
- downstream effect:
  - standalone repository creation target is fixed
  - go-live sequence can name the real repository

### Public Contribution Surface Decision

- state: chosen
- blocking: yes
- owner answer:
  - issue policy: issues may be opened from day one for bugs, docs, and bounded enhancement requests
  - pull request policy: pull requests are accepted from day one and require maintainer review before merge
  - accept public contributions from day one: `yes`
- owner rationale:
  - why this contribution posture fits the first public release: open issue intake supports evaluation while maintainer-reviewed PRs keep early-surface changes bounded
- downstream action target:
  - `CONTRIBUTING.md`
  - public-facing repository guidance
- source notes:
  - `CONTRIBUTING.md`
  - `SECURITY.md`
- owner must decide:
  - issue policy
  - pull request policy
  - security-report intake posture
- downstream effect:
  - `CONTRIBUTING.md` remains the active repository contribution surface

### Public CI Scope Decision

- state: chosen
- blocking: yes
- owner answer:
  - minimum public verification surface: `python shared/python/aci_public_smoke.py` and `python -m py_compile shared/python/*.py domains/pier/python/*.py`
  - CI required at repository creation or allowed immediately after: required at repository creation
- owner rationale:
  - why this verification posture is sufficient for first publication: it validates core mode loading, optional domain loading, normalized finding emission, mirror synchronization, and python shelf integrity before public exposure
- downstream action target:
  - `PUBLIC_RELEASE_CHECKLIST.md`
  - `RELEASE_BOOTSTRAP_NOTES.md`
  - private/public CI wiring step
- source notes:
  - `PUBLIC_RELEASE_CHECKLIST.md`
  - `RELEASE_BOOTSTRAP_NOTES.md`
- owner must decide:
  - minimum smoke/sample validation surface
  - whether public CI is required at repo creation or may follow immediately after
- downstream effect:
  - go-live sequence can declare what must pass before publication

### Public Security Intake Decision

- state: chosen
- blocking: yes
- owner answer:
  - security-report intake posture: use GitHub private vulnerability reporting if enabled
  - private disclosure from day one: `yes`
  - promised response posture: best effort, no fixed SLA at first publication
- owner rationale:
  - why this security posture is supportable at first publication: it provides a standard intake path without committing to an unsupported response guarantee
- downstream action target:
  - `SECURITY.md`
  - public security policy wording
- source notes:
  - `SECURITY.md`
  - `RELEASE_BOOTSTRAP_NOTES.md`
- owner must decide:
  - security-report intake posture
  - whether private disclosure is supported from day one
  - any promised response posture
- downstream effect:
  - `SECURITY.md` remains the active repository security policy

## What Is Already Settled

- public-facing commands are repo-relative
- public-facing file paths are repo-relative
- standalone root shape is documented
- smoke and sample validation are locally demonstrable
- pre-publication draft assets exist

## Decision Closure Rule

Publication execution is ready only when every blocking decision above has:

- a chosen value
- an owner-confirmed rationale
- a downstream action target in the runbook
- `state: chosen`
