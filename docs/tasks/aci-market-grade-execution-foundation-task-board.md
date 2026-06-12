# ACI Market-Grade Execution Foundation Task Board

Status: Active

## Purpose

Turn the market-grade gap inventory into concrete implementation work without leaving any identified gap unassigned.

## Task Groups

### Scan Entry

- `MGEF-T1`
  - add a real `scan` command that accepts a target path
- `MGEF-T2`
  - define and implement scan session inputs: profile, domain pack, config, operations file
- `MGEF-T3`
  - split clean, findings, config error, runtime failure into distinct exit behavior

### Native Detection

- `MGEF-T4`
  - define detector interface and registration shape
- `MGEF-T5`
  - implement first real detector against target files
- `MGEF-T6`
  - define stable finding fingerprint generation
- `MGEF-T7`
  - implement finding dedup and merge behavior

### External Analyzer Runtime

- `MGEF-T8`
  - define analyzer adapter interface
- `MGEF-T9`
  - implement executable, version, and invocation readiness checks
- `MGEF-T10`
  - implement analyzer command execution with timeout handling
- `MGEF-T11`
  - normalize analyzer output into `ACI` findings

### Report Runtime

- `MGEF-T12`
  - emit real machine-readable JSON from a scan
- `MGEF-T13`
  - add full report schema validation
- `MGEF-T14`
  - add summary consistency validation
- `MGEF-T15`
  - add explicit report format versioning

### Repeated Operation

- `MGEF-T16`
  - load baseline entries from the operations file
- `MGEF-T17`
  - load and apply suppression entries
- `MGEF-T18`
  - load and apply waiver entries
- `MGEF-T19`
  - reflect baseline, suppression, and waiver state in finding rows and summaries
- `MGEF-T20`
  - implement finding lifecycle state transitions for repeated runs

### Scope And Ignore

- `MGEF-T21`
  - add include path support
- `MGEF-T22`
  - add exclude path support
- `MGEF-T23`
  - define and implement ignore-file behavior
- `MGEF-T24`
  - define binary-file handling
- `MGEF-T25`
  - define large-file handling
- `MGEF-T26`
  - define symlink traversal behavior

### Gate Behavior

- `MGEF-T27`
  - define gate result model
- `MGEF-T28`
  - implement fail-on-severity threshold
- `MGEF-T29`
  - implement fail-on-new-findings behavior
- `MGEF-T30`
  - implement fail-on-unreviewed-review-required-finding behavior
- `MGEF-T31`
  - expose machine-readable gate output

### Verification Hardening

- `MGEF-T32`
  - remove hardcoded success behavior from automation verification
- `MGEF-T33`
  - make installed-package proof lanes report real pass/fail state
- `MGEF-T34`
  - expand sample-report validation beyond field presence
- `MGEF-T35`
  - add failure coverage for broken analyzer runtime states

### Test Expansion

- `MGEF-T36`
  - add unit tests for config, findings, and parsers
- `MGEF-T37`
  - add detector fixture tests
- `MGEF-T38`
  - started
  - analyzer adapter tests now cover `pytest` no-tests, missing analyzer, readiness summary, `ruff` parsing, and `mypy` parsing
- `MGEF-T39`
  - add end-to-end scan tests on sample repositories
- `MGEF-T40`
  - add report schema and gate regression tests

### Integration

- `MGEF-T41`
  - define SARIF mapping
- `MGEF-T42`
  - implement SARIF emission
- `MGEF-T43`
  - validate SARIF against hosted ingestion expectations
- `MGEF-T44`
  - complete
  - `shared/python/aci_annotations.py` added with `build_github_annotations`; converts ACI report findings into GitHub Actions `::error`/`::warning`/`::notice` workflow command strings with percent-encoded parameter values; `emit-annotations --report <file>` CLI command added following the same pattern as `emit-sarif`

### Expanded Scan Classes

- `MGEF-T45`
  - decided: out of scope. ACI is a code quality inspection tool; secrets scanning is delegated to dedicated tools (gitleaks, truffleHog, etc.). CI-14 covers basic plaintext-secret detection in code and remains in scope.
- `MGEF-T46`
  - decided: out of scope. Dependency and supply-chain scanning is delegated to dedicated tools (Dependabot, pip-audit, etc.).
