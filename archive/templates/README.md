# ACI Legacy Compatibility Templates

Status: Active

## Purpose

`templates/` は legacy compatibility shelf。旧 route を維持するために残している。

## Boundary Rule

- この棚は新規正本ではない
- 新しい採用時は canonical shelf を優先する
- ownership や placement rule の更新は canonical shelf 側を先に直す

## Canonical Route

- project-local integration:
  - `../runtime/templates/aci-runtime-project-local-integration-template.md`
- remediation brief:
  - `../report/templates/aci-report-remediation-brief-template.md`
- validation decision register:
  - `../persistence/templates/aci-persistence-validation-decision-register-template.md`

## Legacy Files

- `aci-project-local-integration-template.md`
- `aci-remediation-brief-template.md`
- `aci-validation-decision-register-template.md`
- `LEGACY_TEMPLATE_SUNSET.md`
