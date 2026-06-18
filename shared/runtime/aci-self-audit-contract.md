# ACI Self-Audit Contract

Status: Active

## Purpose

Define the dedicated self-audit product surface for `ACI` itself.

## Self-Audit Surface

Use:

```bash
python shared/python/aci_cli.py self-audit-check
```

Or scan directly with the dedicated profile:

```bash
python shared/python/aci_cli.py scan --target . --profile self-audit
```

## What This Contract Proves

- `ACI` has a first-class `self-audit` profile instead of relying on ad hoc combinations of `dogfood`, `.aciignore`, and repo conventions
- maintainer probe shelves such as `shared/tools/` are classified explicitly and are not conflated with `runtime-source`
- roadmap evidence shelves such as `docs/roadmap/` are classified explicitly and remain visible without entering the runtime gate
- repo-local ignore policy for no-touch shelves is explicitly verified

## What This Contract Does Not Prove

- that self-audit findings are zero
- that maintainer support shelves are runtime-gating code
- that downstream repositories must mirror ACI's exact self-audit shelf layout

## Reviewed Command Targets

- verification surface:
  - `python shared/python/aci_cli.py self-audit-check`
- scan surface:
  - `python shared/python/aci_cli.py scan --target . --profile self-audit`

