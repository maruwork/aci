# ACI Quickstart

Scan a Python project, read the report, and gate CI — in a few commands.
ACI is Python-first (see the Language Support section in `README.md`).

## 1. Install

```bash
pip install aci
```

This installs the `aci` CLI. Verify:

```bash
aci smoke
```

## 2. Scan your project

```bash
aci scan --target . --profile full --domain core-only --output-format pretty-json
```

- `--target` the directory to scan (read-only; ACI never writes into it).
- `--profile` how much runs. Common choices:
  - `quick-gate` — fast: native structure signals + lightweight external analyzers.
  - `full` — all native detectors + external analyzers + human-judgment lane.
- `--domain core-only` — generic core. Add an optional domain pack with
  `--domain <id> --domain-file <path>`.
- `--no-external-analyzers` — skip ruff/pyflakes/mypy/pytest (native lane only).

The exit code is non-zero when findings are present or the gate fails, so the
command is CI-ready as-is.

## 3. Read the report

Each finding is normalized with a stable shape, e.g.:

```json
{
  "ci_id": "CI-21",
  "signal": "CI21_BROAD_EXCEPTION_SWALLOW",
  "severity": "high",
  "confidence": "medium",
  "target_file": "app/io.py",
  "line": 42,
  "owner_lane": "native-static",
  "recommended_action": "Narrow the exception type or add explicit failure routing..."
}
```

- `severity` (critical/high/medium/low) drives the gate; `confidence`
  (high/medium/low) tells you how much to trust the signal before acting.
- `owner_lane` says who decides: `native-static`, `external-analyzer`, or
  `human-judgment`.

The top-level `summary`, `gate`, and `blockers` fields give the roll-up and the
pass/fail decision.

## 4. Scan only what changed (fast CI)

```bash
aci scan --target . --profile full --diff-from origin/main
```

`--diff-from <ref>` limits the scan to files changed since a git ref (it still
respects include/exclude scope). Ideal for pull-request gates.

## 5. Tune the gate

```bash
# only block on critical findings
aci scan --target . --profile full --severity-threshold critical

# block when any new finding appears vs the baseline
aci scan --target . --profile full --fail-on-new-findings
```

## 6. Accept or defer findings (operations file)

Create an operations TOML and pass `--operations-file ops.toml` to baseline,
suppress, or waive findings without editing code:

```toml
[baseline]
entries = [{ ci_id = "CI-03", target_file = "legacy/util.py", line = 12 }]

[waiver]
entries = [{ waiver_id = "W1", ci_id = "CI-21", target_file = "app/io.py", line = 42 }]
```

## 7. Hosted CI integration

```bash
aci scan --target . --profile full --output-format json > report.json
aci emit-sarif --report report.json > aci.sarif        # upload to code scanning
aci emit-annotations --report report.json              # GitHub Actions annotations
```

## Where next

- `docs/USER_EVALUATION_INDEX.md` — recommended reading order
- `README.md` — components, language support, profiles overview
- `shared/report/examples/` — full sample reports
- `shared/report/aci-generic-report-contract.md` — the report contract
