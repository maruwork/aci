# ACI Market-Grade Execution Foundation Design

Status: Active

## Purpose

Describe the execution-ready design needed before broad implementation begins.

## Design Rule

`ACI` should stop behaving like a contract demonstrator and start behaving like a bounded security scanning product core.

The design below defines the minimum runtime architecture required for that transition.

## 1. Scan Entry Design

### Commands

Add a real scan surface in addition to existing proof commands.

Required command family:

- `scan`
- `validate-report`
- `show-gate-result`

### Required Scan Inputs

- target root path
- profile
- optional domain pack
- optional config file
- optional operations file

### Exit Model

- `0`
  - no blocking findings
- `1`
  - findings or gate failure
- `2`
  - usage or config error
- `3`
  - runtime failure
- `4`
  - contract or schema failure

The exact numbers may be adjusted, but clean and findings must not collapse into the same success code.

## 2. Native Detector Design

### Detector Shape

Each native detector must define:

- detector id
- supported file kinds
- trigger condition
- finding mapping
- fingerprint ingredients
- false-positive guard rules

### Detector Runtime

The runtime must:

- walk target files
- skip unsupported or excluded files
- run detectors by file kind
- emit zero or more findings

### Fingerprint Rule

A finding fingerprint must be derived from stable semantic ingredients, not from volatile run metadata.

Minimum inputs:

- rule or detector id
- normalized path
- stable location anchor
- stable issue signature

## 3. External Analyzer Design

### Adapter Shape

Each analyzer adapter must define:

- analyzer id
- command build logic
- minimum version rule
- timeout behavior
- output parser
- finding normalization map

### Readiness Model

Readiness must distinguish:

- not installed
- installed but unsupported version
- installed and invokable
- installed but runtime-failing

### Failure Model

Analyzer failures must be reportable without silently turning into clean scans.

## 4. Report Design

### Required Outputs

- machine-readable JSON report
- summary block
- findings block
- blockers block
- residuals block
- gate result block

### Validation Rule

Validation must check:

- full top-level structure
- every finding row
- field types
- allowed values where enumerated
- summary consistency against findings

### Versioning Rule

The report must carry an explicit format version once real scans exist.

## 5. Repeated-Operation Design

### Operations File

Use one operations file surface for:

- baseline
- suppression
- waiver

### Application Order

1. raw findings generated
2. fingerprints assigned
3. suppressions applied
4. baseline status assigned
5. waiver status assigned
6. summary recalculated
7. gates evaluated

### Visibility Rule

- suppressed findings may be omitted from active findings
- waived findings remain visible
- existing baseline findings remain visible unless downstream mode says otherwise

## 6. Scope And Ignore Design

### Scope Inputs

- include paths
- exclude paths
- ignore file
- max file size
- binary file rule
- generated file rule
- symlink rule

### Default Behavior

The product must explicitly document its defaults instead of relying on incidental filesystem behavior.

## 7. Quality Gate Design

### Gate Inputs

- minimum severity threshold
- fail on any new finding
- fail on unreviewed review-required finding
- fail on analyzer runtime errors

### Gate Output

Emit:

- overall decision
- reasons
- blocking finding counts

## 8. Verification Design

### Test Layers

- unit tests for helpers and parsers
- detector fixture tests
- analyzer adapter tests
- end-to-end scan tests
- report schema tests
- gate behavior tests

### Fail-Close Rule

No verification surface may claim success through a summary field when any underlying required check fails.

## 9. Integration Design

### Hosted Output

`ACI` should emit at least one hosted-ingestion-ready format.

Primary target:

- SARIF

### Mapping Surface

Map:

- rule id
- finding message
- severity
- location
- fingerprint or dedup key

## 10. Expansion Design

These areas require product direction before implementation expands broadly:

- secrets scanning
- dependency and supply-chain analysis
- IaC scanning
- container scanning

For each one, `ACI` must choose whether it will:

- implement native detection
- wrap external analyzers
- or remain intentionally unsupported

## 11. Performance And Safety Design

### Required Controls

- analyzer timeout
- max file size
- binary skip
- deterministic traversal
- symlink handling policy
- subprocess failure isolation

### Security Rule

Scanning an untrusted repository must not implicitly claim that executing external analyzers is risk-free.

The product must document when a scan executes third-party tools and what trust boundary that implies.
