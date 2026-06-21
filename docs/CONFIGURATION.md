# ACI Configuration & Profiles

Reference for the config file, scan profiles, operations file, and the gate
controls. For a task-oriented walkthrough see `docs/QUICKSTART.md`.

## Config file (`aci.toml`)

Optional. Pass with `--config aci.toml`. All keys live under the `[aci]` table
and set defaults that CLI flags can still override. Inspect the live schema with
`aci show-config-schema`.

```toml
[aci]
output_format = "pretty-json"            # json | pretty-json
severity_threshold = "high"              # critical | high | medium | low
fail_on_new_findings = false             # fail when any new finding remains after baseline
fail_on_analyzer_errors = false          # fail when a configured external analyzer is missing/erroring
fail_on_unreviewed_review_required = false  # fail when a human-judgment finding is neither waived nor baselined
report_output = ""                       # fixed path to write the report to; empty = stdout. Overridden by --output
```

## Report destination

By default `aci scan` prints the report to **stdout**. To write it to a fixed
file instead, set `report_output` in config or pass `--output PATH` (the latter
wins). Parent directories are created; stdout then shows a one-line summary so
the JSON does not mix into logs.

```bash
aci scan --target . --output .aci/report.json     # write to a known location
# or, project-wide, set report_output = ".aci/report.json" in [aci]
```

## Profiles (`--profile`)

A profile selects which lanes and signals run. Lanes: native-static (N),
external-analyzer (E), human-judgment (H).

| Profile | Lanes | Use for |
|---|---|---|
| `startup` | N | fastest orientation pass on a fresh checkout |
| `quick-gate` | N + E | fast pre-commit / PR gate |
| `state-change` | N | mid-work change review |
| `wrap-up` | N + H | end-of-task review |
| `full` | N + E + H | complete scan (all detectors + applicable analyzers + human lane) |
| `self-audit` | N + E + H | dedicated ACI self-audit over runtime code, tests, maintainer probes, and roadmap evidence |
| `build-preflight` | N + E + H | before a build; runs the applicable analyzer set for the target |
| `build-review` | N + E + H | release review; runs the applicable analyzer set for the target, including pytest on Python sources |

External analyzers run only when installed, the lane is enabled, and the target
contains files/config they can actually inspect; add
`--no-external-analyzers` to force native-only. Check readiness with
`aci show-analyzer-availability` and the per-profile plan with
`aci show-profile-execution-plan`.

`show-analyzer-availability` includes:

- `default_policy` - whether the analyzer is a profile default or remains opt-in
- `execution_support_level` - whether ACI can run it or only report readiness
- `version_policy` / `install_spec` - pinned or minimum-version guidance
- `setup_hint` / `remediation_hint` - what to do when the analyzer is absent or downstream-wired

For the continuously verified Python analyzer set used in CI and maintainer flows:

```bash
python -m pip install -r requirements-dev-analyzers.txt
```

## Scope controls

```bash
--target <dir>            # directory to scan (required)
--include-path <rel>      # limit to a subpath; repeatable
--exclude-path <rel>      # exclude a subpath; repeatable
--diff-from <git-ref>     # only files changed since the ref (respects include/exclude)
--ignore-file <path>      # defaults to .aciignore under the target root when present
```

Generated paths (`.git`, `.venv`, `build`, `__pycache__`, `.claude`,
`workspace`, …) are always skipped.

`scan` also accepts `--scope-mode`:

- `source-only` - default CLI mode; excludes common non-runtime shelves such as `docs/`, `examples/`, `fixtures/`, `dist/`, and local scratch shelves
- `dogfood` - focuses on common source + test shelves for self-audit and maintainer verification
- `self-audit` - dedicated ACI self-audit scope for `shared/python/`, `shared/tests/`, `shared/tools/`, and `docs/roadmap/`
- `full-repo` - scans the full tree; fixture and documentation findings remain visible, but blocker/gate decisions are limited to `runtime-source` findings

## Gate controls

```bash
--severity-threshold critical        # lowest severity that blocks the gate
--fail-on-new-findings               # block when a new finding remains after baseline
--fail-on-unreviewed-review-required # block on un-waived human-judgment findings
--fail-on-analyzer-errors            # block when an external analyzer is missing/erroring
```

The `scan` command exits non-zero when the gate fails or any finding remains —
ready to use directly as a CI gate.

## Operations file (`--operations-file ops.toml`)

Accept, excuse, or drop findings without code changes. Entries can match by
`fingerprint` (stable) or by `ci_id` + `target_file` + `line`.

```toml
[baseline]
# accept current occurrences; only NEW findings fail the gate
entries = [
  { fingerprint = "CI-21|src/legacy/error_handler.py|1", ci_id = "CI-21", reason = "known legacy — scheduled refactor", first_seen = "2026-06-01" }
]

[suppression]
# drop matching findings from output entirely
entries = [
  { suppression_id = "SUP-001", match = "sample-text-only", reason = "non-live sample artifact", reviewer = "you" }
]

[waiver]
# explicitly excuse a specific finding (kept visible, not gating)
entries = [
  { waiver_id = "WAV-001", fingerprint = "CI-21|src/legacy/error_handler.py|1", owner = "you", reason = "accepted residual", review_condition = "recheck after refactor" }
]
```

See `aci.example-operations.toml` for a complete example.

## Ratchet gate (`--ratchet`)

Fail if any CI-ID's finding count increases versus the last passing run. On the
first run it writes a baseline state file (default `.aci-ratchet` under
`--target`; override with `--ratchet-file`). Use it to prevent regressions while
you pay down existing findings over time.

```bash
aci scan --target . --profile full --ratchet
```

## Reporting outputs

```bash
aci scan --target . --profile full --output-format json > report.json
aci scan --target . --profile full --scope-mode full-repo --report-scope-class runtime-source
aci emit-sarif --report report.json > aci.sarif    # SARIF 2.1.0 for code scanning
aci emit-annotations --report report.json          # GitHub Actions annotations
aci emit-github-summary --report report.json       # GitHub markdown summary
aci emit-baseline --report report.json --output ops.toml  # accept current findings as a baseline
aci validate-report --report report.json           # check against the report contract
```

Report-view filters are available on `scan`, `emit-sarif`, `emit-annotations`,
`emit-github-summary`, and `emit-baseline`:

```bash
--report-scope-class runtime-source
--report-scope-class tests
--report-owner-lane external-analyzer
```

These filters change the emitted report view, not the underlying source scan.
For `scan`, exit status still follows the unfiltered source gate.
