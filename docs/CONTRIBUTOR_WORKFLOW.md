# ACI Contributor Workflow

Status: Active

## Purpose

Keep the common shelf green locally before CI by using the same bounded checks
that guard report, scan, and lint surfaces.

## Recommended Setup

Install the local hook set:

```bash
python -m pip install pre-commit
pre-commit install
```

The repository ships `.pre-commit-config.yaml` with two bounded hooks:

- `aci ruff`
- `aci core report surfaces`

Both hooks are workspace-safe: the pytest hook writes its scratch data under
`workspace/pre-commit-pytest`.

## Fast Local Checks

Run these before opening or updating a PR:

```bash
python -m ruff check shared/python shared/tests
python -m pytest shared/tests/test_aci_report_surface_contracts.py shared/tests/test_aci_report_view.py shared/tests/test_aci_runtime_scan.py --basetemp workspace/pytest-contributor
python shared/python/aci_cli.py automation-smoke
```

## Full Verification

When the change touches scan/runtime/report contracts more broadly, run:

```bash
python -m pytest --basetemp workspace/pytest-full
python shared/python/aci_cli.py self-audit-check
```

## Why These Checks

- `ruff` keeps the shared Python shelves clean between CI runs.
- the bounded pytest slice protects report projection, scope classification,
  gate behavior, and machine-readable contracts.
- `automation-smoke` confirms the packaged public surfaces still validate.