- `MGEF-T47`
  - decided: out of scope. IaC scanning is outside ACI's code quality inspection scope.
- `MGEF-T48`
  - decided: out of scope. Container scanning is outside ACI's code quality inspection scope.

### Performance And Safety

- `MGEF-T49`
  - complete
  - named constants `VERSION_PROBE_TIMEOUT_SECONDS`, `ANALYZER_TIMEOUT_SECONDS`, `ANALYZER_MAX_OUTPUT_BYTES` added to `shared/python/aci_analyzer_execution.py`; both `subprocess.run` calls now use the constants; stdout/stderr truncated to `ANALYZER_MAX_OUTPUT_BYTES` after execution; isolation rules (shell=False, output cap, timeout behavior, environment inheritance rationale) documented in module docstring
- `MGEF-T50`
  - complete
  - `_iter_target_files` in `shared/python/aci_scan.py` now sorts collected files by POSIX-normalized relative path (`_relative_path(p, root)`) instead of raw `Path` object order, ensuring identical scan order on Windows and POSIX; skipped-target list is also sorted by the same key; traversal and path normalization rules documented in module docstring
- `MGEF-T51`
  - complete
  - `MAX_SCAN_FILE_COUNT = 10_000` constant added to `shared/python/aci_scan.py`; enforced in `_iter_target_files` — files beyond the cap are recorded as `scan-file-count-limit-exceeded` skipped entries; `scope_rules.max_scan_file_count` added to scan output; scan safety guidance (read-only access, symlink skip, file-size cap, file-count cap, no code execution, scope restriction advisory) documented in module docstring
- `MGEF-T52`
  - complete
  - `DEFAULT_GENERATED_PATH_SEGMENTS` extended with `.venv`, `venv`, `env`, `dist`, `.eggs`, `.tox`, `htmlcov`, `.coverage`, `node_modules`; `scope_rules.generated_path_segments` (sorted list) added to every scan report; artifact hygiene rules (no writes to target, no temp files, caller-owned output lifecycle) documented in module docstring

### CI And Release Hardening

- `MGEF-T53`
  - decided: `.github/workflows/ci.yml` is ACI's own development CI only. The common shelf does not provide a reusable CI template for downstream projects; downstream projects define their own CI.
- `MGEF-T54`
  - complete
  - `.github/workflows/ci.yml` added; runs on push/PR to main; Python 3.11 and 3.12 matrix; steps: install package + analyzer deps, pytest full suite, ruff lint, mypy type check, aci automation-smoke, aci self-scan (informational, continue-on-error); all T37/T39/T40 tests are now CI-enforced
- `MGEF-T55`
  - complete
  - `_release_gate_checks` added to `shared/python/aci_installed_package_verification.py`: verifies `ACI_TOOL_VERSION` constant matches `pyproject.toml version` via regex (no import required), and validates sample reports via `validate_sample_reports()`; surfaced as `proof_lanes.release_gate` in `installed-package-check` output; `release-gate` CI job added to `.github/workflows/ci.yml` (runs on `v*` tags only, after test matrix passes: installed-package-check, build, wheel+sdist existence check)
- `MGEF-T56`
  - complete
  - `aci --version` flag added to CLI (outputs `aci {ACI_TOOL_VERSION}`); build provenance step added to `release-gate` CI job (records commit SHA, tag, Python version, build timestamp, and signing posture as JSON); posture defined: current=unsigned, intent=PyPI Trusted Publisher via OIDC (no long-lived secrets), future=Sigstore/Cosign, not-used=PGP/GPG

## Completion Rule

Do not mark this board complete until every gap in `workspace/aci-gap-assessment.md` maps to one or more completed tasks on this board.

## Current Progress

- `MGEF-T1`
  - complete
  - `scan` subcommand fully implemented in `shared/python/aci_cli.py` with target, profile, domain, operations-file, include/exclude paths, ignore-file, domain-file inputs
- `MGEF-T2`
  - complete
  - scan session inputs include target, profile, domain, config, and operations file; all accepted by `scan_target` and recorded in session and report
