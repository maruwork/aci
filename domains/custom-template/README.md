# ACI Custom Domain Template

Status: Active

## Purpose

Copy this shelf shape when a new domain-specific investigation area needs to be promoted out of one project-local override and into a reusable ACI domain pack.

## Expected Shape

```text
domains/<domain>/
  README.md
  python/
    <domain>_domain_rules.py
```

## Minimum Domain Rule Contents

- `DOMAIN_ID`
- `<DOMAIN>_DOMAIN_RULES`
- `STATE_PLANE_TERMS`
- `STATE_SQL_PATTERNS`
- `RISK_SURFACES`
- `AUTHORITY_TERMS`
- `SAFE_AUTHORITY_CONTEXT_TERMS`
- `SIDE_PROGRAM_TERMS`
- `EXCLUDED_FILES`
- `EXCLUDED_PREFIXES`

## Must Not Include

- project-local absolute paths
- runtime trigger schedules
- report output locations
- persistence backend implementation
