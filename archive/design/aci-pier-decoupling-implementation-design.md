# ACI Pier Decoupling Implementation Design

**Task**: aci-pier-decoupling
**Author**: agent
**Date**: 2026-06-08
**Status**: Complete (Amendment 2 2026-06-09; resolved 2026-06-09)

---

## 0. Workstream Linkage

| Layer | File |
|---|---|
| ゴール | `archive/roadmap/aci-independence-goal.md` |
| 道のり | `archive/roadmap/aci-independence-checkpoints.md` |
| チェックポイント | CP6: コード結合除去 |
| タスク（上位） | `archive/tasks/aci-independence-task-board.md` |
| タスク（詳細） | `archive/tasks/aci-pier-decoupling-task-board.md` |
| 設計 | 本文書 |

---

## 1. Packet Minimum Fields

| Field | Value |
|---|---|
| task_id | aci-pier-decoupling |
| goal | ACI core から Pier 固有の hardcoding を全て除去し、domain pack をファイル読み込みで動的ロードする完全汎用ツールにする |
| owner_role | ACI maintainer |
| 完了報告主語 | ACI |
| trigger_owner | ACI maintainer |
| execution_owner | agent |
| decision_owner | ACI maintainer |
| storage_owner | `archive/tasks/aci-pier-decoupling-task-board.md`（task status） |
| scope_in | 下記「4. Files」の Modify 対象ファイル |
| scope_out | CI catalog、finding normalization、report contract、persistence contract、Pier 統合 spec 文書群（domains/pier/*.md） |
| next_gate | 計画書 Approved → 実装 → 検証 (smoke + pytest) → 計画書 Complete |
| cp6_scope_note | この波は CP6 の部分完了。docs 配置（runtime/report/persistence/integration）は後続波に委ねる。CP6 close は後続波完了後 |

---

## 2. Implementation Decision Record

### 2.1 Background

`aci-independence-goal.md` は Current Judgment = "complete" だが、コード調査（2026-06-08）で次の Pier 固有 hardcoding が残存していることを確認した。

| 箇所 | 問題 |
|---|---|
| `python/aci_domain_loader.py:88-95` | `if domain_id == "pier":` の閉じた分岐。第3ドメインを追加できない |
| `python/aci_cli.py:232` | `choices=["core-only", "pier"]` — CLI が pier を列挙 |
| `python/aci_public_smoke.py:21` | `load_domain_rules("pier")` — smoke が Pier を必須としている |
| `python/aci_public_smoke.py:detect_repo_root` | `ancestor.parent.name == "common"` — モノレポ前提の判定。standalone 環境では repo root を誤検出または検出失敗する |
| `python/aci_config.py:13` | `VALID_SAMPLE_MODES = {"core", "pier"}` — pier が固定 |
| `python/aci_signals.py:48-69` | `LOW_INFO_SCATTERED_LITERALS` に Pier 固有 DB 名・ファイル名が混入 |
| `python/aci_working_mirror_sync.py:946` | `root / "epo root"` — 存在しないディレクトリ名で判定が常に standalone-skip に落ちる |
| `tests/test_aci_runtime_scan.py:6` | `from common.aci.python.aci_scan import ...` — monorepo パス固定 |
| `tests/test_aci_analyzer_execution.py:6` | `from common.aci.python import aci_analyzer_execution` — 同上 |

### 2.2 Decision

**Domain loader の設計**: ファイル規約ベース動的 discovery を採用する。

採用理由:
- Python entry-point 方式は packaging 整備が必要で過剰
- TOML registry は設定ファイルの追加維持コストが発生する
- 規約ベース（`domains/<id>/python/<id>_domain_rules.py` を自動探索）は:
  - 既存 Pier domain pack の物理配置をそのまま利用できる
  - `domains/custom-template/` が示す慣例と一致する
  - 設定ゼロで追加ドメインを認識できる
  - `--domain-file` による明示パス上書きも同じ関数で吸収できる

```
load_domain_rules(domain_id, domain_file=None)
  core-only → EMPTY_DOMAIN_RULES (変更なし)
  それ以外 →
    1. domain_file が指定されていれば、そのファイルから読む
    2. aci package import: aci.domains.<id>.<id>_domain_rules
    3. ファイル discovery: <aci_root>/domains/<id>/python/<id>_domain_rules.py
    4. 全て失敗 → ValueError (message にパスを案内)
```

ローダーから `PIER_DOMAIN_RULES` モジュールレベル定数と `_PIER_RULES_FILE` を除去する。

**CLI の設計**: `--domain` から `choices=` を除去してフリー文字列にする。
`--domain-file` オプションを追加し `Path` で受け取る。

**Smoke check の設計**: Pier domain は "利用可能なら表示" に変更。
`load_domain_rules("pier")` を try/except で囲み、失敗時は `pier_domain` キーを省略する。
smoke は core-only だけで `ok=True` を返せるようにする。

`detect_repo_root()` のモノレポ前提判定（`ancestor.parent.name == "common"`）を除去する。
`aci_public_smoke.py` は `python/` 直下に置かれているため、`Path(__file__).resolve().parent.parent` が常に ACI root を指す。
`python/aci_domain_contract.py` の存在で確認し、見つからなければ `None` を返す。
この変更により standalone 環境でも正しく repo root を検出できる。

**`LOW_INFO_SCATTERED_LITERALS` の設計**: Pier 固有値（DB 名・CLI フラグ等）を全て削除し、空の frozenset にする。
この定数が generic scan エンジンで参照されていないことを確認済み。
ドメイン固有の noise filter は domain pack 側で持つべき値であり、汎用コアに置かない。

**sample_mode の設計**: `VALID_SAMPLE_MODES` から "pier" を除去し `{"core"}` のみとする。
pier サンプルは pier domain pack が利用可能な場合のみ参照するため、config validation から外す。

**mirror sync の設計**: `"epo root"` の typo を修正し、monorepo 判定ロジックを明確にする。
standalone repo では常に skip が正しい動作なので、判定を `(root / "common" / "aci").exists()` に変更することで monorepo かどうかを正しく判定する。

**テスト import の設計**: `from common.aci.python.*` を `from python.*` または pyproject.toml の package-dir 定義に従った `from aci.*` に修正する。
standalone 状態での動作を保証する。

### 2.3 Rationale

- agent-workflow-policy §3.5「コードハーネス優先」— 自然言語の説明より実行可能なコードで独立性を確保する
- DOMAIN_PACK_EXTENSION_GUIDE.md の Step 4 は現在「add a bounded loader branch in `python/aci_domain_loader.py`」と書いてあり、閉じた分岐追加を前提としている。今回の変更後はこのガイドも更新が必要

### 2.4 Rejected Alternatives

| 代替案 | 却下理由 |
|---|---|
| Python entry-points (`pkg_resources`) | packaging infrastructure が未整備。過剰 |
| TOML domain registry | 設定ファイルの維持コスト。既存 custom-template 慣例と乖離 |
| 「pier を残してガード追加」 | 根本解決にならない。第3ドメイン追加時にまた同じ問題が発生する |

### 2.5 Impact Scope

- ACI standalone の動作: `--domain core-only` は変更なし
- Pier downstream: `--domain pier` は変更なし（発見パスが変わるだけ）
- カスタムドメイン: `--domain myapp --domain-file /path/to/rules.py` で初めて使用可能になる

### 2.6 Completion Conditions

1. `python aci_cli.py smoke` が Pier domain pack なしの環境で `ok=true` を返す
2. `python aci_cli.py smoke` が Pier domain pack ありの環境で `pier_domain` キーを含む
3. `python aci_cli.py scan --target . --domain pier` が従来どおり動作する
4. `python aci_cli.py scan --target . --domain unknownxyz` が適切な ValueError を返す
5. `pytest tests/` が standalone import パスで全て通過する
6. `LOW_INFO_SCATTERED_LITERALS` が空 frozenset になっている
7. `detect_repo_root()` が standalone 環境でモノレポ構造に依存せず ACI root を返す

### 2.7 SSOT Declaration

- domain loader の正本: `python/aci_domain_loader.py`
- domain pack 規約の正本: `DOMAIN_PACK_EXTENSION_GUIDE.md`（今回の変更後に Step 4 を更新）

---

## 3. Preconditions

| Check | Status | Notes |
|---|---|---|
| scope が承認済み | PASS | owner 判断（2026-06-08）: independence workstream CP6 継続、"complete" 撤回承認 |
| 調査完了（Pier 固有箇所の全列挙） | PASS | 本文書「2.1 Background」で記録済み |
| 既存 Pier domain pack ファイルが discovery パスに存在する | PASS | `domains/pier/python/pier_domain_rules.py` 確認済み |
| tests/ の現状 import が失敗することの確認 | 要確認 | standalone 実行時の挙動を pytest で確認する |
| scope_out の文書群（domains/pier/*.md）に変更不要であることの確認 | PASS | 統合 spec は ACI 側の変更と独立 |

---

## 4. Files

| Path | Operation | Purpose |
|---|---|---|
| `python/aci_domain_loader.py` | Modify | 動的 discovery に全面変更。`PIER_DOMAIN_RULES` 定数と `_PIER_RULES_FILE` を除去。`load_domain_rules(domain_id, domain_file=None)` に変更 |
| `python/aci_cli.py` | Modify | `--domain` から `choices=` を除去。`--domain-file` 引数を追加。`scan` コマンドの呼び出し側に `domain_file` を渡す |
| `python/aci_public_smoke.py` | Modify | Pier domain を optional に変更（try/except）。core-only で `ok=True` になるように修正。`detect_repo_root()` のモノレポ前提判定を除去し standalone 対応にする |
| `python/aci_config.py` | Modify | `VALID_SAMPLE_MODES` を `{"core"}` のみに変更。pier の validation を除去 |
| `python/aci_signals.py` | Modify | `LOW_INFO_SCATTERED_LITERALS` を空 frozenset に変更 |
| `python/aci_working_mirror_sync.py` | Modify | `"epo root"` の判定を `"common/aci"` の存在確認に修正 |
| `python/aci_scan.py` | Modify | `scan_target` シグネチャに `domain_file: Path \| None = None` を追加し `load_domain_rules` に渡す |
| `tests/test_aci_runtime_scan.py` | Modify | import パスを standalone 対応に修正 |
| `tests/test_aci_analyzer_execution.py` | Modify | import パスを standalone 対応に修正 |
| `DOMAIN_PACK_EXTENSION_GUIDE.md` | Modify | Step 4「add a bounded loader branch」を「discovery パスに従いファイルを配置する」に更新 |

---

## 5. Acceptance Mapping

| Acceptance ID | Implementation Point | Verification |
|---|---|---|
| A1 | `load_domain_rules("pier")` が pier domain pack なし環境で `ValueError` を返す | `pytest` または手動 |
| A2 | `load_domain_rules("pier")` が `domains/pier/python/pier_domain_rules.py` を自動発見して返す | smoke check |
| A3 | `load_domain_rules("unknownxyz")` が適切な `ValueError` を返す | pytest |
| A4 | `aci smoke` が Pier なしで `ok=true` を返す | CLI 実行 |
| A5 | `aci smoke` が Pier ありで `pier_domain` を含む出力を返す | CLI 実行 |
| A6 | `aci scan --domain pier` が従来と同等の出力を返す | CLI 実行 |
| A7 | `aci scan --domain custom --domain-file /path/to/rules.py` が動作する | CLI 実行 |
| A8 | `LOW_INFO_SCATTERED_LITERALS` が空 frozenset | コードレビュー |
| A9 | `pytest tests/` が全て通過する（standalone import） | pytest |
| A10 | `DOMAIN_PACK_EXTENSION_GUIDE.md` Step 4 が新しい discovery 方式を説明している | 文書レビュー |
| A11 | `detect_repo_root()` がモノレポ構造なし（standalone）でも ACI root を返す | CLI 実行 |

---

## 6. Verification Plan

- planned checks:
  - `python python/aci_cli.py smoke` — Pier なし環境で `ok=true`
  - `python python/aci_cli.py smoke` — Pier あり環境で `pier_domain` キーを確認
  - `python python/aci_cli.py scan --target . --domain pier` — 従来動作確認
  - `python python/aci_cli.py scan --target . --domain unknownxyz` — 適切エラー確認
  - `python python/aci_cli.py scan --target . --domain-file domains/pier/python/pier_domain_rules.py --domain pier` — 明示パスでの動作確認
- planned tests:
  - `pytest tests/test_aci_runtime_scan.py` — standalone import で全テスト通過
  - `pytest tests/test_aci_analyzer_execution.py` — 同上
  - smoke/fixture check が `ok=true` を返すことを自動検証
- evidence surface:
  - CLI 出力の JSON をそのまま acceptance 証跡とする
- 非汚染確認:
  - `core/`, `domains/pier/*.md`, `runtime/`, `report/`, `persistence/` に変更が生じていないことを `git diff --name-only` で確認する
  - `AciDomainRules` および `AciFinding` の dataclass contract に変更がないことをコードレビューで確認する

---

## 7. 作業順序

次の順で進める。各ステップが受け入れ条件を持つ。

1. `python/aci_domain_loader.py` — 動的 discovery に変更（最初に変更し、他の変更の前提にする）
2. `python/aci_scan.py` — `scan_target` に `domain_file` パラメータを追加
3. `python/aci_cli.py` — `--domain` を open-ended に、`--domain-file` を追加
4. `python/aci_public_smoke.py` — Pier optional に変更
5. `python/aci_config.py` — `VALID_SAMPLE_MODES` を `{"core"}` のみに変更
6. `python/aci_signals.py` — `LOW_INFO_SCATTERED_LITERALS` を空に
7. `python/aci_working_mirror_sync.py` — monorepo 判定ロジックを修正
8. `tests/test_aci_runtime_scan.py` — import パスを修正
9. `tests/test_aci_analyzer_execution.py` — import パスを修正
10. `DOMAIN_PACK_EXTENSION_GUIDE.md` — Step 4 の記述を更新
11. 全検証（smoke + pytest）

---

## 8. Idempotency and Side Effects

- Idempotency type: 冪等。同じ変更を再適用しても結果が変わらない
- Writes: `python/` 配下 7 ファイル、`tests/` 配下 2 ファイル、`DOMAIN_PACK_EXTENSION_GUIDE.md`
- External calls: なし（loader 変更による import 探索は副作用なし）
- Retry behavior: ファイル変更は再試行不要
- **Rollback**: 全変更は `git diff` で追跡可能。問題発生時は変更ファイルを個別に `git checkout <file>` で元に戻せる。Step ごとに変更を分けているため部分巻き戻しが可能。`aci_domain_loader.py` だけ戻せば Steps 1〜4 の動作が全て元に戻る（依存の先頭ファイルのため）

---

## 9. Risks

| Risk | Level | Mitigation |
|---|---|---|
| Pier downstream の `load_domain_rules("pier")` 呼び出しが discovery に依存するため、`domains/pier/python/pier_domain_rules.py` が存在しない環境では RuntimeError になる | medium | パッケージとして install した場合は `aci.domains.pier.*` の package import を先に試みる（既存の fallback ロジックを維持） |
| `aci_config.py` の `sample_mode = "pier"` を持つ既存の `aci.example.toml` が validation error になる | low | `aci.example.toml` の `sample_mode` を `"core"` に更新する（scope 内） |
| `tests/` の import パス変更により monorepo 側の CI が壊れる可能性 | low | tests/ は standalone repo の物理正本。monorepo 側の CI は monorepo 側で独自テストを持つべき（scope out） |
| `LOW_INFO_SCATTERED_LITERALS` を空にすることで、generic scan engine に影響する可能性 | low | `aci_scan.py` がこの定数を参照していないことを確認済み。影響なし |
| mirror sync の "epo root" 修正により monorepo 環境での動作が変わる | low | monorepo では `common/aci/` が存在するため、修正後も正しく monorepo mode になる。standalone では引き続き skip |

---

## 10. Amendment 2026-06-08: pier-optional フォローアップ

### 10.1 発見経緯

Steps 1〜10 の実装完了後、ユーザーレビューで以下の2箇所が pier-optional の変更から漏れていたことを確認した。

| 箇所 | 問題 |
|---|---|
| `python/aci_installed_package_verification.py:58` | `load_domain_rules("pier")` を try/except なしで呼び出している。pier なし環境で `installed-package-check` がクラッシュする |
| `python/package_assets/fixtures/expected_smoke_contract.json:5` | `"pier_domain": "pier"` を必須チェックとして含む。pier なし環境で `fixture-check` が失敗する |

### 10.2 Decision

**`aci_installed_package_verification.py` の修正方針**:
`load_domain_rules("pier")` を try/except (ValueError, ImportError) で囲む。
pier が利用可能な場合: 既存どおり `domain_id == "pier"` を検証する（`ok=True/False`）。
pier が利用不可能な場合: pier はオプショナルドメインのため `ok=True` で「pier-domain-not-installed（optional）」として記録する。クラッシュさせない。

**`expected_smoke_contract.json` の修正方針**:
`"pier_domain": "pier"` エントリを削除する。
`aci fixture-check` は `core_only_domain` のみを必須コントラクトとし、pier の有無は問わない。

### 10.3 Impact Scope

- `installed-package-check`: pier なし環境でもクラッシュしなくなる
- `fixture-check`: pier なし環境でも全チェックが通るようになる
- pier あり環境（本リポジトリ）: 既存の動作を維持

### 10.4 Files（Amendment 追加分）

| Path | Operation | Purpose |
|---|---|---|
| `python/aci_installed_package_verification.py` | Modify | pier チェックを try/except で囲み optional に変更 |
| `python/package_assets/fixtures/expected_smoke_contract.json` | Modify | `pier_domain` を必須コントラクトから除去 |

### 10.5 Acceptance Mapping（Amendment 追加分）

| Acceptance ID | Implementation Point | Verification |
|---|---|---|
| A15 | `installed-package-check` が pier なし環境でクラッシュしない | 手動確認（ValueError が発生しないこと） |
| A16 | `fixture-check` が pier なし環境で `ok=true` を返す | `expected_smoke_contract.json` から pier_domain 除去後に確認 |

### 10.6 Completion Conditions（Amendment）

1. `aci_installed_package_verification.py` が pier なし環境で ValueError を出さない
2. `expected_smoke_contract.json` に `pier_domain` が含まれない
3. `aci fixture-check` が pier あり環境でも引き続き `ok=true` を返す

---

## 11. Amendment 2 2026-06-09: 全ファイル調査による追加発見

### 11.1 発見経緯

ユーザー要求「全ファイルを自分で読み全件を見逃しなく確認する」に従い、`python/` 配下の全 Python ファイルおよび `pyproject.toml`、`README.md` を改めて精読した。
Amendment 1（Steps 11-12）でカバーされていない以下の問題を追加発見した。

| # | ファイル | 行 | 種別 | 問題 |
|---|---|---|---|---|
| C-3 | `python/aci_automation.py` | 64-69 | CRITICAL | `_sample_paths()` が pier サンプルパスを常に返す。pier なし環境で `validate_sample_reports()` が `FileNotFoundError` でクラッシュ |
| C-6 | `python/aci_cli.py` | 343 | CRITICAL | `automation-smoke` コマンドが `result["mirror_sync"]` を直接アクセス。standalone mode では `build_public_smoke_result()` が `"mirror_sync"` キーを返さず `"layout_note"` を返すため `KeyError` クラッシュ |
| C-4 | `python/aci_installed_package_verification.py` | 142-144 | CRITICAL | `built_artifact_contract_checks` が pier レポートファイル（`has_pier_report_json`, `has_pier_report_md`）を必須とする。pier なし環境で常に失敗 |
| C-5 | `pyproject.toml` | 25,30-31 | CRITICAL | `packages = ["aci", "aci.domains", "aci.domains.pier"]` — pier が ACI パッケージに物理的に同梱される。「完全汎用」方針違反 |
| H-1 | `python/aci_cli.py` | 57 | HIGH | `if cwd.name == "aci" and cwd.parent.name == "common":` — `_resolve_repo_root()` 内のモノレポ前提チェック（dead code） |
| H-2 | `python/aci_public_smoke.py` | 79 | HIGH | 同パターン。`main()` 内のモノレポ前提チェック（dead code） |
| H-3 | `python/aci_cli.py` | 82 | HIGH | `else "aci-pier-sample-report"` — `choices=["core"]` のため到達不能な dead code |
| M-1 | `python/aci_installed_package_verification.py` | 15-16 | MEDIUM | `_detect_package_root()` 内の `repo_root / "common" / "aci" / "python"` モノレポパス（パスが存在しなければ benign にスルー） |
| M-2 | `python/aci_installed_package_verification.py` | 87-88 | MEDIUM | `_built_artifact_contract_checks()` 内の `repo_root / "common" / "aci" / "pyproject.toml"` モノレポパス（同上） |
| M-3 | `README.md` | 91-95 | MEDIUM | smoke check の説明が `aci core only` と `aci + pier domain` を並記。pier は optional なので記述を修正が必要 |
| L-1 | `domains/pier/python/pier_domain_rules.py` | 13 | LOW | `from ....python.aci_domain_contract import AciDomainRules` — 4段相対インポートは常に失敗（except にフォールバック）。dead 相対インポート |

また Amendment 1 の Step 11 は `aci_installed_package_verification.py:58` のみを対象としているが、同ファイルには上記 C-4・M-1・M-2 の追加問題もある。効率のため Step 11 の scope を拡張し同ファイルの全変更を一括で行う。

### 11.2 Decision

**`pyproject.toml` の変更方針（C-5）**:

pier は optional domain pack として別パッケージで存在するべきで、ACI core に物理同梱しない。
`packages` から `aci.domains` と `aci.domains.pier` を除去し `["aci"]` のみとする。
`package-dir` から `aci.domains` および `aci.domains.pier` のマッピングを除去する。

除去後の動作:
- `pip install aci` → `python/domains/` は含まれない
- `load_domain_rules("pier")` は (1) `aci.domains.pier.*` import 失敗 → (2) `domains/pier/python/pier_domain_rules.py` ファイル探索（開発環境では成功）→ (3) 両方失敗時は `ValueError` を raise
- ACI 単体インストール環境では pier は利用不可（呼び出し元で try/except により optional 扱い）
- pier を別パッケージ（`aci.domains.pier.*` を提供）としてインストールすれば自動的に有効になる

**`aci_automation.py` の変更方針（C-3）**:

`_sample_paths()` の戻り値型を `tuple[Path, ...]` に変更し、core サンプルのみを返す。
`validate_sample_reports()` は core サンプル 1 件だけを検証する。
pier サンプルの検証は pier domain pack 側の責任とし、ACI core では行わない。

**`aci_installed_package_verification.py` の追加変更方針（C-4・M-1・M-2）**:

C-4: `built_artifact_contract_checks` の `has_pier_report_json`・`has_pier_report_md` 変数を削除。`ok` の判定を `has_core_report_json and has_core_report_md` のみとする。
M-1: `_detect_package_root()` から `monorepo_package_root` パスを削除。standalone パスのみで判定する。
M-2: `_built_artifact_contract_checks()` の `pyproject_candidates` から monorepo パスを削除。`repo_root / "pyproject.toml"` のみとする。

**`aci_cli.py` の変更方針（H-1・H-3・C-6）**:

H-1: `_resolve_repo_root()` の `if cwd.name == "aci" and cwd.parent.name == "common":` ブランチを削除。standalone の `return cwd` のみ残す。
H-3: `_sample_asset_relative_path()` の `else "aci-pier-sample-report"` を `"aci-core-sample-report"` に統合し条件分岐を削除する（`choices=["core"]` のため到達不能なため）。
C-6: `automation-smoke` コマンド（:343）の `result["mirror_sync"]` を `result.get("mirror_sync", result.get("layout_note"))` に変更する。standalone mode で `build_public_smoke_result()` が `"mirror_sync"` ではなく `"layout_note"` を返すため `KeyError` が発生する。`smoke` コマンドは `result.pop("mirror_sync", None)` で安全だが `automation-smoke` だけ漏れていた。

**`aci_public_smoke.py` の変更方針（H-2）**:

`main()` の `if cwd.name == "aci" and cwd.parent.name == "common":` ブランチを削除。`repo_root = cwd` のみ残す。

**`README.md` の変更方針（M-3）**:

"aci + pier domain" を smoke check の説明から削除し、pier が optional である旨に変更する。

**`domains/pier/python/pier_domain_rules.py` の変更方針（L-1）**:

`from ....python.aci_domain_contract import AciDomainRules` の dead 相対インポートを削除し、`from aci_domain_contract import AciDomainRules` の単独インポートのみとする。

### 11.3 Files（Amendment 2 追加分）

| Path | Operation | Purpose |
|---|---|---|
| `python/aci_automation.py` | Modify | `_sample_paths()` を core のみ返すよう変更。戻り値型を `tuple[Path, ...]` に変更 |
| `python/aci_installed_package_verification.py` | Modify（Step 11 scope 拡張） | pier load try/except（Step 11）＋ pier report 要求除去（C-4）＋ monorepo パス除去（M-1・M-2） |
| `pyproject.toml` | Modify | `packages` から `aci.domains`, `aci.domains.pier` を除去。`package-dir` から同エントリを除去 |
| `python/aci_cli.py` | Modify | `_resolve_repo_root():57` モノレポチェック削除。`_sample_asset_relative_path():82` dead code 削除。`automation-smoke`:343 `result["mirror_sync"]` → `result.get("mirror_sync", result.get("layout_note"))` |
| `python/aci_public_smoke.py` | Modify | `main():79` モノレポチェック削除 |
| `README.md` | Modify | smoke check 説明を pier optional 表記に修正（91-95行） |
| `domains/pier/python/pier_domain_rules.py` | Modify | dead 相対インポート削除（L-1） |

### 11.3a 設計上の判断（変更しないファイル）

**L-2: `python/domains/pier/` の孤立ファイル**

Step 14 で pyproject.toml から pier パッケージエントリを除去した後、`python/domains/pier/pier_domain_rules.py`・`python/domains/__init__.py`・`python/domains/pier/__init__.py` はソースツリーに残るが、インストールパッケージにも loader の discovery パス（`domains/<id>/python/`）にも含まれない孤立ファイルになる。

判断: **このセッションでは変更しない。** ソースツリーへの留置を許容する。理由: これらのファイルはいずれ pier が独立パッケージ（`aci.domains.pier` を提供する別 pip パッケージ）として分離された時点で正式に移行または削除される。現時点での削除は pier 分離の判断より先走りとなりスコープを超える。

**事後解決 (2026-06-09)**: `python/domains/pier/` 全体を `archive/python-domains-pier/` に移動済み。

**L-3: `python/package_assets/report/examples/aci-pier-sample-report.*`**

pyproject.toml の package-data glob `"package_assets/report/examples/*.json"` は pier サンプルファイルを引き続きインストールパッケージに同梱する。

判断: **このセッションでは変更しない。** data ファイルとしての同梱は機能的に無害。`validate_sample_reports()`（Step 13 で修正）が pier サンプルを参照しなくなるため、自動検証から pier サンプルは除外済み。pier が独立パッケージとして分離される際に package-data glob の精細化（または pier サンプルの別管理）と合わせて対応する。

**事後解決 (2026-06-09)**: `python/package_assets/report/examples/aci-pier-sample-report.*` を `archive/package-assets-pier/` に移動済み。

### 11.4 Acceptance Mapping（Amendment 2 追加分）

| Acceptance ID | Implementation Point | Verification |
|---|---|---|
| A17 | `validate_sample_reports()` が pier サンプルなし環境で `FileNotFoundError` を出さない | 手動確認 |
| A18 | `installed-package-check` の `built_contract.report_asset_rule` が pier なし環境で `ok=True` | 手動確認 |
| A19 | `pyproject.toml` の `packages` が `["aci"]` のみ | コードレビュー |
| A20 | `_resolve_repo_root()` がモノレポチェックなしで動作する | CLI 実行 |
| A21 | `_sample_asset_relative_path()` が `choices=["core"]` と整合した dead-code-free な実装になっている | コードレビュー |
| A22 | `aci_public_smoke.py main()` がモノレポチェックなしで動作する | CLI 実行 |
| A23 | `README.md` の smoke check 説明が pier optional を明記している | 文書レビュー |
| A24 | `domains/pier/python/pier_domain_rules.py` の dead 相対インポートが除去されている | コードレビュー |
| A25 | `aci automation-smoke` が standalone mode で `KeyError` を出さない | CLI 実行 |

### 11.5 Completion Conditions（Amendment 2）

1. pier なし環境で `aci automation-smoke` が `FileNotFoundError` を出さない
2. pier なし環境で `aci installed-package-check` の全チェックが `ok=true` を返す
3. `pyproject.toml` が pier 関連パッケージエントリを含まない
4. `aci_cli.py` の `_resolve_repo_root()`、`_sample_asset_relative_path()`、`automation-smoke` コマンドにモノレポ前提コードおよびキー直接アクセスが残らない
5. `aci_public_smoke.py main()` にモノレポ前提コードが残らない
6. `README.md` の smoke check 説明が pier を必須前提として記載しない
7. `domains/pier/python/pier_domain_rules.py` の dead 相対インポートが除去されている
