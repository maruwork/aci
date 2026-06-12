# タスク依頼書 task_aci001: Autonomous Code Inspection Pier Integration

Status: Active

**タスクID**: task_aci001  
**タスク名**: Autonomous Code Inspection — Pier Integration  
**タスク種別**: CURRENT_SPEC  
**フェーズ**: PARENT-004 mainline integration  
**担当**: LE / SE / operator  
**依存タスク**: なし  
**参照設計書**:
- [SE-251_autonomous-code-inspection-tool.md](pier:shared/docs/design/SE-251_autonomous-code-inspection-tool.md)
- [task_aci001_trigger-routing-spec.md](pier:shared/specs/current/task_aci001_trigger-routing-spec.md)
- [task_aci001_trigger-read-spec.md](pier:shared/specs/current/task_aci001_trigger-read-spec.md)
- [autonomous-code-inspection-tool_design_20260522.md](pier:workspace/claudecode-output/governance/autonomous-code-inspection-tool_design_20260522.md)

---

## 1. 目的・スコープ

> **Boundary**:
> この spec は `Pier` integration だけを定義する。
> generic `ACI` の正本棚は repo root、template 正本棚は `shared/runtime/templates/`・`shared/report/templates/`。
> この file で generic `ACI` template / wording / report / persistence 契約を再定義しない。

### 1.1 目的

共通 tool `autonomous_code_inspection` を `Pier` の current plane / trigger / operator surface / DB-adjacent read model に接続するための current spec を固定する。

### 1.2 スコープ

- `Pier` 側 trigger / caller
- current operator surface 合流
- `governance_alerts` 投影
- history / projection / summary の current read model
- build-side integration in `Pier`
- full completion authority in `Pier`
- project-local dirty-tree discipline companion lane

### 1.3 スコープ外

- ACI tool body の共通契約
- `CI-01`〜`CI-27` の共通 catalog 定義
- external analyzer 自体の owner rule
- Git authority や delete / archive / restore の最終 owner judgment
- generic template / common wording / generic report / generic persistence 契約

---

## 2. Integration Boundary

### 2.1 current operator surfaces

ACI が `Pier` で合流する current reading surface は次。

- `effective_task_state`
- `pending_human_gate_queue`
- `governance_alerts`

### 2.2 downstream caller surfaces

- `session_start.py`
- `governance_healthcheck.py`
- `aci_build_gate.py`
- `update_task_state.py`
- `update_task_state_query.py`
- `report.py`
- `wrap_up.py`
- `mcp_server.py`
- `regenerate_docs.py`

### 2.3 non-conflict rule

- 新しい current state surface を作らない
- 新しい alert plane を作らない
- detection rule 本体を caller 側へ分散しない
- projection consumer が heavy inspection caller にならない

---

## 3. Trigger Matrix

### 3.1 operational profiles

- `startup`
- `quick-gate`
- `state-change`
- `wrap-up`
- `full`

### 3.2 build-side profiles

- `build-preflight`
- `build-review`

### 3.3 split reading authority

- trigger routing の正本:
  - [task_aci001_trigger-routing-spec.md](pier:shared/specs/current/task_aci001_trigger-routing-spec.md)
- trigger ごとの read-budget / read-surface の正本:
  - [task_aci001_trigger-read-spec.md](pier:shared/specs/current/task_aci001_trigger-read-spec.md)

本 spec では trigger と read-spec を混ぜない。

### 3.4 fixed restrictions

- 全 trigger で全 profile を走らせない
- 1 trigger は 1 primary profile のみ
- `report.py` / `mcp_server.py` / `regenerate_docs.py` は projection consumer であり、新規 broad caller にならない
- `ACI` は front-stage security guard の代替にしない
- reviewed finding を `actionable` のまま未分類で積み残さない
- trigger routing と trigger read-spec を同一 section に混載しない

### 3.5 Pier operational overlay

#### Mode A: Pier 自体のファイル

**対象ディレクトリ**:

- `shared/tools/`（サブディレクトリ含む）
- `shared/db/`
- `shared/tests/`
- `shared/alembic/versions/`

**実行タイミング**:

- 週次整合性チェック（フェーズ4相当）
- Pier 本体への大規模変更後

#### Mode B: Pier が作成するファイル

**対象ディレクトリ**:

- `system-dev/pj-*/` 配下で PG が新規作成した `.py` ファイル

