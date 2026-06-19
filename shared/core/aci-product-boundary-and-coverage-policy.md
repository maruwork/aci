# ACI Product Boundary And Coverage Policy

Status: Active

## Purpose

Fix what the common `ACI` shelf is allowed to claim as its completed product
surface, and what remains explicitly delegated, human-judgment-only, or
downstream-defined.

Execution-order and closure policy for repo-local completion work lives in
`docs/roadmap/ACI_COMPLETION_POLICY.md`.

## Canonical Completion Stance

`ACI` is a **Python-first code audit tool with polyglot text-scan and
external-analyzer evidence lanes**.

The common shelf may claim:

- bounded native structural/code-smell coverage (with documented blind spots) only for Python
- language-agnostic text-scan coverage where the detector is text-based
- bounded external-analyzer integration when the listed analyzer is execution-ready
- optional domain-pack extension without changing core authority

The common shelf must not claim:

- language-general native structural coverage across all source languages
- that cataloged opt-in analyzers are runnable everywhere
- that human-judgment CI IDs are automatically decided
- that `core-only` mode completes domain-specific CI-19 review

## 1. Language Boundary

The completed common-shelf product claim is:

- native structural analysis: Python only
- text-scan coverage: supported text/code files listed in `README.md` and `docs/CI_REFERENCE.md`
- polyglot evidence beyond that: only through applicable external analyzers

Therefore:

- a Python repository can use the full common-shelf native lane
- a non-Python repository may still use text scans and external analyzers
- a non-Python repository must not be told it receives the same native audit depth as Python

## 2. Human-Judgment CI IDs

`CI-08`, `CI-11`, and `CI-24` remain **human-judgment-only** in the common
shelf.

This is an intentional product boundary, not a temporary omission claim. The
common shelf may surface these IDs in the catalog and report vocabulary, but it
does not claim generic high-precision automation for them.

Future automation is allowed only if all of the following become true:

- the narrower sub-problem is explicitly specified
- a low-false-positive static rule exists
- fixtures and precision evidence prove it
- the common shelf can explain the remaining blind spots honestly

Until then, completed `ACI` means these IDs stay review-only.

## 3. Security / Dependency / IaC / Container Boundary

The completed common-shelf security posture is a **bounded executable baseline**:

- native CI-14 checks for dynamic code execution, `subprocess(..., shell=True)`,
  plaintext secrets, insecure HTTP, unsafe deserialization, unsafe YAML load,
  and narrow supply-chain drift patterns
- execution-ready Semgrep baseline integration
- opt-in analyzer catalog entries for deeper security tooling whose repo-local
  wiring remains downstream

This means:

- `semgrep`, `osv-scanner`, and `trivy` are part of the common executable
  product surface (execution-ready adapters that normalize their output into
  CI-14 findings when the tool is installed)
- `codeql` and `gitleaks` are product-visible catalog surfaces, but not part of
  the completed common executable baseline: their execution models (CodeQL needs
  a prebuilt database; gitleaks writes a file report rather than JSON-on-stdout)
  do not fit the bounded single-invocation contract, so they stay opt-in until
  the shelf gains adapters for those models

## 4. Domain-Pack Completion Rule For CI-19

`CI-19` is domain-aware. Completion depends on whether a domain pack exists.

### `core-only`

In `core-only` mode, the common shelf may claim:

- the CI-19 catalog entry exists
- the execution model knows CI-19 is domain-aware

In `core-only` mode, the common shelf must not claim:

- that CI-19 is substantively covered for a downstream repository

### `aci + <domain>`

CI-19 can be called complete for a downstream domain only when that domain pack
provides at minimum:

- explicit `side_program_terms`
- explicit `authority_terms`
- tests or fixtures proving the intended match boundary
- examples or docs showing what counts as a valid signal in that domain

Without those, CI-19 remains an incomplete downstream extension, not a core
defect in generic `ACI`.

## 5. CI-14 Supply-Chain Coverage Boundary

The current common-shelf supply-chain detector intentionally has a narrow,
explicit manifest set:

- `requirements*.txt`
- `pyproject.toml` dependency surfaces
- `package.json`
- `Dockerfile` / `Containerfile`
- GitHub workflow `uses:` refs

The common shelf must state this limitation directly whenever it describes CI-14
supply-chain coverage. It must not imply general lockfile/manifests coverage for
surfaces such as:

- `poetry.lock`
- `package-lock.json`
- `pnpm-lock.yaml`
- `Cargo.lock`
- `go.mod`

Completed `ACI` under the current boundary means this narrow scope is
documented honestly. Broader manifest support is an allowed future extension,
not part of the current completion claim.

## Reading Rule

Use this policy together with:

1. `README.md`
2. `shared/core/aci-autonomous-code-inspection-tool-contract.md`
3. `shared/core/aci-code-inspection-execution-spec.md`
4. `docs/CI_REFERENCE.md`
5. `shared/core/aci-downstream-adoption-contract.md`
