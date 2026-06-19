# ACI General-Purpose Completion Plan

- Drafted: 2026-06-20
- Builds on: `docs/AUDIT_2026-06-19_GENERAL_PURPOSE_READINESS.md`,
  `docs/AUDIT_2026-06-19_REMEDIATION_PLAN.md`, `docs/roadmap/ACI_COMPLETION_POLICY.md`
- Each phase has a **mechanically verifiable closure gate** (a command/test a
  reviewer can re-run), consistent with the evidence-based audit.

## Target definition (what "complete general-purpose" means here)

ACI = **Python-native structural core + fully live-verified multi-language
orchestration of best-in-class analyzers**, honestly bounded.

- This is the *orchestration model* of general-purpose, the only realistic path.
- **Explicit non-goal**: self-implemented native structural/taint detectors for
  languages other than Python. That competes with CodeQL/Semgrep and is a
  multi-year effort; ACI borrows multi-language depth via orchestration. Native
  structural depth stays Python.

## Present position (2026-06-20)

- execution-ready (12): ruff, pyflakes, mypy, pytest, semgrep, eslint, tsc,
  shellcheck, sqlfluff, osv-scanner, trivy, gitleaks
- availability-only (1): codeql
- **live-verified (8 lanes, real binaries run)**: ruff, mypy, pytest, semgrep
  (JS+multi-language), sqlfluff (SQL), shellcheck (shell), trivy (deps), gitleaks
  (secrets)
- **not yet live-verified**: eslint, tsc (Windows `.CMD` + eslint flat-config),
  osv-scanner (not installed in this env), codeql (opt-in)

## Phase G1 — Every executable lane live-verified in CI

Goal: turn "execution-ready by construction" into "proven to run" for all 12.

Tasks:
1. CI (Linux) installs the remaining binaries: gitleaks, trivy, osv-scanner
   (release binaries / apt), eslint + typescript (npm). shellcheck is preinstalled
   on ubuntu-latest.
2. Fix the eslint lane: eslint v9 needs a flat config to lint. Ship a bundled
   baseline `eslint.config` and pass it, or run with an explicit config path, so
   eslint actually produces findings instead of a config error.
3. Resolve the Windows npm-shim invocation (`.CMD` cannot be launched by
   `subprocess(shell=False)`): resolve the executable via `shutil.which` to its
   real path, or document Windows-needs-WSL for the npm lanes. Linux/macOS are
   unaffected.
4. Verify the osv-scanner adapter against the real binary; fix any command quirk
   the live run surfaces (as live runs already did for sqlfluff and gitleaks).

Closure gate (mechanical):
- `pytest shared/tests/test_aci_external_analyzer_e2e.py` runs a live e2e per
  execution-ready analyzer (skip only on a documented platform exception), and
  the CI Linux job installs every one so none is skipped there.
- Verify: number of live-e2e tests == number of execution-ready analyzers minus
  documented platform exceptions.

Risk: medium. CI binary installs are untested until CI runs; eslint flat-config
is a real behavior change.

## Phase G2 — codeql execution adapter

Goal: move codeql opt-in → execution-ready (the deep multi-language taint engine).

Tasks:
1. Build the database-create → analyze pipeline per detected language
   (`codeql database create` then `codeql database analyze ... --format=sarif`).
2. Add a SARIF parser normalizing codeql results into CI-IDs.
3. Make it execution-ready: run when codeql is installed and a DB can be built;
   otherwise return a clear downstream-setup state.

Closure gate (mechanical):
- `show-analyzer-availability` reports `codeql` execution_support_level ==
  `execution-ready`.
- A CI job that installs codeql runs a live e2e producing a normalized finding on
  a small multi-language target.

Risk: high. codeql DB-build is heavy, per-language, and slow; may warrant a
dedicated CI job rather than the main matrix.

## Phase G3 — Multi-language taint depth

Goal: prove source→sink taint across languages (the SAST definition), not just
Python intra-procedural (CI14_TAINTED_FLOW).

Tasks:
1. Curate semgrep taint-mode rules (source→sink) for the major languages in the
   bundled `aci-semgrep-rules.yml`; optionally add codeql taint queries (Phase G2).
2. Add a multi-language taint fixture pack (e.g., JS request param → eval;
   Python request → subprocess) and assert detection through the orchestrated lane.

Closure gate (mechanical):
- An e2e test scans the multi-language taint fixtures with semgrep installed and
  asserts a normalized source→sink finding for at least JS and Python.

Risk: medium. Depends on rule quality (precision vs. recall on real code).

## Phase G4 — Positioning and completion contract

Goal: declare the completed product honestly.

Tasks:
1. README + `aci-product-boundary-and-coverage-policy.md`: state ACI is a
   general-purpose code audit tool = Python-native core + complete live-verified
   orchestration, with the explicit native-Python boundary and the non-goal above.
2. `docs/roadmap/ACI_COMPLETION_POLICY.md`: add the "general-purpose complete"
   closure criteria (G1+G2+G3 gates met) and maturity gate.
3. `shared/python/aci_known_limits.py`: remove gaps closed by G1–G3; keep honest
   residuals (platform exceptions, opt-in tools requiring downstream setup).

Closure gate (mechanical):
- grep confirms the positioning wording is present and no now-false boundary
  claim remains; the completion-policy closure section exists; known-limits and
  the sample-report assets stay in sync (`test_sample_report_asset_known_limits_stay_in_sync`).

## Maturity gates

- **Working general-purpose (orchestration), live-proven** — reached today for 8
  lanes; G1 closes the remaining executable lanes.
- **Complete general-purpose (orchestration)** — G1 + G2 + G3 + G4 closed: every
  executable lane live-CI-proven, codeql wired, multi-language taint proven, and
  the product positioned honestly.

## Honest ceiling (stated, not hidden)

Even at completion, native structural/taint depth is Python-only; non-Python
depth is borrowed from orchestrated analyzers (proven to run). That is the same
shape as every "general-purpose" platform, which orchestrates rather than
re-implements per language. ACI does not claim language-general native analysis.