**実行タイミング**:

- PG が `.py` ファイルを書き込んだ直後（PostToolUse フック）
- または `STEP4_REQUEST` 遷移前の validation

**自動実行時の判定**:

- CRITICAL 1件以上 → `STEP4_REQUEST` を遮断し REVISION 扱い
- HIGH 2件以上 → `STEP4_REQUEST` を遮断し REVISION 扱い
- MEDIUM のみ → 通過し、改善推奨として監査 JSON に記録

#### Mode C: dirty-tree discipline companion lane

**位置づけ**:

- `ACI` 共通コアの拡張ではなく、`Pier` project-local companion lane
- status は **reserved**。caller proof が入るまでは active route として扱わない

**対象入力**:

- `git status --short` 相当の dirty path list
- `shared/docs/file-taxonomy.md`
- `shared/docs/document-boundary-register.md`
- `shared/governance/file-and-folder-operation-rules.md`
- active closure board / execution register（存在する場合のみ）

**想定実行タイミング**:

- handoff preparation
- pre-commit review
- lane switch review
- end-of-session review

**判定の役割**:

- `THEME_MIX`
- `OWNER_UNKNOWN`
- `FORBIDDEN_SHELF_TOUCH`
- `CLASS_MIX`
- `GENERATED_DRIFT`
- `ROOT_RULE_BREAK`
- `PARKED_LANE_TOUCH`

**companion verdict**:

- `clean`
- `review-needed`
- `fail-close-candidate`

**非役割**:

- commit / restore / archive の代行
- historical vs canonical の最終確定
- theme close 判定

### 3.6 Pier exception list

以下のファイルは構造上の理由により一部閾値の例外を認める。
ただし CRITICAL（循環インポート・SQL インジェクション等）は対象外とする。

| ファイル | 許容閾値（CI-04 行数） | Pier 理由 |
|---|---|---|
| `shared/tools/import_audit.py` | 1000行 | 複数 ADR にまたがる監査ロジックを単一エントリポイントに集約しているため |
| `shared/tools/update_task_state.py` | 1000行 | 全ステータス遷移ロジックと CLI を単一スクリプトに集約しているため |

新たに例外を追加する場合は、ファイル名・許容閾値・根拠 ADR を必ず記載する。

### 3.7 Pier post-run handling

| 項目 | 内容 |
|---|---|
| 実行者 | LE |
| Mode A 実行頻度 | 週次 または Pier 本体への大規模変更後 |
| Mode B 実行頻度 | PG が `.py` を書き込んだ直後（PostToolUse hook 自動実行） |
| Mode C 実行頻度 | reserved; handoff / pre-commit / lane-switch / end-of-session review に限定 |
| REVISION 判定後のアクション | 全検出パターンを PT 登録し、次回セッションで修正計画を提示する |
| PASS 判定後のアクション | レポートのみ保管し、PT 登録不要 |
| レポート保管 | `workspace/audit-results/YYYYMMDD_code_inspection_report.md`（直近3件を保持） |
| 例外リスト変更ルール | `import_audit.py` / `update_task_state.py` の上限変更はマネージャー承認必須 |

Mode C の場合は追加で次を守る:

- `fail-close-candidate` を出しても owner judgment を自動実行しない
- dirty-tree disposition は closure board / owner lane に返す

#### 3.7.1 mandatory disposition after review

Pier で `ACI` finding を review した後は、各 finding を必ず次のいずれかに落とす。

- `fix-now`
- `fix-next`
- `exclude`
- `hold`

`fix-next` と `hold` には、owner、理由、次に触る条件を残す。未分類の `actionable` を current board に積んだままにしてはならない。

---

## 4. Alert / Projection / History

### 4.1 alert projection

- top-level findings を `governance_alerts` へ投影する
- lower-level static signals は evidence として保持し、alert plane へ直接は出さない

### 4.2 required storage

- `inspection_run_history`
- `inspection_remediation_history`
- `inspection_detail_projection`
- `inspection_history_summary_projection`

### 4.3 operator summary

最低限、次を current surface から読めること。

- active top-level findings
- ranked summary
- latest remediation / rerun 状態
- unresolved carry

---

## 5. Build-Side Integration

### 5.1 boundary

- `feature-dev` は existing code analysis owner のまま維持する
- ACI は structure inspection / patchwork / bypass residue の inspection owner に留まる

