# task_aci001 Trigger Routing Spec

Last updated: 2026-05-28

Purpose:

- separate `ACI` trigger routing from read-surface/read-budget rules
- keep caller routing stable without mixing it with operator reading policy

Boundary:

- this file is a `Pier` trigger-routing spec only
- generic `ACI` templates and common contracts stay at the repo root and `templates/`

Scope:

- `Pier` current trigger moments
- caller -> profile mapping
- non-trigger surfaces
- caller-proof status

## Fixed Trigger Rule

`ACI` is not ad hoc. In `Pier`, it is allowed to run only at fixed moments.

| moment | trigger status | profile | caller surface |
|---|---|---|---|
| task start | active | `startup` | `session_start.py` |
| quick governance gate | active | `quick-gate` | `governance_healthcheck.py --quick` |
| full governance audit | active | `full` | `governance_healthcheck.py` |
| implementation wave close | active | `full` | explicit operator / LE run |
| PR preflight | active | `build-review` or `full` | `aci_build_gate.py` or explicit operator / LE run |
| merge preflight | active | `build-review` or `full` | `aci_build_gate.py` or explicit operator / LE run |
| state transition guard | active | `state-change` | `update_task_state.py` |
| wrap-up guard | active | `wrap-up` | `wrap_up.py` |
| build-side pre-implementation | active | `build-preflight` | `aci_build_gate.py` |
| build-side post-diff | active | `build-review` | `aci_build_gate.py` |

## Reserved Companion Trigger Rule

The following trigger moments are reserved for a project-local dirty-tree discipline companion lane.

They are **not** active generic `ACI` routes yet.

| moment | trigger status | profile / lane | caller surface |
|---|---|---|---|
| handoff preparation | reserved | `dirty-tree-discipline` companion lane | explicit operator / Codex run |
| pre-commit review | reserved | `dirty-tree-discipline` companion lane | explicit operator / Codex run |
| lane switch review | reserved | `dirty-tree-discipline` companion lane | explicit operator / Codex run |
| end-of-session review | reserved | `dirty-tree-discipline` companion lane | explicit operator / Codex run |

## Non-Trigger Rule

The following are projection consumers only and must not become broad `ACI` callers.

- `report.py`
- `mcp_server.py`
- `regenerate_docs.py`
- `update_task_state_query.py`

## Caller-Proof Status

Current code-proven active callers:

- `session_start.py` -> `startup`
- `governance_healthcheck.py --quick` -> `quick-gate`
- `governance_healthcheck.py` full path -> `full`
- `update_task_state.py` -> `state-change`
- `wrap_up.py` -> `wrap-up`
- `aci_build_gate.py` -> `build-preflight` / `build-review`

Reserved only; not yet code-proven:

- dirty-tree discipline companion lane -> no authoritative caller yet

## Weakness Resolution Rule

Weak points must not stay as vague "known issues". Each one has a fixed resolution path.

### R1. `state-change` activation rule

`state-change` is active because all of the following are code-proven:

1. `update_task_state.py` or `update_task_state_cmd.py` calls `ACI` directly in the runtime path.
2. The caller passes explicit changed-file or bounded-path evidence.
3. The caller surface shows state-plane-only results rather than full ranked findings.

### R2. `wrap-up` activation rule

`wrap-up` is active because all of the following are code-proven:

1. `wrap_up.py` calls `ACI` directly in the runtime path.
2. The caller limits the read to unresolved carry or close-relevant summary.
3. The caller does not reopen broad historical detail by default.

### R3. `build-preflight` / `build-review` activation rule

These profiles are active because one repo-level entrypoint is now authoritative.

Required shape:

1. one stable caller surface
2. bounded changed-scope or module-scope input
3. stable verification output contract

### R4. active-to-reserved fallback rule

If a caller later loses bounded path evidence, or silently widens into full-repo behavior, the route must be treated as degraded and reviewed again rather than assumed active forever.

## Operational Separation

- front-stage security guard
  - immediate prevention during write / diff / commit flow
- back-stage `ACI`
  - residual inspection after implementation work

`ACI` must not be used as a substitute for front-stage security guard behavior.
