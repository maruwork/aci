# ACI CLI And Config Contract

Status: Active

## Purpose

Define the bounded common-shelf CLI and config surface for `ACI`.

## CLI Entry

Use:

```bash
python shared/python/aci_cli.py <command>
```

## Supported Commands

- `smoke`
  - runs the bounded common-shelf smoke check
- `automation-smoke`
  - runs the bounded automation-facing verification surface
- `fixture-check`
  - runs the bounded common-shelf fixture suite and emits compact JSON
- `installed-package-check`
  - runs the bounded installed-package verification surface and emits compact JSON
- `self-audit-check`
  - runs the dedicated self-audit verification surface and emits compact JSON
- `show-config-schema`
  - prints the supported config schema
- `show-analyzer-catalog`
  - prints the bounded external-analyzer catalog known to the common shelf
- `show-profile-catalog`
  - prints the bounded profile execution catalog known to the common shelf
- `show-analyzer-availability`
  - prints bounded analyzer availability checks from the current shell, including setup and version-policy hints
- `show-profile-execution-plan`
  - prints the bounded analyzer execution plan for supported profiles, plus opt-in analyzers that stay outside the defaults
- `show-sample-report`
  - prints a built-in sample report
- `validate-report`
  - validates a machine-readable report JSON file against the bounded contract
  - requires `--report <path>`
- `emit-sarif`
  - converts an ACI machine-readable report JSON file into SARIF 2.1.0
  - requires `--report <path>`
- `validate-sarif`
  - validates a SARIF 2.1.0 JSON file against the bounded hosted-ingestion-ready contract
  - requires `--report <path>`
- `scan`
  - runs a bounded real-target scan against a directory
  - requires `--target <path>`
  - options: `--operations-file`, `--include-path`, `--exclude-path`, `--ignore-file`, `--severity-threshold`, `--fail-on-new-findings`, `--no-external-analyzers`, `--fail-on-analyzer-errors`, `--profile`, `--domain`, `--domain-file`, `--output-format`

## Config File

- format: `TOML`
- example: `aci.example.toml`
- top-level table: `[aci]`

## Supported Config Fields

- `output_format`
  - allowed: `json`, `pretty-json`
  - default: `pretty-json`
- `severity_threshold`
  - allowed: `low`, `medium`, `high`, `critical`
  - default: `high`
  - purpose: lowest severity that should block the gate when not waived
- `fail_on_new_findings`
  - allowed: `true`, `false`
  - default: `false`
  - purpose: fail the gate when any new finding remains after baseline handling
- `fail_on_analyzer_errors`
  - allowed: `true`, `false`
  - default: `false`
  - purpose: fail the gate when configured analyzers are missing or runtime-failing

## Exit Codes

- `0`
  - command completed successfully
- `1`
  - scan findings present or gate failure (`scan` command only)
- `2`
  - usage or config error
- `3`
  - runtime failure while running the bounded common-shelf command
- `4`
  - internal contract error such as an invalid generic mode or contract mismatch
- `5`
  - automation verification failure

## Boundary

This CLI does not own:

- downstream project runtime wiring
- analyzer installation or provider-specific orchestration
- baseline, suppression, or waiver persistence
