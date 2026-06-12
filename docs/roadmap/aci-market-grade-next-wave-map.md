# ACI Market-Grade Next-Wave Map

Status: Active

## Purpose

Convert the market-grade gap classification into concrete next waves.

## Next Waves

## 1. ACI Market-Grade Execution Foundation

- target:
  - turn every known market-grade gap into a defined implementation stream, checkpoint, and task set
- reason:
  - current readiness work stops at evaluation and bounded next-wave hints, but implementation still lacks a fixed architecture
- design authority:
  - `docs/roadmap/aci-market-grade-execution-foundation-goal.md`
  - `docs/roadmap/aci-market-grade-execution-foundation-path.md`
  - `docs/roadmap/aci-market-grade-execution-foundation-checkpoints.md`
  - `docs/design/aci-market-grade-execution-foundation-design.md`
  - `docs/tasks/aci-market-grade-execution-foundation-task-board.md`

## 2. ACI Scan Core Implementation

- target:
  - real scan command
  - target selection
  - scan session and exit behavior
- reason:
  - nothing else becomes product-real until `ACI` can scan a real target

## 3. ACI Detection And Analyzer Runtime

- target:
  - native detector engine
  - external analyzer adapters
  - fingerprint and dedup logic
- reason:
  - market-grade output depends on real finding generation and normalization

## 4. ACI Repeated-Operation Runtime

- target:
  - baseline
  - suppression
  - waiver
  - lifecycle and gate state
- reason:
  - repeated operation is a core difference between a demo tool and a production tool

## 5. ACI Report And Integration Runtime

- target:
  - full JSON report
  - schema validation
  - SARIF
  - hosted integration output
- reason:
  - results must be both machine-consumable and host-platform-ready

## 6. ACI Verification And Hardening

- target:
  - fail-close verification
  - regression tests
  - CI strengthening
  - performance and safety controls
- reason:
  - market trust depends on repeatable correctness, not only feature presence

## 7. ACI Expanded Security Coverage

- target:
  - explicit product direction for secrets, dependency, IaC, and container scanning
- reason:
  - unsupported or postponed classes must be chosen deliberately, not left ambiguous

## Execution Order

1. `ACI Market-Grade Execution Foundation`
2. `ACI Scan Core Implementation`
3. `ACI Detection And Analyzer Runtime`
4. `ACI Repeated-Operation Runtime`
5. `ACI Report And Integration Runtime`
6. `ACI Verification And Hardening`
7. `ACI Expanded Security Coverage`
