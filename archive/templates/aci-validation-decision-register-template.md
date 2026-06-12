# ACI Validation Decision Register Template

**canonical shelf**: `persistence/templates/aci-persistence-validation-decision-register-template.md`
**legacy status**: 互換維持のため `templates/` に残している。persistence layer で読む時は canonical shelf を主に見る。

**使う場面**: 特定 project 上で `ACI` を回した residual の判定を、記憶に頼らず残す時に使う。  
**差し替える所**: `project_id`、`tool_id`、bucket 名、owner lane、human-confirm の扱い。  
**書かないこと**: 共通 detector 設計、project 全体の current board、修正実装 plan 本文。

**project_id**: `project_xxx`  
**tool_id**: `aci_local_001`  
**status**: Draft / Active

---

## Purpose

- reviewed residual の分類を traceable に残す
- detector tuning / suppress / decomposition / implementation follow-up を project-local に追う
- `ACI` が出した finding と manual conclusion の actor を混同しない

## Three-Way Classification Rule

reviewed finding は、owner boundary を確認したうえで **次の3分類のいずれかに必ず落とす**。

| 分類 | 何を意味するか | 主な行き先 |
|---|---|---|
| **根本解決で潰すべきもの** | repo 側の実装修正で消すべき true positive | implementation follow-up |
| **ツール側で消せる誤検知** | detector / suppress / decomposition で消せる false positive | detector work |
| **人間確認で除外する必要があるもの** | 文脈判断が残るため人間確認が必要 | human-confirm |

ルール:

- 1 finding = 1分類
- 複数の runtime role / failure behavior / judgment question を束ねる finding は、
  先に decomposition してから分類する
- `manual-only gap` や companion lane owner の事象は、owner boundary を切ってから記録する
- 各 row には最低限 `actor label` / `owner lane` / `current bucket` / `recommended bucket` / `reason` を入れる

## Bucket Mapping

- `根本解決で潰すべきもの`
  - 下の `Residuals Confirmed As Implementation-Side Follow-Up`
- `ツール側で消せる誤検知`
  - 下の `Residuals Requiring Detector Decomposition Before Bucketing`
  - 下の `Human-Confirm Residuals Confirmed As Tool-Side Suppressible Pending Detector Work`
- `人間確認で除外する必要があるもの`
  - 下の `Human-Confirm Residuals That Still Require Human Confirmation`
  - 下の `Human-Confirm Residuals Likely Removable Later`

## Human-Confirm Rendering Rule

human-facing review output は、最低でも次の 8 見出しへ投影できなければならない。

- `コード全体の目的`
- `ツール名`
- `エラー種別`
- `参照先`
- `エラー内容`
- `詳細解説`
- `推奨`
- `確認事項`

## Residuals Requiring Detector Decomposition Before Bucketing

| date | actor label | owner lane | target file | line | signal | current bucket | recommended bucket | code excerpt | runtime role | failure behavior | judgment question | reason | source report | promotion candidate | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Human-Confirm Residuals Confirmed As Tool-Side Suppressible Pending Detector Work

| date | actor label | owner lane | target file | line | signal | current bucket | recommended bucket | code excerpt | runtime role | failure behavior | judgment question | reason | source report | promotion candidate | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Human-Confirm Residuals That Still Require Human Confirmation

| date | actor label | owner lane | target file | line | signal | current bucket | recommended bucket | code excerpt | runtime role | failure behavior | judgment question | reason | source report | promotion candidate | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Residuals Confirmed As Implementation-Side Follow-Up

| date | actor label | owner lane | target file | line | signal | current bucket | recommended bucket | code excerpt | runtime role | failure behavior | judgment question | reason | source report | promotion candidate | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Human-Confirm Residuals Likely Removable Later

| date | actor label | owner lane | target file | line | signal | current bucket | recommended bucket | code excerpt | runtime role | failure behavior | judgment question | reason | source report | promotion candidate | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Notes

- `current bucket` = latest validation report での現分類
- `recommended bucket` = reviewed next-state
- `actor label` = `ACI-detected` / `manual refinement of ACI output` / `manual-only gap`
- `owner lane` = `ACI` / external analyzer / human-judgment / integrity guard / other companion lane
- `promotion candidate` = recurring pattern を `spec -> design -> ACI` へ上げるかどうか
- `status` = detector work / implementation work / rerun proof の進捗
- `manual-only gap` を記録する場合は、`ACI` 欠落と断定する前に companion lane owner を書く
- 同じ `manual-only gap` が複数 project で再発し、human policy judgment を要しないなら `promotion candidate=yes` とする
