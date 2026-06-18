# ACI Maintainer Scan Mode Runbook

Status: Active

## Purpose

Pick the smallest scan surface that answers the maintainer question without
losing blocker accuracy.

## Mode Table

| Situation | Profile | Scope mode | Command |
|---|---|---|---|
| everyday runtime review | `full` | `source-only` | `aci scan --target . --profile full --scope-mode source-only` |
| ACI self-dogfood | `self-audit` | `self-audit` | `aci scan --target . --profile self-audit --scope-mode self-audit` |
| maintainer source + tests pass | `full` | `dogfood` | `aci scan --target . --profile full --scope-mode dogfood` |
| exhaustive repository audit | `full` | `full-repo` | `aci scan --target . --profile full --scope-mode full-repo --output workspace/full-repo-report.json` |
| targeted pre-build pass | `build-preflight` | usually `source-only` + `--include-path` | `aci scan --target . --profile build-preflight --scope-mode source-only --include-path shared/python` |
| targeted release review | `build-review` | usually `source-only` + `--include-path` | `aci scan --target . --profile build-review --scope-mode source-only --include-path shared/python` |

## Report Filters

Use report-view filters when the scan is intentionally exhaustive but the triage
question is narrower.

Examples:

```bash
aci emit-github-summary --report workspace/full-repo-report.json --report-scope-class runtime-source
aci emit-github-summary --report workspace/full-repo-report.json --report-scope-class tests
aci emit-github-summary --report workspace/full-repo-report.json --report-scope-class fixtures --report-owner-lane human-judgment
aci emit-sarif --report workspace/full-repo-report.json --report-owner-lane external-analyzer > workspace/full-repo-external.sarif
```

## Rules Of Thumb

- `source-only` is the default operational gate.
- `dogfood` is for maintainers who need source plus tests without fixture/docs noise.
- `self-audit` is the dedicated ACI product surface; use it for dogfooding.
- `full-repo` keeps non-runtime findings visible, but blocker decisions stay
  limited to `runtime-source`.
- `build-*` profiles should usually be paired with `--include-path` so the
  analyzer lane stays targeted and reproducible.
