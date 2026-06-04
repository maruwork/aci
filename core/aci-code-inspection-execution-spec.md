# ACI Code Inspection Execution Spec

**Role**: generic inspection catalog and execution contract for code / docs / structure review.
**Pattern IDs**: `CI-01` to `CI-27`.
**Primary use**: decide what to inspect, how to classify findings, and what a valid report must contain.
**Boundary**: this is not current task state, not DB runtime truth, and not a project-local gate by itself.

## 1. Reading Rule

Use this file as a compact catalog.

- Use `CI-*` rows to select inspection angles.
- Use severity and lane guidance to route findings.
- Put project-specific trigger, owner, output path, and exception rules in a project-local overlay.
- Do not turn examples, comments, or historical notes into live findings without checking the actual target file.

## 2. Inspection Lanes

| Lane | Use When | Typical CI IDs |
|---|---|---|
| native-static | AST / text / structure can detect the issue directly | CI-02, CI-03, CI-05, CI-06, CI-12, CI-13, CI-18, CI-20, CI-21, CI-22, CI-23, CI-25, CI-26 |
| external analyzer | lint / type / test / dependency tooling gives stronger proof | CI-07, CI-09, CI-10, CI-13, CI-14, CI-15, CI-21, CI-23, CI-25 |
| human judgment | design intent, ownership, or domain meaning is required | CI-01, CI-04, CI-11, CI-16, CI-17, CI-19, CI-24, CI-27 |

One finding may cross lanes. Split it before handoff if different owners must decide different parts.

## 3. Classification Rule

Use three finding classes.

| Class | Meaning | Expected Action |
|---|---|---|
| confirmed defect | concrete bug, safety hole, contract drift, or maintainability break | fix or explicitly defer with owner and reason |
| design / review question | plausible weakness requiring domain or owner judgment | handoff with evidence and question |
| noise / not applicable | sample text, historical note, intentional exception, or unsupported signal | close with reason; do not inflate counts |

Severity should reflect blast radius, not how easy the issue was to spot.

| Severity | Use For |
|---|---|
| CRITICAL | data loss, security exposure, authority bypass, false close, or silent corruption |
| HIGH | likely runtime failure, governance bypass, contract break, or major maintenance trap |
| MEDIUM | local defect, unclear ownership, test gap, or contained maintainability issue |
| LOW | wording, style, or weak signal that does not change behavior or authority |

## 4. Compact CI Catalog

| ID | Pattern | Inspect For | Primary Lane |
|---|---|---|---|
| CI-01 | AI Slop | generic-looking code or docs that do not fit the actual domain / contract | human judgment |
| CI-02 | Spaghetti Code | tangled control flow, unclear state movement, unreadable branching | native-static |
| CI-03 | Patchwork Code | leftover TODO/FIXME/HACK, partial migrations, stitched exceptions, local hacks | native-static |
| CI-04 | God Class / God Object | one module/class owning too many unrelated responsibilities | human judgment |
| CI-05 | Copy-Paste Programming | repeated logic, repeated try/except, duplicated query or validation patterns | native-static |
| CI-06 | Magic Number / String | scattered literal status, role, path, timeout, policy, or error values | native-static |
| CI-07 | Lava Flow | unused, unreachable, or obsolete code kept without live caller or reason | external analyzer |
| CI-08 | Configuration Hell | config split across files/env/defaults without clear precedence | human judgment |
| CI-09 | Test Rot | stale tests, skipped tests, brittle fixtures, or tests no longer covering behavior | external analyzer |
| CI-10 | Cargo Cult Programming | copied patterns without required surrounding contract or reason | external analyzer |
| CI-11 | Golden Hammer | one mechanism forced onto problems that need a different control point | human judgment |
| CI-12 | Poltergeist | tiny pass-through classes/functions adding indirection without ownership | native-static |
| CI-13 | Dependency Rot | outdated, unused, unsafe, or mismatched dependency / import surface | external analyzer |
| CI-14 | Security Neglect | secrets, unsafe input handling, weak auth, unsafe file or shell behavior | external analyzer |
| CI-15 | Documentation Rot | docs contradict code, generated snapshots, task state, or canonical rules | external analyzer |
| CI-16 | Premature Optimization | complexity added before evidence of performance or scale need | human judgment |
| CI-17 | Over-Engineering | unnecessary abstraction, framework, genericity, or multi-layer routing | human judgment |
| CI-18 | Data Clump | repeated parameter groups or record shapes without an explicit contract | native-static |
| CI-19 | Feature Envy | code reaching into another owner or domain instead of using a boundary | human judgment |
| CI-20 | Shotgun Surgery | one concept scattered across many files with no single edit point | native-static |
| CI-21 | Error Handling Rot | swallowed errors, broad exceptions, unsafe fallback, unbounded retry | native-static |
| CI-22 | Resource Lifecycle Leak | file/socket/session/process/transaction lifecycle not closed or bounded | native-static |
| CI-23 | Interface / Contract Drift | producer/consumer, schema, API, output, or generated contract mismatch | native-static |
| CI-24 | Observability Gap | missing logs, evidence, metrics, audit trail, or operator readback | human judgment |
| CI-25 | Nondeterminism / Environment Drift | time/order/env/path/locale/randomness changes behavior unpredictably | native-static |
| CI-26 | Concurrency / Race Hazard | shared mutable state, lock gap, transaction race, async ordering issue | native-static |
| CI-27 | Patchwork Structure / ツギハギ構造 | bridge-on-bridge layering, partial authority moves, duplicated mapping shelves, or long-lived temporary seams that leave the structure stitched together | human judgment |
