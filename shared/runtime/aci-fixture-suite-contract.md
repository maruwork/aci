# ACI Fixture Suite Contract

Status: Active

## Purpose

Define the bounded fixture suite for the common `ACI` shelf.

## Command

Use:

```bash
python shared/python/aci_cli.py fixture-check
```

## What It Locks

- smoke mode domain IDs
- expected smoke finding sample fields
- machine-readable sample report contract presence

## What It Does Not Lock

- downstream project behavior
- provider-specific CI behavior
- historical report state lifecycle

## Output

- compact JSON
- `ok` boolean
- per-check results
- sample report validation results
