# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

### Changed

### Fixed

---

## [0.1.3] - 2026-06-18

### Fixed
- point self-audit verification at a tracked `docs/roadmap/` file so CI does not depend on a locally ignored roadmap inventory artifact

---

## [0.1.2] - 2026-06-18

### Fixed
- add explicit `shared` and `shared.tests` package markers so CI can import `shared.tests._aci_test_helpers` reliably during pytest collection on GitHub runners

---

## [0.1.1] - 2026-06-18

### Added
- `aci_report_view.py`, `aci_self_audit_verification.py`, and `aci_scale_verification.py` as stable operator-facing surfaces for triage, self-audit, and scale/platform verification
- owner-gated release evidence capture via `shared/tools/aci_capture_owner_release_state.py`
- public-repo-ready SARIF upload workflow in `.github/workflows/code-scanning.yml`

### Changed
- PyPI distribution name to `ac-inspector` while keeping the end-user CLI command `aci`
- release/distribution verification to normalize artifact prefixes from PyPI distribution names
- self-audit scope contracts, analyzer catalog surfacing, and detector/report boundaries for stricter code-audit use

### Fixed
- mypy type gaps in review-brief/report-view projection logic
- workspace-safe distribution verification and release readiness evidence flow

---

## [0.1.0] - 2026-06-17

### Added
- `aci_annotations.py`: GitHub Actions workflow command annotation emitter (`emit-annotations` CLI command)
- `--version` flag for `aci` CLI (emits `ACI_TOOL_VERSION` from `aci_scan.py`)
- Protocol types `PerFileDetector` and `CrossFileDetector` (PEP 544) in `aci_scan.py`
- `ACI_TOOL_VERSION = "0.1.0"` named constant in `aci_scan.py`
- `resolved_baseline_entries` and `resolved_baseline_count` fields in report schema and sample reports
- `MAX_SCAN_FILE_COUNT = 10_000` guard in `aci_scan.py`
- Extended `DEFAULT_GENERATED_PATH_SEGMENTS` for generated-file detection
- CI workflow (`.github/workflows/ci.yml`): test matrix, lint, type-check, ACI self-scan, release gate
- Release gate lane in `aci_installed_package_verification.py`: version consistency check and sample report schema validation
- Test coverage for CI-06 (Literal Rot), CI-09 (Test Rot ruff PT codes), CI-13 (Dependency Rot ruff I codes)
- GitHub optimization baseline files for repository health, contribution guidance, and security reporting
- Domain pack template in `domains/custom-template/` for creating new domain packs

### Changed
- `ANALYZER_MAX_OUTPUT_BYTES` renamed to `ANALYZER_MAX_OUTPUT_CHARS` (subprocess returns `str` not `bytes` when `text=True`)
- `aci_working_mirror_sync.py` reduced from ~970 lines to 70 lines: host-project-specific `REQUIRED_MIRROR_PAIRS` removed; pairs are managed by the downstream host project
- repository community guidance now uses the promoted `SECURITY.md` and `CONTRIBUTING.md` surfaces instead of draft-only wording

### Fixed
- Dead branch removed from `_version_probe_command` in `aci_analyzer_execution.py` (both branches returned the same value)
- Unused `subprocess` import removed from CI provenance step in `ci.yml`
- `result["errors"]` replaced with `result` in three report schema test assertions in `test_aci_report_and_gate_regression.py`; the `"errors"` key does not exist in `validate_report_payload` return value

### Removed
- Dead proof helper files archived to `archive/python-proof-helpers/`: `aci_built_wheel_install_proof.py`, `aci_editable_install_proof.py`, `aci_source_distribution_proof.py`
