# AI Agent Runtime Token Optimization

## Purpose

Reduce token waste during ACI contract reading, smoke verification, and packaging checks without weakening canonical authority.

## Adopt Now

- RTK for repetitive CLI and smoke-check output
- thin entrypoint reading from `AGENTS.md` / `CLAUDE.md`
- bounded reads in `docs/governance/`, `shared/python/`, `shared/runtime/`, and the exact contract shelf under change
- compact / plan discipline for long release or packaging sessions
- avoid loading `archive/`, `.pytest_cache/`, `build/`, or `aci.egg-info/` unless the task explicitly targets residue handling

## Deferred

- distill
- local RAG
- proxy / budget-kill layers
- heavier context-mode automation

## Scale Profile

ACI should currently use the medium-scale profile.

## Operator Rules

1. Read the smallest authority route first.
2. Prefer targeted reads of `shared/python/`, `shared/runtime/`, `shared/core/`, or the exact root contract file under change.
3. Do not load generated residue or historical shelves by default.
4. Use RTK-filtered command execution for repetitive validation output.
5. Compression helpers do not decide tool truth, package truth, or publication truth.
