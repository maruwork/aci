# ACI Product Boundary And Coverage Policy

Status: Active

## Purpose

Fix what the common `ACI` shelf is allowed to claim as its completed product
surface, and what remains explicitly delegated, human-judgment-only, or
downstream-defined.

Execution-order and closure policy for repo-local completion work lives in
`docs/roadmap/ACI_COMPLETION_POLICY.md`.

## Canonical Completion Stance

`ACI` is a **complete general-purpose code audit tool on the orchestration
model**: a Python-native structural core plus a fully live-verified
multi-language orchestration of best-in-class analyzers (all 13 cataloged lanes
execution-ready and CI-proven to run), with polyglot text-scan evidence lanes.

"Complete general-purpose" here is the *orchestration* definition, the only
realistic path: multi-language depth — including source→sink taint — is borrowed
from orchestrated analyzers, not re-implemented natively per language (an
explicit non-goal). Native structural and intra-procedural taint depth stays
Python-only. The closure evidence for this stance lives in
`docs/ACI_GENERAL_PURPOSE_COMPLETION_PLAN.md` (gates G1–G4).

**What "complete" means — and what it does not.** Completion is defined by
*balanced orchestration*, not by building features in-house. Completion is an
*equilibrium*, not a finish line of coverage. ACI is complete when it holds these
four — each verbalizable — in balance:

1. **Own only what is genuinely ACI's** — the CI-ID taxonomy, finding
   normalization, the analyzer adapters, the Python-native detectors, and a
   closed convenience baseline. Everything generic and multi-language is
   **borrowed** from best-in-class analyzers, never re-implemented.
2. **Borrow, but actually deliver** — a borrowed lane counts only when it is
   wired, live-verified, and normalized into a CI-ID. Orchestration that is
   claimed but not proven to run is under-built.
3. **Claim only what is proven; bound the rest** — coverage that is not
   live-CI-proven is not claimed; residual limits are documented honestly
   (`aci_known_limits.py`), not hidden.
4. **Convenience without unbounded growth** — a small closed baseline for
   out-of-box use; deeper or wider coverage is opt-in and borrowed, never grown
   into ACI's bundle.

Because completion is an equilibrium, "add another analyzer / language / rule" is
**not** automatically "more complete". Past the balance point, adding native or
bundled coverage is over-building — it moves ACI *away* from completion. Coverage
breadth is the analyzers' axis to grow; ACI's axis is the **quality and honesty
of the orchestration**.

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

- `semgrep`, `osv-scanner`, `trivy`, and `gitleaks` are part of the common
  executable product surface (execution-ready adapters that normalize their
  output into CI-14 findings when the tool is installed). gitleaks runs via a
  bounded temp-report-file invocation; the others are JSON-on-stdout. `semgrep`
  also carries a **closed** bundled taint-mode baseline (JavaScript + Python), so
  the default lane proves source→sink taint out of the box, not only bare
  patterns. That baseline is precision-gated by `shared/tools/aci_taint_eval.py`
  (perfect recall and zero false positives on a curated source→sink + control
  corpus). It is **not** grown language-by-language — see "Taint: what ACI
  authors vs borrows" below. Real-world precision on unlabelled code still needs
  human adjudication; the gate proves discrimination on a controlled set, not a
  field false-positive rate.
- `codeql` is **also execution-ready**: the shelf has a database-build → analyze
  → SARIF → normalized-CI-14 adapter (per-language DB create, then the
  security-and-quality suite). It stays **default-opt-in** because the
  per-language database build is heavy (a multi-step, slow invocation), not
  because the adapter is missing. All 13 cataloged analyzers are now
  execution-ready; none remain availability-only.

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

## 6. Taint: What ACI Authors vs Borrows

This section draws an explicit, verbalizable line so "strengthening" is never
confused with "complexification". The boundary is stated as DO / DON'T, and the
bundled ruleset is cut exactly there.

**ACI authors (and maintains):**

- the Python-native intra-procedural taint detector (`CI14_TAINTED_FLOW`) — the
  native core
- the analyzer adapters, the SARIF/JSON normalization, and the CI-ID taxonomy
- rules that encode ACI's **own catalog concepts** that the ecosystem does not
  express (e.g. CI-21 silent-shell-continue, CI-22 fire-and-forget, CI-26
  world-writable) — the engine is borrowed, the taxonomy is ACI's
- a single **closed** taint baseline: JavaScript + Python source→sink, kept small
  and precision-gated, so the default lane is useful out of the box

**ACI does not author (it borrows):**

- generic, multi-language taint coverage — that is what `codeql` query suites and
  the `semgrep` registry already own and maintain; ACI orchestrates those rather
  than re-implementing them
- additional bundled taint rules added **language-by-language as a coverage
  project** (no Go/Java/Rust/… taint rules grown into the bundle to chase
  breadth). Multi-language depth is reached by pointing at the analyzers' own
  rulesets, not by enlarging ACI's

**The one-line rule:** ACI authors rules only for its own catalog concepts and a
closed convenience baseline. Coverage growth is the analyzer's job, delivered by
**orchestrating** maintained rulesets — never by expanding ACI's bundle. A change
that adds a language or a generic security rule to the bundle to "cover more" is
complexification, not strengthening, and is out of scope by this policy.

## Reading Rule

Use this policy together with:

1. `README.md`
2. `shared/core/aci-autonomous-code-inspection-tool-contract.md`
3. `shared/core/aci-code-inspection-execution-spec.md`
4. `docs/CI_REFERENCE.md`
5. `shared/core/aci-downstream-adoption-contract.md`