### 5.2 build-side loop

1. `feature-dev`
2. `build-preflight`
3. human alignment
4. implementation
5. `build-review`
6. unresolved finding があれば rework

### 5.3 build-side non-substitution

ACI は次を置き換えない。

- `feature-dev` の既存コード地図
- review / approval flow
- repo 正本 verification

---

## 6. Full Completion Contract In Pier

### 6.1 Pier運用 full completion

- `autonomous_code_inspection.py` が唯一の inspection judgment owner
- operational profiles が caller contract どおり実装される
- top-level findings が `governance_alerts` に投影される
- history / projection / summary storage が current read model として実装される
- `event_ledger` の意味を汚染しない
- caller/read integration が current surfaces へ揃う

### 6.2 Pier作成 full completion

- `build-preflight` / `build-review` が caller contract どおり実装される
- build-side result は current SSOT に昇格しない
- machine-readable JSON と human-readable review evidence summary を返す
- human-in-the-loop build-side loop を維持する

### 6.2.1 current caller-proof reading

- `startup` -> `session_start.py`
- `quick-gate` / `full` -> `governance_healthcheck.py`
- `state-change` -> `update_task_state.py`
- `wrap-up` -> `wrap_up.py`
- `build-preflight` / `build-review` -> `aci_build_gate.py`

現在の残課題は caller 不在ではなく、runtime cost / false positive / operator wording の継続調整である。

### 6.3 overall completion reading

`Pier` で ACI を完成と呼ぶのは、運用側・作成側の両方が満たされた時だけ。

---

## 7. Immediate Reading Authority

ACI の共通契約は [SE-251_autonomous-code-inspection-tool.md](pier:shared/docs/design/SE-251_autonomous-code-inspection-tool.md) を正とする。  
`Pier` での trigger / surface / storage / completion authority は本 spec を正とする。

ただし、

- trigger routing は [task_aci001_trigger-routing-spec.md](pier:shared/specs/current/task_aci001_trigger-routing-spec.md)
- trigger ごとの read-budget / read-surface は [task_aci001_trigger-read-spec.md](pier:shared/specs/current/task_aci001_trigger-read-spec.md)

を直読する。

## 8. Validation Decision Register

### 8.1 Authority

`Pier` 上で実行した `ACI` validation residual の reviewed classification 正本は次とする。

- [task_aci001_validation-decision-register.md](pier:shared/specs/current/task_aci001_validation-decision-register.md)

### 8.2 Reading Rule

- 共通 tool rule や validation report contract は
  [SE-251_autonomous-code-inspection-tool.md](pier:shared/docs/design/SE-251_autonomous-code-inspection-tool.md)
  を正とする
- `Pier` validation run で残った reviewed residual のうち
  - `human-confirm`
  - `human-confirm` だが later suppressible
  の分類は、本 register を正とする
- detector tuning へ戻す候補でも、`Pier` run を根拠にした reviewed
  decision は先に本 register へ残す

### 8.3 Human-Confirm Rendering Rule In Pier

`Pier` で `human-confirm` として出す項目は、抽象文ではなく次の固定見出しで
人間に提示する。

- コード全体の目的
- ツール名
- エラー種別
- 参照先
- エラー内容
- 詳細解説
- 推奨
- 確認事項

出力条件:

- `コード全体の目的` は、そのファイルやコマンドがワークフロー上で何を達成する
  ためのものかを先に説明する。局所的な if / except の説明だけでは足りない
- `参照先` は file path だけでなく、必要なら line まで含める
- `エラー内容` は一文で「今なにが起きているか」を書く
- `詳細解説` は
  - なぜ検知されたか
  - その処理の runtime role は何か
  - 今の fallback / failure behavior は何か
  - 消したら何が変わるか
  を含める
- `推奨` は
  - 現時点で最も筋が良い判断案
  - その短い理由
  を書く
  - 強制結論ではなく、reviewer が最初に比較すべき既定候補として扱う
- `確認事項` は、人間が yes/no または 2択で答えられる形にする

この形に落とせないものは、`human-confirm` に送る前に情報不足として差し戻す。
また、複数の `except` や複数の runtime role が 1 束で出ていて、
確認事項が 1 問に定まらないものは、そのまま `human-confirm` に送らない。
先に `except` 単位または decision question 単位へ分解してから再分類する。
