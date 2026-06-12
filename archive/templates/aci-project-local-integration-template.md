# ACI Project-Local Integration Template

**canonical shelf**: `runtime/templates/aci-runtime-project-local-integration-template.md`
**legacy status**: 互換維持のため `templates/` に残している。runtime layer で読む時は canonical shelf を主に見る。

**使う場面**: 共通の `ACI` 本体を、特定 project の起動条件、対象範囲、閾値、出力先に接続する時に使う。  
**差し替える所**: `project_id`、`tool_id`、trigger matrix、threshold、report shelf、例外 handling。  
**書かないこと**: detector 本体の設計、共通 `ACI` catalog の定義、project 全体の runtime rule。

**project_id**: `project_xxx`  
**tool_id**: `aci_local_001`  
**status**: Draft / Approved  
**generic_refs**:
- `SE-251_autonomous-code-inspection-tool.md`
- `code-inspection-execution-spec.md`

---

## 1. Purpose

- generic `ACI` をこの project の current runtime / operator flow にどう接続するかを固定する

## 2. Scope

- scan target roots
- trigger / caller
- blocking threshold
- report shelf
- exception handling

## 3. Out of Scope

- generic `CI-01`〜`CI-27` catalog の再定義
- detector 実装そのもの
- project 外の runtime / DB rule

## 4. Local Trigger Matrix

| profile | caller | timing | scan scope | notes |
|---|---|---|---|---|
| `startup` | `{caller}` | `{timing}` | `{scope}` | `{notes}` |
| `quick-gate` | `{caller}` | `{timing}` | `{scope}` | `{notes}` |
| `state-change` | `{caller}` | `{timing}` | `{scope}` | `{notes}` |
| `wrap-up` | `{caller}` | `{timing}` | `{scope}` | `{notes}` |
| `full` | `{caller}` | `{timing}` | `{scope}` | `{notes}` |

## 5. Local Thresholds

- block threshold:
  - `{example: HIGH on fail-close candidates}`
- review threshold:
  - `{example: HIGH and MEDIUM require review}`
- advisory threshold:
  - `{example: MEDIUM only summary}`

## 6. Local Report Shelf

- machine-readable output:
  - `{path}`
- human-readable report:
  - `{path}`
- retention:
  - `{policy}`

## 6.1 Local Report Contract

- raw `ACI` findings only で終える report か、manual conclusion を含む report かを明記する
- manual conclusion を含む場合、各 conclusion を次で label する
  - `ACI-detected`
  - `manual refinement of ACI output`
  - `manual-only gap`
- `manual-only gap` を `ACI` emitted finding として書かない
- non-ACI owner の issue を扱う場合は companion lane を書く
  - `{example: integrity guard / snapshot checker / runtime supervision owner}`
- `CI21` broad cluster を remediation handoff する時は、少なくとも
  - runtime role
  - failure behavior
  - judgment question
  ごとに分解して書く
- owner handoff を出す場合は、少なくとも次を含む
  - output compatibility
  - verification results
  - deferred items
  - extraction / commonization boundary
  - verification results には status を付ける
    - `executed`
    - `code-review-only`
    - `blocked`
  - `blocked` の場合は runtime prerequisite / blocker を書く
  - deferred items には wave class を付ける
    - `first-wave`
    - `second-wave`
    - `aci-candidate`
    - `structural-debt`

## 7. Local Exception / Baseline Rule

- baseline file:
  - `{path or none}`
- waiver file:
  - `{path or none}`
- local exception principle:
  - `{rule}`

## 8. Post-Run Action

- pass:
  - `{action}`
- revision:
  - `{action}`
- escalation:
  - `{action}`
- decompose-then-reclassify:
  - `{action}`

## 9. Validation Authority

- reviewed residual authority:
  - `{project-local validation decision register path}`
- generic rule authority:
  - `SE-251_autonomous-code-inspection-tool.md`
  - `code-inspection-execution-spec.md`
- companion lane authorities:
  - `{example: integrity checker / runtime guard / security audit owner}`
- promotion-to-generic authority:
  - `{path or note where recurring manual-only patterns are proposed back to generic spec/design/ACI}`
