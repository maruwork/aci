# ACI Completion Policy

Status: Active

## Purpose

Define the **execution order** and **closure criteria** for repo-local completion
work on the common `ACI` shelf. This is the doc referenced by
`shared/core/aci-product-boundary-and-coverage-policy.md` as the authority for
"execution-order and closure policy."

A phase is **closed** only when its closure criterion is mechanically verifiable
(a command, test, or grep that a reviewer can re-run), not by assertion.

## Scope Boundary

This policy governs completion of the **Python-first orchestration tool** defined
in `aci-product-boundary-and-coverage-policy.md`. It does **not** authorize
claiming language-general native coverage. Multi-language depth is delivered by
orchestrating external analyzers, not by re-implementing native detectors per
language (an explicit non-goal — see `docs/NON_GOALS.md`).

## Execution Order

Phases are ordered by dependency. Do not open a later phase before the earlier
phase's closure criterion holds. Phase detail and measured baselines live in
`docs/AUDIT_2026-06-19_REMEDIATION_PLAN.md`.

| Phase | Theme | Closure criterion (mechanical) |
|---|---|---|
| 0 | Correction — remove false/missing claims | `grep -c "All 17\|17 .*detectors" README.md` = 0; `test -f docs/roadmap/ACI_COMPLETION_POLICY.md`; `grep -ci alias shared/python/aci_known_limits.py` ≥ 1; contract/boundary "full coverage" wording downgraded |
| 1 | Python robustness — import/name-resolution pass | alias/nested-call fixture pack reaches recall = 1.0 in `aci_validation_scorecard.py`; existing clean precision unchanged |
| 2 | Independent evaluation — break circularity | precision/recall computed on a corpus the detectors were **not** tuned on; `recall_probe` reports known-limits instead of excluding them from pass/fail |
| 3 | Taint / dataflow for security IDs | source→sink fixture suite detected; constant-flow control set produces no false positive |
| 4 | Orchestration formalization | positioning doc states "orchestrator, not native polyglot"; `codeql`/`gitleaks`/`osv-scanner`/`trivy` move from `opt-in` to `execution-ready` and return normalized findings |
| 5 | Maintenance debt | `ci_22.py` reduced to a principled escape/ownership analysis with CI-22 recall unchanged |

## Closure Rule

- Phase 0, 1, 4, 5 closure is checkable with existing tooling
  (`grep` / `test -f` / `aci_validation_scorecard.py` / `wc -l` /
  `show-analyzer-catalog`).
- Phase 2 and 3 closure requires building the measurement harness
  (independent labeled corpus; taint fixtures) as part of that phase's
  deliverable.

## Maturity Gates

- "Honest, robust Python-first tool": Phase 0 + 1 + 2 closed. ✅ **REACHED**
- "General-purpose code-audit tool (orchestration model)": additionally Phase
  3 + 4 closed. ✅ **REACHED (2026-06-20)**

Both maturity gates are now reached. Public docs may describe ACI as a
**completed general-purpose code-audit tool on the orchestration model** — with
the explicit, non-negotiable boundary that native structural and
intra-procedural taint depth is Python-only and multi-language depth is borrowed
from orchestrated analyzers (an explicit non-goal to re-implement them). The
honest blind spots in `shared/python/aci_known_limits.py` remain in force; the
completion claim is the orchestration model, not language-general native depth.

## General-Purpose Completion Closure (G1–G4)

The newer `docs/ACI_GENERAL_PURPOSE_COMPLETION_PLAN.md` refines Phase 3 + 4 into
four mechanically-gated steps; all are closed:

| Gate | Theme | Closure evidence (re-runnable) |
|---|---|---|
| G1 | Every executable lane live-verified | `pytest shared/tests/test_aci_external_analyzer_e2e.py` runs a live e2e per execution-ready analyzer; CI installs each tool so none skips there |
| G2 | codeql execution adapter | `show-analyzer-availability` reports `codeql` execution-ready; the `codeql-e2e` CI job builds a DB, analyzes, and normalizes a real data-flow finding |
| G3 | Multi-language source→sink taint | `test_semgrep_lane_detects_multilang_taint_flow` asserts a normalized CI-14 source→sink finding for **both** JS and Python through the default lane |
| G4 | Honest positioning | `README.md` + `aci-product-boundary-and-coverage-policy.md` state the orchestration-complete claim with the native-Python boundary; no now-false "codeql availability-only" / "until the shelf gains a database-build adapter" claim remains; known-limits and sample-report assets stay in sync (`test_sample_report_asset_known_limits_stay_in_sync`) |

"Complete general-purpose (orchestration)" = G1 + G2 + G3 + G4 all closed.

## Reading Order

1. `shared/core/aci-product-boundary-and-coverage-policy.md`
2. `docs/AUDIT_2026-06-19_GENERAL_PURPOSE_READINESS.md` (audit evidence)
3. `docs/AUDIT_2026-06-19_REMEDIATION_PLAN.md` (phase detail + baselines)
4. This policy (execution order + closure)
