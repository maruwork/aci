# ACI Autonomous Code Inspection Tool Contract

Status: Active

## 1. Reader Contract

`ACI` is the common autonomous code-inspection tool body. It interprets the 22 active inspection patterns catalog, runs native / external / human-judgment lanes, normalizes evidence, and returns ranked findings.

This file defines the generic tool contract. It does not define project-specific trigger wiring, DB writeback, operator UI, approval judgment, or current task state. Those belong to each project-local integration shelf.

Primary companion:

- `aci-code-inspection-execution-spec.md`: compact 22 active inspection patterns catalog and report contract
- `aci-product-boundary-and-coverage-policy.md`: explicit completion boundary for language scope, human-judgment lanes, CI-19, and CI-14 supply-chain breadth
- `aci-analyzer-registry-contract.md`: bounded external-analyzer catalog contract
- `aci-profile-execution-contract.md`: bounded profile execution catalog contract
- `aci-analyzer-execution-contract.md`: bounded analyzer execution contract
- `aci-downstream-adoption-contract.md`: bounded downstream adoption contract
- `python/aci_findings.py`: normalized finding helper for structure-signal emission

## 2. Scope

ACI can:

- select inspection lanes for 22 active inspection patterns
- run native static checks where direct evidence is possible
- invoke external analyzers where stronger tool evidence is available
- carry human-judgment findings without pretending they are fully automated
- normalize evidence into one finding format
- separate baseline / waiver / suppression / ranking
- return human-readable and machine-readable reports
- provide bounded native structural/code-smell coverage for Python targets, with blind spots documented in `shared/python/aci_known_limits.py`

ACI does not:

- claim language-general native structural coverage outside Python
- replace human approval
- judge product requirements or business correctness by itself
- solve runner supervision, shell transport, or terminal encoding failures
- own project current trigger / DB / projection wiring
- become the canonical source for project-local trigger routing or runtime authority

## 3. Inspection Lanes

| Lane | Role | Output |
|---|---|---|
| native-static | direct AST / text / structure signals | machine evidence with file / line / rule |
| external-analyzer | lint / type / test / security tools | analyzer result normalized into ACI findings |
| human-judgment | design intent / ownership / domain context | review question with required evidence |

One finding can cross lanes, but handoff must split owners before remediation.

## 4. Profile Model

A profile is a named selection of lanes, scope, severity policy, and output contract.

Minimum profile fields:

- profile id
- target path / include / exclude
- enabled CI IDs
- enabled lanes
- external analyzers
- severity overrides
- baseline / waiver policy
- output format

Profiles must not hide skipped surfaces. If a profile excludes a class of findings, the report must say so.

## 5. Evidence Contract

Every finding must carry:

- CI ID
- target file and tight location when available
- lane
- severity
- finding class
- observed evidence
- impact
- owner / next action
- verification method

Use the finding classes from `aci-code-inspection-execution-spec.md`: confirmed defect, design / review question, and noise / not applicable.

## 6. Baseline, Waiver, Suppression, Ranking

| Concept | Meaning | Rule |
|---|---|---|
| baseline | known existing finding set | separates old debt from new regression |
| waiver | approved exception | requires owner, reason, expiry or review condition |
| suppression | noise filter | must be narrow and explainable |
| ranking | remediation order | follows severity, blast radius, confidence, and fix leverage |

Suppression rules belong to the tool implementation / profile config. The compact execution spec defines pattern meaning and report contract; it is not a long suppressor catalog.

## 7. Extension Rule

ACI should grow by adding the smallest fitting extension:

1. lane selection or profile change
2. native-static rule
3. external analyzer integration
4. evidence schema extension
5. dedicated companion lane for non-inspection failures
6. human-judgment formalization

Do not turn ACI into a universal governance engine. If a concern belongs to project runtime, approval, DB authority, or operator workflow, route it to the integration layer.
