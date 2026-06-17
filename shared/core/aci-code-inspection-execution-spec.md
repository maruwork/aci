# ACI Code Inspection Execution Spec

Status: Active

**Role**: generic inspection catalog and execution contract for code / docs / structure review.
**Pattern IDs**: 22 active patterns (`CI-01`, `CI-10`, `CI-16`, `CI-17`, `CI-27` retired).
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
| native-static | AST / text / structure can detect the issue directly | CI-02, CI-03, CI-04, CI-05, CI-06, CI-07, CI-12, CI-13, CI-14, CI-18, CI-19, CI-20, CI-21, CI-22, CI-23, CI-25, CI-26 |
| external analyzer | lint / type / test / dependency tooling gives stronger proof | CI-07, CI-09, CI-13, CI-14, CI-15, CI-21, CI-23, CI-25 |
| human judgment | design intent, ownership, or domain meaning is required | CI-04, CI-08, CI-11, CI-19, CI-24 |

One finding may cross lanes. Split it before handoff if different owners must decide different parts.

### Supported External Analyzers

| Analyzer | Language | CI IDs | Notes |
|---|---|---|---|
| ruff | Python | CI-02, CI-07, CI-13, CI-14, CI-15, CI-21, CI-23, CI-25 | default for quick-gate, build-preflight, build-review, full when `.py` files are present |
| pyflakes | Python | CI-07, CI-13, CI-21 | default for quick-gate and above when `.py` files are present |
| mypy | Python | CI-23 | default for build-preflight and above when `.py` files are present |
| pytest | Python | CI-09 | default for build-review and full when `.py` files are present |
| eslint | JS / TS | CI-02, CI-07, CI-13, CI-14, CI-21, CI-23 | default for build-preflight, build-review, and full when JS/TS files are present |
| tsc | TypeScript | CI-23 | default for build-preflight, build-review, and full when TS files and `tsconfig.json` are present |
| shellcheck | Shell | CI-02, CI-21 | default for build-preflight, build-review, and full when `.sh`/`.bash` files are present |
| sqlfluff | SQL | CI-02 | default for build-preflight, build-review, and full when `.sql` files are present |

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
| CI-02 | Spaghetti Code | tangled control flow, unclear state movement, unreadable branching | native-static |
| CI-03 | Patchwork Code | leftover TODO/FIXME/HACK, partial migrations, stitched exceptions, local hacks | native-static |
| CI-04 | God Class / God Object | one module/class owning too many unrelated responsibilities | native-static / human judgment |
| CI-05 | Copy-Paste Programming | repeated logic, repeated try/except, duplicated query or validation patterns | native-static |
| CI-06 | Magic Number / String | scattered literal status, role, path, timeout, policy, or error values | native-static |
| CI-07 | Lava Flow | unused, unreachable, or obsolete code kept without live caller or reason | native-static (cross-file dead private symbols) / external analyzer |
| CI-08 | Configuration Hell | config split across files/env/defaults without clear precedence | human judgment |
| CI-09 | Test Rot | stale tests, skipped tests, brittle fixtures, or tests no longer covering behavior | external analyzer |
| CI-11 | Golden Hammer | one mechanism forced onto problems that need a different control point | human judgment |
| CI-12 | Poltergeist | tiny pass-through classes/functions adding indirection without ownership | native-static |
| CI-13 | Dependency Rot | outdated, unused, unsafe, or mismatched dependency / import surface | native-static (cross-file circular imports) / external analyzer |
| CI-14 | Security Neglect | secrets, unsafe input handling, weak auth, unsafe file or shell behavior | native-static / external analyzer |
| CI-15 | Documentation Rot | docs contradict code, generated snapshots, task state, or canonical rules | external analyzer |
| CI-18 | Data Clump | repeated parameter groups or record shapes without an explicit contract | native-static |
| CI-19 | Feature Envy | code reaching into another owner or domain instead of using a boundary | native-static (domain-aware) / human judgment |
| CI-20 | Shotgun Surgery | one concept scattered across many files with no single edit point | native-static |
| CI-21 | Error Handling Rot | swallowed errors, broad exceptions, unsafe fallback, unbounded retry | native-static |
| CI-22 | Resource Lifecycle Leak | file/socket/session/process/transaction lifecycle not closed or bounded | native-static |
| CI-23 | Interface / Contract Drift | producer/consumer, schema, API, output, or generated contract mismatch | native-static |
| CI-24 | Observability Gap | missing logs, evidence, metrics, audit trail, or operator readback | human judgment |
| CI-25 | Nondeterminism / Environment Drift | time/order/env/path/locale/randomness changes behavior unpredictably | native-static |
| CI-26 | Concurrency / Race Hazard | shared mutable state, lock gap, transaction race, async ordering issue | native-static |

## 5. Out-of-Scope Detection Notes

Patterns considered for detection and intentionally excluded. Document the reason so the decision is not relitigated.

### Retired signal IDs

CI-01, CI-10, CI-16, CI-17, CI-27 are retired and will not be reassigned. Reason: excluded at initial catalog design; no implementation record remains.

### CI-06 Magic Number / String — excluded sub-patterns

| Pattern | Reason for exclusion |
|---|---|
| Magic string literals | Generic string literals cannot be reliably distinguished from intentional values without domain knowledge. Only absolute paths and hardcoded URLs would qualify universally, but these have too narrow a scope to justify a dedicated detector. Scattered string constants across multiple files are already covered by CI-20. |

### CI-21 Error Handling Rot — excluded sub-patterns

| Pattern | Reason for exclusion |
|---|---|
| Overbroad global / application-level catch | AST cannot identify the application entry point. A top-level `try/except` in a module could be initialization code, a CLI entry, or a test fixture. No universal structural rule applies. |
| Exceptions used as control flow | Whether exception use is intentional (e.g. `StopIteration` for iteration protocol) or misuse cannot be determined without understanding the author's intent. False-positive rate is too high for a generic detector. |
| Inconsistent catch granularity (too broad vs. too specific) | "Appropriate" exception granularity is domain-dependent. No universal threshold exists. |
| Duplicate logging across call stack | Detecting that the same error is logged at multiple levels requires call graph analysis. File-level AST inspection cannot track log calls across call boundaries. |
