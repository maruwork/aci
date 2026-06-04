# ACI

**目的**: 汎用コード・ファイルチェックツールの共通正本棚。

ここでは、ACI の共通 code、template、example を持つ。
特定 project の current 状態や運用結果は持たない。
また、特定 project の import layout や side program 固有名を共通正本へ直書きしない。

## これは何か

- `ACI` は汎用コード inspection tool の共通正本棚
- core は domain-independent
- `Pier` などは optional domain pack として追加する
- project-local trigger や current state は downstream integration 側で持つ

`ACI` は、共通 inspection catalog、normalized finding、optional domain pack、report contract を提供する共通棚です。

## これは何ではないか

- `Pier` 専用 repo ではない
- project-local runtime gate そのものではない
- DB writeback や operator workflow の最終 owner ではない

## コンポーネント

| コンポーネント | 役割 |
|---|---|
| `core/` | generic inspection catalog と tool contract |
| `python/` | loader、finding helper、signal/profile/wording helper |
| `domains/` | optional domain pack |
| `runtime/` | quickstart と runtime binding guidance |
| `report/` | report contract と public samples |
| `persistence/` | reviewed residual / artifact traceability contract |
| `integrations/` | bounded external connection contracts |

## 3-Minute Evaluation

GitHub 初見で最短確認したい時は、まず次を見る。

1. `core/aci-autonomous-code-inspection-tool-contract.md`
2. `core/aci-code-inspection-execution-spec.md`
3. `runtime/aci-generic-quickstart.md`
4. `report/aci-generic-report-contract.md`
5. `ACI_SHELF_CLASSIFICATION.md`

最小 smoke check は次で足りる。

```bash
python python/aci_public_smoke.py
```

公開向け sample report は `report/examples/` にある。

## セットアップ

### 1. まず共通棚だけ試す

```bash
python python/aci_public_smoke.py
```

この smoke check は次だけを確認する。

- `aci core only`
- `aci + pier domain`
- normalized finding emission
- mirror sync helper

### 2. その後に読むもの

- `runtime/aci-generic-quickstart.md`
- `report/examples/`
- `PUBLIC_RUNTIME_ASSUMPTIONS.md`
- `NON_GOALS.md`
- `DOMAIN_PACK_EXTENSION_GUIDE.md`
- `REPO_EXPORT_GUIDE.md`
- `REPO_EXPORT_CHECKLIST.md`
- `PRE_PUBLICATION_DECISIONS.md`
- `OWNER_DECISION_PACKET.md`
- `CONTRIBUTING_DRAFT.md`
- `SECURITY_DRAFT.md`
- `RELEASE_BOOTSTRAP_NOTES.md`
- `PUBLISHABLE_HOLD_CHECKLIST.md`
- `PUBLIC_GO_LIVE_SEQUENCE_DRAFT.md`
- `PUBLIC_RELEASE_CHECKLIST.md`
- `PRIVATE_HOST_BOOTSTRAP_RUNBOOK.md`
- `PRIVATE_RELEASE_HOLD_LINE.md`

## 棚

- `python/`: generic signal / profile / wording の共通 code。path / side-program term / surface は placeholder で置き、project 側で差し替える
  - 当面は `ACI core python` の暫定棚として扱う
  - domain pack 選択の helper は `python/aci_domain_loader.py`
- `core/`: domain-independent core の概念棚。今 wave の物理 mapping は `python/` と `examples/`
- `templates/`: legacy 互換のため残している共通雛形。canonical shelf は `runtime/` `report/` `persistence/` を優先する
  - downstream 側で canonical shelf 参照へ移行が確認できた後に削除候補とする
  - 削除条件は `templates/LEGACY_TEMPLATE_SUNSET.md`
- `examples/`: false-negative challenge pack、precision replay pack などの共通 sample
  - domain-independent example pack の canonical shelf
- `domains/`: `Pier` など domain pack の置き場
- `runtime/`: project-local runtime binding の責務棚
  - runtime/operator-facing boundary constants もここで持つ
- `report/`: owner-facing report 契約の責務棚
- `persistence/`: residual / artifact traceability の責務棚
  - `report/` と `persistence/` は runtime 配下へ入れず top-level で維持する
- `integrations/`: healthcheck など外部接続の責務棚

## 公開ファイル構成

```text
./
├── README.md
├── ACI_SHELF_CLASSIFICATION.md
├── REPO_EXPORT_GUIDE.md
├── REPO_EXPORT_CHECKLIST.md
├── PRE_PUBLICATION_DECISIONS.md
├── OWNER_DECISION_PACKET.md
├── CONTRIBUTING_DRAFT.md
├── SECURITY_DRAFT.md
├── RELEASE_BOOTSTRAP_NOTES.md
├── PUBLISHABLE_HOLD_CHECKLIST.md
├── PUBLIC_GO_LIVE_SEQUENCE_DRAFT.md
├── PUBLIC_RUNTIME_ASSUMPTIONS.md
├── NON_GOALS.md
├── DOMAIN_PACK_EXTENSION_GUIDE.md
├── PUBLIC_RELEASE_CHECKLIST.md
├── PRIVATE_HOST_BOOTSTRAP_RUNBOOK.md
├── PRIVATE_RELEASE_HOLD_LINE.md
├── core/
├── python/
├── domains/
├── runtime/
├── report/
├── persistence/
├── integrations/
├── roadmap/
├── tasks/
└── design/
```

