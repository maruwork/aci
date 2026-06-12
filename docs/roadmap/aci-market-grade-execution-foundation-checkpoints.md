# ACI Market-Grade Execution Foundation Checkpoints

Status: Active

## CP1 Scan Entry Exists

Pass when:

- `ACI` accepts a real target path or repository root
- the command returns distinct exit states for clean, findings, config failure, and runtime failure

## CP2 Native Detection Exists

Pass when:

- at least one real detector walks target files and emits findings from actual content
- finding fingerprints are stable across reruns on unchanged input

## CP3 External Analyzer Runtime Exists

Pass when:

- configured analyzers can be executed, timed out, and normalized into `ACI` findings
- analyzer readiness checks mean more than executable visibility

## CP4 Report Runtime Is Stable

Pass when:

- a real scan emits the machine-readable report contract
- report validation checks all required structures, not only field presence

## CP5 Repeated-Operation State Exists

Pass when:

- baseline, suppression, and waiver data affect scan output
- new versus old findings are visible in both finding rows and summary counts

## CP6 Scope And Ignore Rules Exist

Pass when:

- include and exclude behavior is configurable
- ignored paths and unsupported files are handled explicitly and predictably

## CP7 Gate Behavior Exists

Pass when:

- gate decisions can fail on severity or new findings
- repeated runs produce stable machine-readable gate outcomes

## CP8 Verification Is Fail-Close

Pass when:

- smoke, fixture, package, and report validation surfaces fail correctly on real breakage
- no status field claims success while underlying checks fail

## CP9 Integration Output Exists

Pass when:

- `ACI` can emit SARIF or an equivalent hosted-ingestion-ready format
- the output is valid against the intended hosted ingestion rules

## CP10 Expansion Strategy Is Fixed

Pass when:

- the product direction for secrets, dependency, IaC, and container scanning is explicit
- unsupported classes are named rather than left ambiguous
