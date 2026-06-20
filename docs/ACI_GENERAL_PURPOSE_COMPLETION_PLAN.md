# ACI General-Purpose Completion Plan

- Drafted: 2026-06-20
- Builds on: `docs/AUDIT_2026-06-19_GENERAL_PURPOSE_READINESS.md`,
  `docs/AUDIT_2026-06-19_REMEDIATION_PLAN.md`, `docs/roadmap/ACI_COMPLETION_POLICY.md`
- Each phase has a **mechanically verifiable closure gate** (a command/test a
  reviewer can re-run), consistent with the evidence-based audit.

## Target definition (what "complete general-purpose" means here)

Completion is **balanced orchestration**, not in-housing features. ACI =
**Python-native structural core + fully live-verified multi-language orchestration
of best-in-class analyzers**, honestly bounded — held at an *equilibrium*, not
driven toward maximal coverage.

- This is the *orchestration model* of general-purpose, the only realistic path.
- Completion is an equilibrium: past the balance point, adding native or bundled
  coverage is over-building and moves ACI *away* from complete. "More analyzers /
  languages / rules" is not "more complete". The authoritative definition of the
  balance — own only ACI's own taxonomy/adapters/Python core/closed baseline;
  borrow everything generic and multi-language; claim only what is live-CI-proven;
  no unbounded bundle growth — lives in the Canonical Completion Stance of
  `shared/core/aci-product-boundary-and-coverage-policy.md`.
- **Explicit non-goal**: self-implemented native structural/taint detectors for
  languages other than Python. That competes with CodeQL/Semgrep and is a
  multi-year effort; ACI borrows multi-language depth via orchestration. Native
  structural depth stays Python.

## Present position (2026-06-20, after G3)

- execution-ready (12): ruff, pyflakes, mypy, pytest, semgrep, eslint, tsc,
  shellcheck, sqlfluff, osv-scanner, trivy, gitleaks
- availability-only (1): codeql
- **G1 done — all 12 execution-ready lanes live-verified** (real binaries run and
  normalize findings): ruff/mypy/pytest (Python), semgrep (JS+multi-language),
  sqlfluff (SQL), shellcheck (shell), trivy + osv-scanner (deps), gitleaks
  (secrets), eslint (JS), tsc (TS). Live runs found and fixed six real invocation
  bugs (sqlfluff `--dialect`, gitleaks `detect`→`dir`, tsc exit-2, eslint flat
  config / unmatched-glob, Windows `.CMD` resolution) that parser-only tests could
  not catch. CI installs every tool so the e2e run there.
- **G2 done — codeql is execution-ready and live-verified**: a database-build →
  analyze (security-and-quality suite) → SARIF → normalized EXT_CODEQL pipeline.
  Live run flags a real data-flow finding (flask `request.args` → `eval`,
  `py/code-injection`) mapped to CI-14. codeql stays catalog `opt-in` (heavy, not
  run by default) but is now execution-ready. SARIF parser is unit-tested; the
  live e2e runs in a dedicated Linux CI job that installs the codeql bundle. Live
  runs surfaced two more real bugs (no query suite → empty SARIF; pack default
  suite is narrower than security-and-quality).
- **G3 done — multi-language source→sink taint proven through the default lane**:
  the bundled `aci-semgrep-rules.yml` now carries taint-mode rules
  (`aci.ci14.taint-js-code-injection`, `aci.ci14.taint-py-code-injection`) that
  track untrusted input through a local variable into a code-execution sink. A
  committed fixture pack (`shared/tests/fixtures/taint_multilang/`) encodes a JS
  (`req.query` → `eval`) and a Python (`request.args` → `eval`) flow, and
  `test_semgrep_lane_detects_multilang_taint_flow` asserts a normalized CI-14
  source→sink finding for **both** languages through the orchestrated lane.
  semgrep runs by default (codeql remains opt-in), so taint depth is now part of
  the default general-purpose scan, not an opt-in heavy lane. Live runs surfaced
  two more real bugs (a 10s version-probe edge that flapped semgrep's readiness on
  its ~9s cold start → widened to 30s; semgrep's default `tests/` ignore silently
  scanning zero files → fixtures copied to a neutral temp dir in the e2e).
