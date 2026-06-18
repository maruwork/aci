# ACI Quickstart

Scan a project, read the report, and gate CI — in a few commands.
ACI is Python-first (see the Language Support section in `README.md`).

## 1. Install

Standard install:

```bash
pip install ac-inspector
```

This installs the `aci` CLI.

Source install for local development:

```bash
git clone https://github.com/maruwork/aci.git
cd aci
pip install -e .
```

Verify the shelf and sample report contract:

```bash
aci automation-smoke
```

(`aci smoke` is a lightweight common-shelf check only; use `aci automation-smoke` to verify the installed package.)

If you want the same pinned Python analyzer set that CI uses:

```bash
python -m pip install -r requirements-dev-analyzers.txt
```

## 2. Scan your project

```bash
aci scan --target . --profile full --domain core-only --output-format pretty-json
```

- `--target` the directory to scan (read-only; ACI never writes into it).
- `--profile` how much runs. Common choices:
  - `quick-gate` — fast: native structure signals + lightweight Python external analyzers.
  - `full` — all native detectors + all applicable external analyzers + human-judgment lane.
- `--domain core-only` — generic core. Add an optional domain pack with
  `--domain <id> --domain-file <path>`.
- `--scope-mode source-only` - default preset; excludes common non-runtime shelves such as `docs/` and `examples/`.
- `--scope-mode dogfood` - focuses on common source + test shelves for self-audit.
- `--scope-mode self-audit` - dedicated ACI self-audit scope; includes runtime code, tests, maintainer probes, and `docs/roadmap/`.
- `--scope-mode full-repo` - scans the full tree but only `runtime-source` findings can block the gate.
- `--no-external-analyzers` - skip ruff/pyflakes/mypy/pytest/semgrep/eslint/tsc/shellcheck/sqlfluff (native lane only).

ACI itself should prefer:

```bash
aci self-audit-check
aci scan --target . --profile self-audit
aci scale-check --scratch-root workspace/scale-check
```

The exit code is non-zero when findings are present (including waived ones) or the
gate fails. If you want to rely only on the gate decision, check
`gate.decision` in the JSON output rather than the exit code.

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
- `scope_class` says where the finding lives: `runtime-source`, `tests`,
  `fixtures`, `docs-evidence`, `roadmap-evidence`, `maintainer-probes`,
  `support`, or `generated`.

The top-level `summary`, `gate`, and `blockers` fields give the roll-up and the
pass/fail decision.

Use report-view filters when the scan is intentionally exhaustive but the triage
question is narrower:

```bash
aci emit-github-summary --report report.json --report-scope-class runtime-source
aci emit-github-summary --report report.json --report-scope-class tests
aci emit-github-summary --report report.json --report-scope-class fixtures --report-owner-lane human-judgment
```

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
aci emit-github-summary --report report.json           # Markdown summary for PRs / step summary
aci emit-github-summary --report report.json --report-scope-class runtime-source
```

## Where next

- `docs/USER_EVALUATION_INDEX.md` — recommended reading order
- `README.md` — components, language support, profiles overview
- `shared/report/examples/` — full sample reports
- `shared/report/aci-generic-report-contract.md` — the report contract
- `docs/MAINTAINER_SCAN_MODE_RUNBOOK.md` — when to use each scan mode
- `docs/NON_RUNTIME_TRIAGE_WORKFLOW.md` — how to handle advisory-only findings
