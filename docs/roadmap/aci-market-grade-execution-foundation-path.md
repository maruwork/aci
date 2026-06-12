# ACI Market-Grade Execution Foundation Path

Status: Active

## Purpose

Define the execution order for turning `ACI` from a contract-heavy shelf into a market-grade-capable product core.

## Path

1. establish the scan entry surface
2. implement native finding generation
3. implement external analyzer invocation and normalization
4. define stable report emission and schema validation
5. implement baseline / suppression / waiver application
6. implement scope control and ignore behavior
7. implement quality gates and repeated-operation decisions
8. harden verification, tests, and CI
9. add ecosystem-facing outputs and integrations
10. expand to additional scan classes and runtime hardening

## Why This Order

- without a real scan entry surface, every later stream is speculative
- without native and external finding generation, report, baseline, and gate work remain artificial
- without stable report output, hosted integrations and repeated-operation state stay fragile
- without hardened tests and verification, market-grade claims remain untrustworthy

## Streams In Order

### 1. Scan Core

- scan command
- target selection
- scan session model
- exit status model

### 2. Detection Core

- native detector engine
- finding fingerprint design
- finding merge and dedup rules

### 3. Analyzer Runtime

- analyzer adapter interface
- analyzer process execution
- version / readiness validation
- timeout and failure model

### 4. Report Runtime

- full JSON report emission
- schema validation
- summary aggregation
- report versioning

### 5. Repeated-Operation Runtime

- baseline application
- suppression matching
- waiver visibility
- finding lifecycle updates

### 6. Scope Runtime

- include / exclude
- ignore file rules
- binary / large-file / generated-file handling
- symlink and path policy

### 7. Gate Runtime

- fail on severity threshold
- fail on new findings
- fail on unreviewed review-required findings
- machine-readable gate result

### 8. Verification Runtime

- contract tests
- detector fixtures
- analyzer adapter tests
- end-to-end regression checks

### 9. Integration Runtime

- SARIF output
- hosted upload path
- pull request annotation-compatible output

### 10. Expansion And Hardening

- secrets strategy
- dependency / supply-chain strategy
- IaC strategy
- container strategy
- performance and safety controls