- **all 13 cataloged analyzers are now execution-ready; none remain
  availability-only.**

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

## Phase G3 — Multi-language taint depth  ✅ DONE (2026-06-20)

Goal: prove source→sink taint across languages (the SAST definition), not just
Python intra-procedural (CI14_TAINTED_FLOW).

Closure evidence: `test_semgrep_lane_detects_multilang_taint_flow` scans the
committed `shared/tests/fixtures/taint_multilang/` pack with semgrep installed and
asserts a normalized CI-14 source→sink finding for both JS (`req.query` → `eval`)
and Python (`request.args` → `eval`) through the external-analyzer lane.

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
  lanes; G1 closes the remaining executable lanes. ✅
- **Complete general-purpose (orchestration)** — G1 + G2 + G3 + G4 closed: every
  executable lane live-CI-proven, codeql wired, multi-language taint proven, and
  the product positioned honestly. ✅ **REACHED (2026-06-20); CI green on the
  branch (test-linux + codeql-e2e + platform-smoke all pass).**

## Post-completion hardening — strengthening only, not complexification

G3's gate proved the taint baseline *fires*; "fires" is not "is precise". That
one residual is worth closing because it raises the **integrity of the existing
claim** without enlarging surface. The two distinct moves are kept apart on
purpose:

- **H1 (kept — strengthening) — taint precision is measured, not assumed.**
  `shared/tools/aci_taint_eval.py` runs the orchestrated semgrep taint lane over a
  curated corpus of source→sink **positives** (direct, one-hop, multi-hop, several
  sink kinds) and **control** flows that must stay silent (a constant fed to the
  sink, a tainted value that never reaches the sink, a source with no dangerous
  sink). `test_aci_taint_eval.py` gates **recall = 1.0 and false-positive
  rate = 0** on that corpus. The controls are the point: they prove the closed
  baseline *discriminates* a real flow from a look-alike, which a bare
  `eval()`-pattern match cannot. The corpus is small and bounded (it gates the
  closed JS+Python baseline; it does not grow). Honest caveat: a field
  false-positive rate still needs a labelled real-world corpus + human
  adjudication (same caveat as the native independent-eval noise surface).

- **H2 (reverted — complexification) — per-language taint expansion.**
  A Go taint rule was briefly added and then removed. Growing the bundled ruleset
  language-by-language is not strengthening the completed product: it adds a
  permanent, self-maintained surface that duplicates what `codeql` query suites
  and the `semgrep` registry already own, and it invites unbounded scope
  (Java? Rust? …). The orchestration-true answer for multi-language taint is to
  borrow the analyzers' maintained rulesets, not to enlarge ACI's bundle. The
  bundled taint baseline is therefore declared **closed** (JS + Python only); the
  DO/DON'T line is written into `aci-product-boundary-and-coverage-policy.md`
  ("Taint: What ACI Authors vs Borrows") so a future "add language X" change is
  rejected by policy, not by taste.

Closure gate (mechanical):
- `pytest shared/tests/test_aci_taint_eval.py` (semgrep installed) asserts
  recall=1.0 and false-positive-rate=0 across the closed JS + Python corpus; CI's
  Linux job installs semgrep so this runs there.
- `grep -c "languages: \[go\]" shared/python/package_assets/analyzers/aci-semgrep-rules.yml`
  = 0 (the bundle is not grown per-language).

## Honest ceiling (stated, not hidden)

Even at completion, native structural/taint depth is Python-only; non-Python
depth is borrowed from orchestrated analyzers (proven to run). That is the same
shape as every "general-purpose" platform, which orchestrates rather than
re-implements per language. ACI does not claim language-general native analysis.
