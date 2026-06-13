# ACI

**Purpose**: Common canonical shelf for a general-purpose code and file inspection tool.

Contains shared code, templates, and examples for ACI.
Does not hold the current state or operational results of any specific project.
Does not hardcode project-specific import layouts or side-program names in the common canonical shelf.

## What is this

- `ACI` is the common canonical shelf for a general-purpose code inspection tool
- core is domain-independent
- `Pier` and similar are added as optional domain packs
- project-local triggers and current state are held by the downstream integration

`ACI` provides a shared inspection catalog, normalized findings, optional domain packs, and a report contract.

## What this is not

- Not a `Pier`-only repository
- Not the project-local runtime gate itself
- Not the final owner of DB writeback or operator workflow

## Components

| Component | Role |
|---|---|
| `shared/core/` | generic inspection catalog and tool contract |
| `shared/python/` | loader, finding helper, signal/profile/wording helper |
| `domains/` | optional domain packs |
| `shared/runtime/` | quickstart and runtime binding guidance |
| `shared/report/` | report contract and public samples |

## 3-Minute Evaluation

For a first look on GitHub, start here:

1. `docs/USER_EVALUATION_INDEX.md`
2. `docs/ACI_SHELF_CLASSIFICATION.md`

Minimum smoke check:

```bash
python shared/python/aci_cli.py smoke
```

Public sample reports are in `shared/report/examples/`.
Triage guide is in `shared/report/README.md` and `shared/report/aci-generic-report-contract.md`.
Generic baseline/suppression/waiver contract is in `shared/core/aci-baseline-suppression-waiver-contract.md`.
Analyzer catalog bounded contract is in `shared/core/aci-analyzer-registry-contract.md`.
Profile catalog bounded contract is in `shared/core/aci-profile-execution-contract.md`.
Downstream adoption bounded contract is in `shared/core/aci-downstream-adoption-contract.md`.
Analyzer execution bounded contract is in `shared/core/aci-analyzer-execution-contract.md`.

## Setup

### 1. Try the common shelf first

```bash
python shared/python/aci_cli.py smoke
```

```bash
python shared/python/aci_cli.py show-analyzer-catalog
```

```bash
python shared/python/aci_cli.py show-profile-catalog
```

```bash
python shared/python/aci_cli.py show-analyzer-availability
python shared/python/aci_cli.py show-profile-execution-plan
```

```bash
python shared/python/aci_cli.py installed-package-check
```

This smoke check verifies only:

- `aci core only` (domain packs are optional — load with `--domain <id>`)
- normalized finding emission
- mirror sync helper

### 2. Next reading

- `docs/USER_EVALUATION_INDEX.md`
- `shared/runtime/aci-cli-and-config-contract.md`
- `shared/runtime/aci-ci-and-automation-contract.md`
- `shared/runtime/aci-fixture-suite-contract.md`
- `shared/runtime/aci-installed-package-verification-contract.md`
- `shared/core/aci-analyzer-registry-contract.md`
- `shared/core/aci-profile-execution-contract.md`
- `shared/core/aci-analyzer-execution-contract.md`

- `docs/ACI_DOWNSTREAM_ADOPTION_PACKET.md`

## Shelves

- `shared/python/`: shared code for generic signals, profiles, and wording; paths, side-program terms, and surfaces are placeholders to be substituted per project
  - domain pack selector helper: `shared/python/aci_domain_loader.py`
  - external analyzer catalog: `shared/python/aci_analyzers.py`
  - profile catalog: `shared/python/aci_profile_catalog.py`
- `shared/core/`: domain-independent core inspection catalog and contracts
- `domains/`: location for domain packs such as `Pier`
- `shared/runtime/`: responsible shelf for project-local runtime binding; also holds runtime/operator-facing boundary constants
- `shared/report/`: responsible shelf for owner-facing report contracts

## Public File Structure

The only surfaces a user needs to be aware of initially:

- `README.md`
- `shared/core/`
- `shared/python/`
- `shared/runtime/`
- `shared/report/`
- `domains/`

## Generic vs. Non-Generic Boundary

- generic `ACI` canonical shelf:
  - `shared/core/`
  - `shared/python/`
  - `shared/runtime/`
  - `shared/report/`
- non-generic:
  - `domains/<domain>/` (domain pack body and bridge documents)
- classification list:
  - `docs/ACI_SHELF_CLASSIFICATION.md`

## Optional Domain Packs

- `aci core only`
  - generic core only
- `aci + pier domain`
  - optional Pier investigation vocabulary and bridge docs
- future `aci + <domain>`
  - added in the same pack shape

Entry point for domain packs is `domains/README.md`.

## Standalone Repo View

- current physical home is this repository root
- public-facing commands and file paths in this shelf are written repo-relative
- keep `README.md`, `shared/`, and `domains/` at the repo root

## Packaging and Install Proof

Package metadata and packaged CLI entrypoint: `pyproject.toml`.
Installed-package proof surface: `shared/runtime/aci-installed-package-verification-contract.md`.
Editable install proof surface: `shared/runtime/aci-editable-install-proof-contract.md`.
Built wheel proof surface: `shared/runtime/aci-built-wheel-install-proof-contract.md`.
Source distribution proof surface: `shared/runtime/aci-source-distribution-proof-contract.md`.

## Usage

1. substitute placeholders in the generic code with project-specific paths, scopes, and surfaces to create a runtime copy
2. bring in templates from `shared/runtime/templates/` and `shared/report/templates/`
3. replace only the project-specific paths, scopes, surfaces, and result writeback targets
4. verify expected behavior against samples in `shared/report/examples/`

## Downstream Adoption

Carry/customize boundary for downstream maintainers: `docs/ACI_DOWNSTREAM_ADOPTION_PACKET.md`.

## Repository Community Files

- `SUPPORT.md`
- `.github/ISSUE_TEMPLATE/`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/CODEOWNERS`

## Rules for the Generic Shelf

- Do not assume specific project import paths
- Do not hardcode specific project or tool names in signal rules
- Do not place operational artifacts such as current registers, operator manuals, or validation results

## What Not to Write

- project-specific current registers
- project-specific operator manuals
- project-specific validation records

## Return Point

- To return to the entry point of this shelf: `README.md`
- When reading as a standalone repo, start from this `README.md`

## Pier Integration Documents

The following are not part of the generic `ACI` canonical shelf; they are `Pier`-specific bridge documents.

- `domains/pier/aci-pier-integration-spec.md`
- `domains/pier/aci-trigger-read-spec.md`
- `domains/pier/aci-trigger-routing-spec.md`
- `domains/pier/aci-pier-validation-decision-register.md`
