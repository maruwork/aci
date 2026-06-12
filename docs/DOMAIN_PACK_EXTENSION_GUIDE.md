# ACI Domain Pack Extension Guide

Status: Active

## Purpose

Show a first-time reader how to add a new optional domain pack without mixing project-local runtime rules into core.

## When To Add A Domain Pack

Add a domain pack when:

- the investigation vocabulary is reusable beyond one runtime copy
- the terms do not belong in generic `ACI core`
- the rules are domain-specific, not project-path-specific

Do not add a domain pack when:

- the content is just one downstream project's trigger wiring
- the content is just one project's output path
- the content is a project-local operator rule

## Minimal Shape

```text
domains/<domain>/
  README.md
  python/
    <domain>_domain_rules.py
```

## Required Steps

1. copy the shape from `domains/custom-template/`
2. define one `<DOMAIN>_DOMAIN_RULES` object matching `shared/python/aci_domain_contract.py`
3. keep absolute paths, trigger schedules, and output locations out of the domain pack
4. place the rules file at `domains/<domain>/python/<domain>_domain_rules.py`; the loader discovers it automatically via this convention — no registration required
5. update shelf classification or README only if the new domain becomes a maintained public example

## Required Fields

- `domain_id`
- `state_plane_terms`
- `state_sql_patterns`
- `risk_surfaces`
- `authority_terms`
- `safe_authority_context_terms`
- `side_program_terms`
- `excluded_files`
- `excluded_prefixes`

## Must Not Cross The Boundary

- generic signal semantics stay in `shared/python/aci_signals.py`
- project-local trigger/runtime rules stay out of the domain pack
- reviewed persistence records stay outside core/domain semantics

## Minimal Verification

- `load_domain_rules('<domain>')` returns the expected `domain_id`
- the domain pack imports from the common shelf path
- no project-local absolute path is committed into the pack