## 汎用と非汎用の境界

- 汎用 `ACI` 正本:
  - `core/`
  - `python/`
  - `examples/`
  - `runtime/`
  - `report/`
  - `templates/`
  - `integrations/`
- 非汎用:
  - `domains/<domain>/`
  - `persistence/aci-<domain>-*.md`
- classification 一覧:
  - `ACI_SHELF_CLASSIFICATION.md`

## Optional Domain Packs

- `aci core only`
  - generic core only
- `aci + pier domain`
  - optional Pier investigation vocabulary and bridge docs
- future `aci + <domain>`
  - same pack shapeで追加する

## Standalone Repo View

- current physical home in this monorepo is `common/aci/`
- public-facing commands and file paths in this shelf are written repo-relative
- if this shelf is lifted into its own repo, keep `README.md`, `python/`, `core/`, `runtime/`, `report/`, and `domains/` at the repo root
- extraction notes are in `REPO_EXPORT_GUIDE.md`

## Pre-Publication Drafts

The following files are preparation assets only. They do not mean `ACI` is already public.

- `PRE_PUBLICATION_DECISIONS.md`
- `OWNER_DECISION_PACKET.md`
- `CONTRIBUTING_DRAFT.md`
- `SECURITY_DRAFT.md`
- `RELEASE_BOOTSTRAP_NOTES.md`
- `PUBLISHABLE_HOLD_CHECKLIST.md`
- `PUBLIC_GO_LIVE_SEQUENCE_DRAFT.md`

## Private Bootstrap Docs

The following are execution-grade docs for preparing the repository in a private state while explicitly stopping before public release.

- `PRIVATE_HOST_BOOTSTRAP_RUNBOOK.md`
- `PRIVATE_RELEASE_HOLD_LINE.md`

## 使い方

1. generic code の placeholder を project ごとの path / scope / surface に差し替えて runtime copy を作る
2. `templates/` の雛形を project 側へ持ち込む
3. project ごとの path、scope、surface、result writeback 先だけ差し替える
4. `examples/` で期待挙動を確認する

## ACI Independence Reading Order

`ACI` 独立化を読む時は次の順に読む。

1. `roadmap/aci-independence-goal.md`
2. `roadmap/aci-independence-path.md`
3. `roadmap/aci-independence-checkpoints.md`
4. `tasks/aci-independence-task-board.md`
5. `design/aci-independence-basic-design.md`

## ACI Generic Hardening Reading Order

1. `roadmap/aci-generic-hardening-goal.md`
2. `roadmap/aci-generic-hardening-path.md`
3. `roadmap/aci-generic-hardening-checkpoints.md`
4. `tasks/aci-generic-hardening-task-board.md`
5. `design/aci-generic-hardening-design.md`

## ACI Mirror Governance Reading Order

1. `roadmap/aci-mirror-governance-goal.md`
2. `roadmap/aci-mirror-governance-path.md`
3. `roadmap/aci-mirror-governance-checkpoints.md`
4. `tasks/aci-mirror-governance-task-board.md`
5. `design/aci-mirror-governance-design.md`

## ACI Private Host Bootstrap Reading Order

1. `roadmap/aci-private-host-bootstrap-goal.md`
2. `roadmap/aci-private-host-bootstrap-path.md`
3. `roadmap/aci-private-host-bootstrap-checkpoints.md`
4. `tasks/aci-private-host-bootstrap-task-board.md`
5. `design/aci-private-host-bootstrap-design.md`

## Common ACI Core Reading Order

1. `core/aci-autonomous-code-inspection-tool-contract.md`
2. `core/aci-code-inspection-execution-spec.md`
3. `runtime/aci-generic-quickstart.md`
4. `report/aci-generic-report-contract.md`
5. `persistence/README.md`
6. `report/examples/`
7. `PUBLIC_RUNTIME_ASSUMPTIONS.md`
8. `NON_GOALS.md`
9. `DOMAIN_PACK_EXTENSION_GUIDE.md`
10. `PUBLIC_RELEASE_CHECKLIST.md`

## 汎用棚として守ること

- 特定 project の import path を前提にしない
- 特定 project / tool 群の固有名を signal rule に直書きしない
- current register、operator manual、validation result のような運用生成物を置かない

## 書かないこと

- 特定 project 固有の current register
- 特定 project 固有の operator manual
- project 固有の validation 記録

## 戻り先

- この棚の入口へ戻る: `README.md`
- standalone repo として読む時も、この `README.md` を起点にする

## Pier Integration Documents

以下は generic `ACI` 正本ではなく、`Pier` 専用 bridge document。

- `domains/pier/aci-pier-integration-spec.md`
- `domains/pier/aci-trigger-read-spec.md`
- `domains/pier/aci-trigger-routing-spec.md`
- `persistence/aci-pier-validation-decision-register.md`