- `MGEF-T3`
  - complete
  - all five exit codes implemented: 0 clean, 1 findings-present, 2 config-error, 3 runtime-failure, 4 contract-error, 5 automation-verification-failure
- `MGEF-T4`
  - complete
  - `PerFileDetector` and `CrossFileDetector` Protocol types added to `shared/python/aci_scan.py`; per-file shape is `(path, text, target_root, next_id) -> list[AciFinding]`, cross-file shape is `(paths, root, next_id) -> list[AciFinding]`; all existing `_scan_*` functions satisfy the appropriate Protocol structurally via PEP 544
- `MGEF-T5`
  - complete
  - native detectors implemented for CI-02, CI-03, CI-05, CI-06, CI-12, CI-14 (plaintext-secret, dynamic-code, subprocess-shell, insecure-http), CI-18, CI-20, CI-21, CI-22, CI-23, CI-25, CI-26; structure signals (CI-04, CI-19, CI-24) handled via domain vocabulary; external analyzers cover CI-07, CI-09, CI-13, CI-15
- `MGEF-T6`
  - complete
  - stable SHA-256 fingerprint generation in `shared/python/aci_findings.py` using ci_id, signal, target_file, line, reason
- `MGEF-T7`
  - complete
  - `_deduplicate_findings` in `shared/python/aci_scan.py` deduplicates by fingerprint key using dict.setdefault
- `MGEF-T8`
  - complete
  - `AnalyzerReadiness` and `AnalyzerRunResult` dataclasses plus `run_analyzer` in `shared/python/aci_analyzer_execution.py`
- `MGEF-T9`
  - complete
  - `_readiness_for` checks executable visibility via `which` and probes version against minimum bounds
- `MGEF-T10`
  - complete
  - `run_analyzer` runs bounded subprocess with timeout=30, handles TimeoutExpired and OSError explicitly
- `MGEF-T11`
  - complete
  - `ruff`, `pyflakes`, `mypy`, and `pytest` output each normalized into ACI findings with CI-id mapping
- `MGEF-T12`
  - complete
  - `scan_target` returns full machine-readable JSON including tool, report_format_version, summary, findings, blockers, residuals, and gate
- `MGEF-T13`
  - complete
  - `validate-report` command checks report JSON against `REQUIRED_SAMPLE_TOP_LEVEL_FIELDS` and finding-row field contract
- `MGEF-T14`
  - complete
  - summary consistency validation checks finding-row counts against summary fields; blocker and residual rows materialized from real findings
- `MGEF-T15`
  - complete
  - `report_format_version: "1.0.0"` carried in every scan output and sample report
- `MGEF-T16`
  - complete
  - `load_operations_state` in `shared/python/aci_operations.py` loads baseline entries from TOML operations file
- `MGEF-T17`
  - complete
  - `find_matching_suppression` removes matching findings from visible output; suppressed_count recorded in summary
- `MGEF-T18`
  - complete
  - `find_active_waiver` applies waiver state to matching findings; waived findings remain visible with `accepted-residual` triage state
- `MGEF-T19`
  - complete
  - `_apply_operations` sets baseline_status, waiver_status, lifecycle_state, and triage_state on each finding; summary counts reflect all states
- `MGEF-T21`
  - complete
  - `--include-path` (repeatable) accepted by CLI and enforced in `_path_matches_filters`
- `MGEF-T22`
  - complete
  - `--exclude-path` (repeatable) accepted by CLI and merged with domain-level exclusions
- `MGEF-T23`
  - complete
  - `.aciignore` auto-loaded from target root; `--ignore-file` override accepted; patterns merged into exclude list
- `MGEF-T24`
  - complete
  - binary detection via null-byte check; unsupported suffixes both produce explicit `skipped_targets` entries
- `MGEF-T25`
  - complete
  - files exceeding `DEFAULT_MAX_FILE_BYTES` skip with `max-file-size-exceeded`; generated cache paths skip with `generated-path-skipped`
- `MGEF-T26`
  - complete
  - symlinks skip with `symlink-skipped` reason instead of relying on filesystem traversal behavior
- `MGEF-T27`
  - complete
  - `_build_gate_result` returns decision, blocking_severities, blocking_count, analyzer_failure_count, unreviewed_review_required_count, reasons, reason_details
