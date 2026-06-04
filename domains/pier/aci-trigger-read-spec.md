# task_aci001 Trigger Read Spec

Last updated: 2026-05-28

Purpose:

- define what each `ACI` trigger may read
- prevent broad, unnecessary reading that wastes tokens or runtime cost
- separate read-budget policy from trigger routing

Boundary:

- this file is a `Pier` trigger read-spec only
- generic `ACI` templates and common contracts stay at the repo root and `templates/`

Scope:

- trigger-specific read surfaces
- allowed scan scope
- forbidden broad reads
- current weak points

## Read-Spec By Trigger

| trigger/profile | allowed read surface | expected scan scope | forbidden default reads |
|---|---|---|---|
| `startup` | current summary only, top-level findings count, signal summary | bounded `project-current` cohort | remediation packet bodies, detail refs, workspace outputs, archive shelves |
| `quick-gate` | top-level findings, fail-close candidates, signal/count summary | bounded `project-current` cohort | historical detail payloads, remediation markdown, broad generated artifacts |
| `full` | summary + detail refs + ranked findings + history summary | `full-repo` allowed | none, except archive/workspace authority promotion |
| `state-change` | changed files + caller adjacency + state-plane relevant findings only | `changed-scope` required | full-repo sweep by default |
| `wrap-up` | unresolved carry + close-relevant summary only | `project-current` or `changed-scope` | broad historical reread, remediation packet bulk load |
| `build-preflight` | changed files / bounded module + external analyzer evidence | `changed-scope` or `module-scope` only | full-repo |
| `build-review` | changed files / bounded module + external analyzer evidence + verification result | `changed-scope` or `module-scope` only | full-repo |

## Reserved Companion Read-Spec

For the reserved dirty-tree discipline companion lane, the read contract is:

| trigger/profile | allowed read surface | expected scan scope | forbidden default reads |
|---|---|---|---|
| `dirty-tree-discipline` companion lane | dirty path list, placement/boundary rules, active closure board/register when present | `dirty-paths-only` | broad historical shelf reread, archive payload bodies, generated artifact bodies beyond classification need |

## Reading Rule

1. Read the thinnest surface that can answer the current decision.
2. Do not open remediation packet bodies unless the caller is already in a remediation step.
3. Do not open `workspace/` or `archive/` as authority for `startup`, `quick-gate`, `state-change`, or `wrap-up`.
4. `report.py` / `mcp_server.py` / `update_task_state_query.py` consume projection; they do not widen read scope.
5. dirty-tree discipline may read path/rule metadata, but it must not widen into historical-content rereads just to classify ownership.

## Current Weak Points Found

### W1. `startup` caller was narrowed

`session_start.py` currently calls:

- `ScanConfig(profile="startup", root=repo, paths=(shared/tools, shared/docs/tasks, index))`

The caller now passes an explicit bounded cohort:

- `shared/tools`
- `shared/docs/tasks`
- `index`

Current verdict:

- caller proof is explicit
- next optimization target only if runtime cost still drifts

### W2. `quick-gate` caller was narrowed

`governance_healthcheck.py` currently calls:

- `ScanConfig(profile="quick-gate", root=repo, paths=(shared/tools, shared/docs/tasks, index))`

The caller now passes the same explicit bounded cohort:

- `shared/tools`
- `shared/docs/tasks`
- `index`

Current verdict:

- caller proof is explicit
- next optimization target only if output drift rises

### W3. `state-change` and `wrap-up` now have caller proof

The tool body and repo-level callers are now fixed.

Current verdict:

- they are active
- both pass bounded path evidence and keep output local

## Weakness Resolution Rule

### R1. `startup` narrowing target

`startup` narrowing is complete for the current caller:

1. keep operator read summary-only
2. pass a bounded `project-current` path cohort explicitly
3. add a projection-first fast path if runtime cost still drifts

### R2. `quick-gate` narrowing target

`quick-gate` narrowing is complete for the current caller:

1. keep fail-close summary first
2. pass a bounded `project-current` path cohort explicitly
3. only open detail refs when a fixed fail-close condition is already present

### R3. `state-change` / `wrap-up` activation target

These profiles are fixed by both read policy and runtime caller proof.

They become valid only after:

1. caller proof exists
2. bounded path evidence is passed
3. the caller output remains state-local or close-local

### R4. build-side caller target

`build-preflight` and `build-review` are now lifted behind one stable repo-level entrypoint: `aci_build_gate.py`.

The entrypoint must preserve:

1. changed/module scope only
2. explicit verification evidence
3. no silent escalation to full-repo

## Overreaction Weakness

Another weak point is overreaction: broad findings can be surfaced too early, too loudly, or as a blocker when the caller only needed a thin decision.

### Anti-Overreaction Rule

1. `startup` and `quick-gate` must not stop work on counts alone.
2. `startup` and `quick-gate` must not escalate to stop on medium/low findings by themselves.
3. stop behavior is allowed only for fixed fail-close conditions already recognized by the caller contract.
4. summary-first callers must render top signals and next action, not raw finding floods.
5. if scope proof is weak or missing, the result must degrade to `review-needed` behavior rather than a hard stop.
6. `full` may surface ranked detail; non-`full` triggers must default to suppression of detail refs until explicit drilldown.

## Mandatory Narrowing Rule

When a trigger can be satisfied by:

- summary text
- counts
- top-level signal ids
- next action

it must not escalate itself into:

- detail refs
- remediation packet bodies
- historical report rereads
- workspace-generated artifact sweeps

This is the fixed token-saving rule for `ACI` current operation in `Pier`.
