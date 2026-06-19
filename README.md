# ACI

**Auto Code Inspector.**

ACI (Auto Code Inspector) is a Python-first code audit and structure inspection tool.
Install from PyPI with `pip install ac-inspector`; run scans with the `aci` CLI.

```bash
pip install ac-inspector
aci scan --target .
```

## What is this

ACI is a Python code inspection tool focused on cross-file structure:

- **Native static detectors** — 17 detectors covering god classes, spaghetti code, duplicate code, scattered constants, interface drift, resource leaks, exception swallowing, and more (full list in `docs/CI_REFERENCE.md`)
- **External analyzer lane** — integrates ruff, pyflakes, mypy, pytest, semgrep, eslint, tsc, shellcheck, and sqlfluff when installed and applicable
- **Cataloged opt-in security analyzers** — tracks `codeql`, `gitleaks`, `osv-scanner`, and `trivy` as availability-only lanes until a consuming repository wires them locally
- **Optional domain packs** — add project-specific vocabulary and exclusion rules without touching core

`ACI` provides a normalized finding format, configurable severity gate, suppression/baseline/waiver contract, SARIF and annotation output, and a machine-readable report schema.

Exhaustive scans can now be projected into first-class report views by
`scope_class` and `owner_lane`, so runtime, tests, fixtures, docs, and support
shelves can be triaged without post-processing.

The common shelf now also ships a bounded `scale-check` surface plus continuous
CI verification on Linux, Windows, and macOS.

Product-boundary claim for this common shelf: `ACI` is a **Python-first**
native audit tool with polyglot text-scan and external-analyzer evidence lanes,
not a language-general native structural auditor. See
`shared/core/aci-product-boundary-and-coverage-policy.md`.

The `scan` CLI supports four scope presets:

- `source-only` - default; excludes common non-runtime shelves such as `docs/`, `examples/`, `fixtures/`, and scratch/output shelves
- `dogfood` - focuses on common source + test shelves for self-audit
- `self-audit` - dedicated ACI self-audit surface for runtime code, tests, maintainer probes, and roadmap evidence
- `full-repo` - scans the full tree, but blocker decisions stay limited to `runtime-source` findings

## What this is not

- Not a single-project-only repository
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

## Language Support

ACI is **Python-first**. Be aware of the scope before adopting:

| Lane | Languages | Notes |
|---|---|---|
| Native static detectors | **Python** | All 17 native CI-ID detectors parse Python (AST). This is the only language with full native coverage. |
| Language-agnostic text scans | supported text/code files | A few detectors are text-based rather than Python-AST-based: plaintext-secret and insecure-HTTP (CI-14), and TODO/FIXME/HACK markers (CI-03). Supported suffixes include `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.rs`, `.java`, `.cs`, `.kt`, `.kts`, `.sh`, `.bash`, `.sql`, `.tf`, `.hcl`, `.md`, `.txt`, `.toml`, `.yml`, `.yaml`, and `.json`, plus `Dockerfile` / `Containerfile`. |
| External analyzers (opt-in) | Python, JS/TS, Shell, SQL, polyglot source | ruff / pyflakes / mypy / pytest (Python); semgrep (bundled baseline polyglot rules); eslint, tsc (JS/TS); shellcheck (Shell); sqlfluff (SQL). `full`, `build-preflight`, and `build-review` automatically run the analyzers that match files/config found in the target; `quick-gate` keeps the lighter Python pair (`ruff`, `pyflakes`). TypeScript type checking via `tsc` requires a `tsconfig.json` in the target root. |

Non-Python codebases do not get the Python-native structure detectors. They can
still use the supported text scans plus any applicable external analyzers.

## Product Boundary

The completed common-shelf product claim is intentionally bounded:

