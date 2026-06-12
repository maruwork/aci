# ACI Remediation Brief Template

**canonical shelf**: `report/templates/aci-report-remediation-brief-template.md`
**legacy status**: 互換維持のため `templates/` に残している。report layer で読む時は canonical shelf を主に見る。

**使う場面**: `ACI` の監査結果を、repository owner がそのまま修正着手できる修正 brief に落とす時に使う。  
**差し替える所**: `project_id`、wave の切り方、actor label、verification contract、handoff 先。  
**書かないこと**: raw finding の全量転記、detector 本体の改善設計、project 全体の current 管理。

**project_id**: `project_xxx`  
**audit_run_ref**: `{artifact path or run id}`  
**status**: Draft / Active / Handed-off

---

## 1. Purpose

- 監査結果を owner handoff 可能な修正指示へ変換する
- `ACI` finding と manual repair planning を混同しない

## 2. Conclusion Actor Labels

- `ACI-detected`
- `manual refinement of ACI output`
- `manual-only gap`

各 repair wave / hold item / deferred item に actor label を付ける。

## 3. Repair Wave Summary

| wave | wave class | actor label | target files | target signals | owner action | priority | reason |
|---|---|---|---|---|---|---|---|
| `wave-1` |  |  |  |  |  |  |  |

## 4. File-Level Repair Instructions

| file | actor label | target lines or function | issue summary | required change | acceptance check |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## 5. Output Compatibility

- unchanged surfaces:
  - `{UI / API / generated artifact / routing / CLI output}`
- compatibility statement:
  - `{what remains unchanged and why}`
- compatibility risk if touched:
  - `{what would break if the boundary is crossed}`

## 6. Verification Results

| target | command or check | pass condition | observed result | verification status | runtime prerequisite or blocker |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

- `verification status`
  - `executed` = 実行または観測で確認済み
  - `code-review-only` = コード読解だけで、実行検証ではない
  - `blocked` = 実行前提不足のため未実行

## 7. Deferred Items

| item | wave class | actor label | reason deferred | next wave or owner |
|---|---|---|---|---|
|  |  |  |  |  |

- `wave class`
  - `first-wave` = 今回ただちに直す対象
  - `second-wave` = 次の修正波で扱う対象
  - `aci-candidate` = generic ACI へ返す候補
  - `structural-debt` = 今回の narrow repair を超える大きい負債

## 8. Extraction / Commonization Boundary

- moved to common authority:
  - `{helper / module / common layer}`
- intentionally kept file-local:
  - `{project-specific replacement table / runtime-specific branch / manual assembly logic}`
- boundary reason:
  - `{why it was split this way}`

## 9. Companion-Lane Holds

`ACI` owner boundary 外の項目がある場合だけ書く。

| item | owner lane | why not ACI-owned | follow-up |
|---|---|---|---|
|  |  |  |  |

## 10. Attached Evidence

- raw audit report:
  - `{path}`
- machine-readable artifact:
  - `{path}`
- verification note or replay:
  - `{path}`

## 11. Handoff Rule

- この brief は、owner が full audit trail を再読せず first repair wave に着手できる粒度で書く
- `output compatibility`、`verification results`、`deferred items`、`extraction / commonization boundary` の 4 面が空なら handoff-ready としない
- `manual-only gap` を `ACI` finding と誤記しない
- `verification status` は `executed` / `code-review-only` / `blocked` のいずれかを必ず書く
- `blocked` の行は runtime prerequisite / blocker を空欄にしない
- `wave class` は `first-wave` / `second-wave` / `aci-candidate` / `structural-debt` のいずれかを使う
