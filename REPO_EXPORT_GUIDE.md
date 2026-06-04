# ACI Repo Export Guide

Status: Active

## Purpose

Describe how to read and extract `ACI` as a standalone repository even while it physically lives under `common/aci/` in the current monorepo.

## Reading Rule

- public-facing commands in this shelf are repo-relative
- public-facing file paths in this shelf are repo-relative
- monorepo-specific host paths must not be required to understand the tool

## Expected Standalone Root

```text
./
├── README.md
├── ACI_SHELF_CLASSIFICATION.md
├── REPO_EXPORT_GUIDE.md
├── PUBLIC_RUNTIME_ASSUMPTIONS.md
├── NON_GOALS.md
├── DOMAIN_PACK_EXTENSION_GUIDE.md
├── PUBLIC_RELEASE_CHECKLIST.md
├── PRIVATE_HOST_BOOTSTRAP_RUNBOOK.md
├── PRIVATE_RELEASE_HOLD_LINE.md
├── core/
├── python/
├── domains/
├── runtime/
├── report/
├── persistence/
├── integrations/
├── roadmap/
├── tasks/
└── design/
```

## Must Stay Repo-Relative

- smoke commands
- quickstart file paths
- public sample report references
- shelf classification examples

## May Stay Monorepo-Aware

- internal governance notes about `common/refernce`
- bounded sync helpers that intentionally validate the current monorepo mirror workflow

## Export Blockers

- legal files such as license selection
- hosting/org decisions outside this shelf
- private repository setup actions in the chosen repository host