- Python gets the full native structural lane
- non-Python files get text scans plus applicable external analyzers
- `CI-08`, `CI-11`, and `CI-24` remain human-judgment-only
- deep security analyzers such as `codeql`, `gitleaks`, `osv-scanner`, and `trivy` stay opt-in/cataloged until the common shelf owns execution-ready adapters
- `CI-19` is only substantively complete when a downstream domain pack provides its vocabulary and tests
- CI-14 supply-chain drift currently covers `requirements*.txt`, `pyproject.toml` dependency surfaces, `package.json`, `Dockerfile` / `Containerfile`, and GitHub workflow `uses:` refs

This boundary is defined canonically in `shared/core/aci-product-boundary-and-coverage-policy.md`.

## Relationship to ruff and other single-file linters

ACI **complements** a fast single-file linter like ruff; it is not a replacement.

- **ACI's unique value is cross-file and structural analysis a single-file
  linter cannot do:** duplicate / near-duplicate code across files (CI-05),
  low-cohesion god classes via LCOM (CI-04), constants/numbers scattered across
  files (CI-20, CI-06), interface/contract drift (CI-23), and the
  dataflow/cross-file parts of CI-14/CI-22/CI-25.
- **For single-file lint signals, prefer ruff** — it already covers broad-except
  (CI-21 ≈ ruff BLE), TODO markers (CI-03 ≈ TD/FIX), too-many-arguments
  (CI-18 ≈ PLR0913), `global` mutation (CI-26 ≈ PLW0603), and most complexity
  (CI-02 ≈ C901). When ACI's external lane runs ruff, ACI automatically drops the
  duplicate native finding so you are not double-reported.

Recommended setup: run ruff for fast single-file lint, and ACI for the cross-file
/ structural layer on top.

## 3-Minute Evaluation

To scan a project right away, follow `docs/QUICKSTART.md`.

For a first look on GitHub, start here:

1. `docs/QUICKSTART.md`
2. `docs/CI_REFERENCE.md`
3. `shared/core/aci-product-boundary-and-coverage-policy.md`
4. `docs/USER_EVALUATION_INDEX.md`
5. `docs/ACI_SHELF_CLASSIFICATION.md`

Minimum smoke check:

```bash
python shared/python/aci_cli.py smoke
```

Public sample reports are in `shared/report/examples/`.
Triage guide is in `shared/report/README.md` and `shared/report/aci-generic-report-contract.md`.
Maintainer mode selection is in `docs/MAINTAINER_SCAN_MODE_RUNBOOK.md`.
Advisory-only non-runtime triage flow is in `docs/NON_RUNTIME_TRIAGE_WORKFLOW.md`.
Contributor hook and verification workflow is in `docs/CONTRIBUTOR_WORKFLOW.md`.
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

Maintainers who want the continuously verified Python analyzer set should install:

```bash
python -m pip install -r requirements-dev-analyzers.txt
```

```bash
python shared/python/aci_cli.py emit-github-summary --report report.json
```

```bash
python shared/python/aci_cli.py installed-package-check
```

```bash
python shared/python/aci_cli.py self-audit-check
```

This smoke check verifies only:

- `aci core only` (domain packs are optional — load with `--domain <id>`)
- normalized finding emission

For full install verification (automation-smoke, fixture-check, installed-package-check), see `shared/runtime/aci-ci-and-automation-contract.md`.
For the dedicated ACI self-audit surface, see `shared/runtime/aci-self-audit-contract.md`.
For scale budgets and multi-OS verification, see `shared/runtime/aci-scale-and-platform-contract.md`.
For human-labeled precision review preparation, see `docs/PRECISION_REVIEW_WORKFLOW.md`.

### 2. Next reading

- `docs/CONFIGURATION.md`
- `docs/PRECISION_REVIEW_WORKFLOW.md`
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
- `domains/`: location for optional domain packs
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
- `aci + <domain>`
  - optional domain-specific vocabulary and bridge docs; added in the same pack shape

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

## Domain Pack Bridge Documents

Bridge documents under `domains/<domain>/` are not part of the generic `ACI` canonical shelf.
They contain domain-specific vocabulary and integration rules and are maintained by the domain pack owner.
See `domains/README.md` for the list of available domain packs.
