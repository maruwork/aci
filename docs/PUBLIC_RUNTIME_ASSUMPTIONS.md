# ACI Public Runtime Assumptions

Status: Active

## Purpose

State the minimum assumptions a first-time reader should know before trying the common ACI shelf.

## What Is Assumed

- Python is available in the local environment
- the reader can run a small Python CLI command
- the reader is evaluating the common shelf, not a downstream project runtime copy

## What Is Not Assumed

- no package install flow is required for the common-shelf smoke check
- no downstream `shared/tools/autonomous_code_inspection.py` runtime copy is required
- no project-local DB, trigger, or operator workflow is required

## Public Smoke-Check Boundary

The public smoke check proves only:

- domain-pack loading works
- normalized finding emission works
- report contract samples are readable

It does not prove:

- downstream runtime integration
- project-local trigger routing
- project-local persistence/writeback
- operator workflow ownership