- `MGEF-T28`
  - complete
  - `--severity-threshold` accepted by CLI and config; gate blocks findings at or above threshold that are not waived
- `MGEF-T29`
  - complete
  - `--fail-on-new-findings` flag adds `new-findings-present` reason when any new (non-baselined) finding remains
- `MGEF-T30`
  - complete
  - `--fail-on-unreviewed-review-required` flag adds `unreviewed-review-required` reason when any `LANE_HUMAN_JUDGMENT` finding has not been waived or baselined; supported in CLI, config, ScanSession, and gate output
- `MGEF-T31`
  - complete
  - gate output includes decision, blocking_severities, counts, reasons, reason_details, and all gate-control flags as machine-readable fields
- `MGEF-T32`
  - complete
  - `build_public_smoke_result` used as the real smoke dependency in `automation-smoke`; no fixed success values
- `MGEF-T33`
  - complete
  - `run_installed_package_check` returns real pass/fail state for each proof lane
- `MGEF-T34`
  - complete
  - `validate_sample_reports` checks every finding row and summary consistency in sample report JSON files
- `MGEF-T35`
  - complete
  - analyzer missing/timeout/spawn-failure/runtime-failure states surface in `AnalyzerRunResult.runtime_state` and can trigger gate failure via `fail_on_analyzer_errors`
- `MGEF-T36`
  - complete
  - `shared/tests/test_aci_runtime_scan.py` covers scan output, operations handling, skipped-target reporting, analyzer-error gates, SARIF conversion, ignore-file behavior, config-driven gate defaults
- `MGEF-T38`
  - complete
  - `shared/tests/test_aci_analyzer_execution.py` covers pytest no-tests, missing analyzer, readiness summary, ruff parsing, and mypy parsing
- `MGEF-T41`
  - complete
  - SARIF rule and result mapping defined in `shared/python/aci_sarif.py` with severity→level and fingerprint fields
- `MGEF-T42`
  - complete
  - `emit-sarif` command converts ACI report JSON into SARIF 2.1.0 with `$schema` and `runs[].tool.driver`
- `MGEF-T43`
  - complete
  - `validate-sarif` checks version, runs array, driver name, rules, result ruleId, and physicalLocation.artifactLocation.uri
- `MGEF-T20`
  - complete
  - `find_resolved_baseline_entries` added to `shared/python/aci_operations.py`; `scan_target` now computes resolved entries from pre-suppression findings and surfaces them as `resolved_baseline_entries` in the report and `resolved_baseline_count` in the summary
- `MGEF-T37`
  - complete
  - `shared/tests/test_aci_detector_fixtures.py` added; covers CI-02, CI-03, CI-05, CI-12, CI-14 (dynamic code, subprocess shell, plaintext secret, insecure HTTP), CI-18, CI-21, CI-22, CI-23, CI-25, CI-26 — each with a triggering fixture and a clean fixture; also includes T20 resolved-baseline test
- `MGEF-T39`
  - regressed
  - `shared/tests/test_aci_e2e_sample_packs.py` and its sample packs (`examples/aci-false-negative-challenge-pack/`, `examples/aci-precision-replay-pack/`) are missing. Not an intentional deletion; restoration required. Tracked separately as `MGEF-T39-restore`
- `MGEF-T40`
  - complete
  - `shared/tests/test_aci_report_and_gate_regression.py` added; covers report schema validation across clean/findings/operations scans, required top-level and finding-row fields, gate pass/fail for all four conditions (severity-threshold, new-findings, unreviewed-review-required, analyzer-errors), waived-all gate pass, reason_details structure, and T20/T30 summary fields
- `MGEF-T39-restore`
  - pending
  - recreate `shared/tests/test_aci_e2e_sample_packs.py` and rebuild `examples/aci-false-negative-challenge-pack/`, `examples/aci-precision-replay-pack/` based on current scanner signal definitions
  - false-negative-challenge-pack: fixtures that confirm CI-18, CI-20, CI-21, CI-25, CI-26 are reliably detected
  - precision-replay-pack: fixtures that should be clean against the same signals (false-positive prevention)
  - review each CI signal definition in `shared/python/aci_scan.py` before rebuilding
- remaining tasks
  - pending
