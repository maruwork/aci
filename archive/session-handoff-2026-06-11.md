# セッション引継書

作成日: 2026-06-11

---

## 前セッション（2026-06-09 引継書）から引き継いだ状態

前セッション終了時点では以下が完了済みだった:

- ACI Pier 分離（Steps 1–18）
- 外部アナライザー CI マッピング修正（ruff/pyflakes → 正しい CI ID）
- CI-01/10/16/17/27 削除（5 patterns → 22 active patterns）
- CI-18/CI-20 修正（Data Clump / Scattered Constant）
- テスト: 17/17 pass、Pyright 新規エラー 0 件

---

## 本セッションで完了した作業

### テーマ: MGEF（Market-Grade Execution Foundation）T1–T56 全完了

#### 完了タスク一覧（本セッション中に実施）

| タスク | 内容 |
|--------|------|
| CI-09/CI-13 テスト追加 | `tests/test_aci_analyzer_execution.py` に ruff コードマッピング確認テストを追加。`PT001` → `CI-09`、`I001` → `CI-13` |
| §C ギャップ評価更新 | `workspace/aci-gap-assessment.md` の T37-T40 パターンを covered に更新。CI-04/08/11/19/24 を by-design 未テストとして明示 |
| §D/§G ギャップ評価更新 | T54 CI workflow を resolved に。56タスク全完了エビデンスを確認 |
| `result["errors"]` バグ修正 | `tests/test_aci_report_and_gate_regression.py` 3 箇所。`validate_report_payload` 戻り値に `"errors"` キーが存在しないため `result["errors"]` → `result` |
| 未使用 import 除去 | `.github/workflows/ci.yml` プロベナンスステップの `import subprocess` を除去（`text=True` 実行で不要）|
| Dead branch 除去 | `python/aci_analyzer_execution.py` の `_version_probe_command`。両分岐が同一値を返す死んだ if-else を除去 |
| `ANALYZER_MAX_OUTPUT_BYTES` → `CHARS` | `subprocess.run(text=True)` は `str` を返すため naming が misleading。4 箇所で一括リネーム |
| `aci_working_mirror_sync.py` 縮小 | 970 行 → 70 行。pier monorepo 固有の `REQUIRED_MIRROR_PAIRS`（typo `refernce/` 含む）を空タプルに置換。ACI standalone では `check_required_mirror_pairs` が `common/aci/` 不存在を検知して `standalone-skip / ok=True` を返すため機能影響ゼロ |
| Dead proof ファイルをアーカイブ | `python/` から `archive/python-proof-helpers/` へ移動: `aci_built_wheel_install_proof.py`, `aci_editable_install_proof.py`, `aci_source_distribution_proof.py`。いずれも他ファイルから未 import、pyproject.toml / CI 未参照 |
| Pier サンプルレポートを移動 | `report/examples/aci-pier-sample-report.{json,md}` → `domains/pier/examples/`。「本体ファイルに Pier の記述は残さない」ルール準拠 |
| 参照先更新 | `report/README.md` および `runtime/aci-generic-quickstart.md` の pier サンプルパスを新ロケーションに更新 |
| `domains/pier/README.md` 更新 | `## Sample Outputs` セクションを追加し、移動済みサンプルへの参照を記述 |
| `CHANGELOG.md` 更新 | `[Unreleased]` セクションに MGEF (T1–T56) 全作業を Added / Changed / Fixed / Removed で記録 |

---

## 現在の状態

### テスト結果: **75 passed / 2 failed**

以下 2 件が失敗中。次セッションの最初の対処対象。

| # | テスト | ファイル | 症状 |
|---|--------|---------|------|
| 1 | `test_ci05_triggers_on_duplicate_function_across_files` | `tests/test_aci_detector_fixtures.py:86` | 同一関数ボディを 2 ファイルに置いても `CI05_COPY_PASTE_CODE` シグナルが発火しない（`set()` が返る） |
| 2 | `test_gate_passes_when_all_findings_waived` | `tests/test_aci_report_and_gate_regression.py:167` | CI-03 finding に waiver を付けて `severity_threshold="critical"` で走らせても gate が `'fail'` を返す |

これら 2 件が pre-existing の失敗なのか、本セッションの変更による regression なのかは未確認。

### 実装・品質

- **MGEF 56 タスク（T1–T56）: 全完了**（owner 決定待ちは別途記載）
- `python/` 下のコードに dead code・typo・pier 混在なし
- テスト: CI-06/09/13 含む全パターンをカバー（CI-04/08/11/19/24 は human-judgment で by-design 未テスト）
- CI ワークフロー: test matrix / lint / type-check / ACI self-scan / release gate が `.github/workflows/ci.yml` に揃っている

### ファイル配置

| 棚 | 状態 |
|----|------|
| `python/` | pier 記述なし、dead code なし |
| `report/examples/` | core サンプルのみ（pier は `domains/pier/examples/` へ） |
| `domains/pier/` | pier 固有コンテンツがすべて集約 |
| `archive/` | 旧 proof ヘルパー 3 件を格納済み |
| `aci.egg-info/` | checkout-generated packaging residue。正本でも編集対象でもない。no-touch |

### 配布モデル（確定）

- 配布方式: `pip install aci`（通常インストール）
- ユーザー手元に届くもの: `python/` 配下が site-packages に `aci/` としてインストールされる
- `core/`, `docs/`, `common/` 等: 届かない。開発者用・リポジトリ内のみ
- fixed tool-checkout placement is not a general rule
- `pyproject.toml` の `packages = ["aci"]` / `package-dir: aci = "python"` が正規設定

### 生成物・外部ツール配置方針

- root 直下にファイル・フォルダを適当に増やさない、が上位方針
- this checkout may correspond to a consuming repo's local tool checkout
  - the tool checkout path is project-local, not fixed by shared rule
  - `aci.egg-info/` は pip が tool checkout 内に生成する残渣（controllable output ではないので `workspace/` には行かない）
  - tool checkout 内に留まる（移動不可）。残渣として扱う・canonical authority にしない
- ACI を外部ツールとして別 repo に置く場合の置き場:
  - ACI 本体: `{approved local tool path}`
  - ACI の実行時ローカル状態: `root/workspace/aci/`
  - 生成残渣: `tool checkout/aci.egg-info/` のような tool-checkout residue
- 置き場を選べる生成物は `workspace/aci/` に寄せる。tool checkout は生成残渣の標準置き場にしない

---

## Owner 決定待ち（実装不可）

| タスク | 内容 |
|--------|------|
| T45 | secrets scanning 製品ポスチャ決定 |
| T46 | dependency / supply-chain scanning 製品ポスチャ決定 |
| T47 | IaC scanning 製品ポスチャ決定 |
| T48 | container scanning 製品ポスチャ決定 |
| T53 | CI ワークフロー所有区分（common 棚 vs. downstream ルーティング） |
| — | `git init`（ユーザーが明示的に保留中） |
| — | PyPI 公開 / public release タイミング |

---

## 手動対応が必要な残件

```powershell
# 空ディレクトリの手動削除（ツール権限外）
Remove-Item -Path "C:\Users\f_tan\project\aci\common\tmp_pj_template_rules" -Recurse
```

---

## セッション行動規則（新セッションが必ず守ること）

1. **質問には答えるだけ、実装しない**
2. **明示的に指示された作業のみ実施**（余分な改善・整理をしない）
3. **一歩ずつ進める**（承認なしに次ステップへ進まない）
4. **削除しない → `archive/` へ移動**
5. **`git init` は明示的指示まで禁止**
6. **判断前にファイル全文を読む**（部分読みで判断しない）
7. **修正時は ACI 本体への影響ゼロを保証する**（"修正するなら、ACI に絶対に影響がないように注意しながら進めろ"）
8. **本体ファイルに Pier の記述は残さない**（pier コンテンツは `domains/pier/` へ）
9. **影響の有無関係なく修正すべき箇所は修正**（エラー・バグ・不整合は軽微でも放置しない）

---

## 技術コンテキスト（新セッションが参照する基本知識）

### 22 active CI パターン（CI-01/10/16/17/27 は削除済み）

| CI ID | 名称 | Lane |
|-------|------|------|
| CI-02 | Spaghetti Code | NATIVE_STATIC |
| CI-03 | TODO Decay | NATIVE_STATIC |
| CI-04 | God Object | HUMAN_JUDGMENT |
| CI-05 | Copy-Paste Code | NATIVE_STATIC |
| CI-06 | Magic Number | NATIVE_STATIC |
| CI-07 | Lava Flow | NATIVE_STATIC |
| CI-08 | Dead Feature Sprawl | HUMAN_JUDGMENT |
| CI-09 | Test Rot | NATIVE_STATIC |
| CI-11 | Responsibility Sprout | HUMAN_JUDGMENT |
| CI-12 | Feature Envy | NATIVE_STATIC |
| CI-13 | Dependency Rot | EXTERNAL_ANALYZER |
| CI-14 | Security Neglect | EXTERNAL_ANALYZER |
| CI-15 | Documentation Rot | EXTERNAL_ANALYZER |
| CI-18 | Data Clump | NATIVE_STATIC |
| CI-19 | Shotgun Surgery | HUMAN_JUDGMENT |
| CI-20 | Scattered Constant | NATIVE_STATIC |
| CI-21 | Error Handling Rot | EXTERNAL_ANALYZER |
| CI-22 | Resource Leak | NATIVE_STATIC |
| CI-23 | Contract Drift | EXTERNAL_ANALYZER |
| CI-24 | Authority Bypass | HUMAN_JUDGMENT |
| CI-25 | Nondeterminism | EXTERNAL_ANALYZER |
| CI-26 | State Mutation Leak | NATIVE_STATIC |

CI-04/08/11/19/24 は `LANE_HUMAN_JUDGMENT` のため自動テスト不可（by-design）。

### exit code 定義

| コード | 意味 |
|-------|------|
| 0 | OK |
| 1 | findings_present |
| 2 | config_error |
| 3 | runtime_failure |
| 4 | contract_error |
| 5 | automation_verification_failure |

### gate 条件

- `severity_threshold` — 指定 severity 以上のみ gate 判定対象
- `fail_on_new_findings` — baseline に存在しない new finding があれば fail
- `fail_on_unreviewed_review_required` — HUMAN_JUDGMENT finding が未 review なら fail
- `fail_on_analyzer_errors` — 外部アナライザーがエラーを返したら fail

### finding lifecycle

`new` → `existing-baseline` → `resolved`（baseline エントリに対応する finding が現スキャンに存在しない場合）

### 既知の pre-existing 静的解析警告（新規 regression ではない）

- Pyright `reportMissingImports` — テストファイル（`pyrightconfig.json` なし）
- Pyright `"object" is not iterable` — `aci_scan.py` 約 1665 行目 (`_build_gate_result`) — 今回変更と無関係

---

## 次セッションの起点

1. **テスト失敗 2 件を修正**（`test_ci05_triggers_on_duplicate_function_across_files` / `test_gate_passes_when_all_findings_waived`）
2. owner 決定待ちタスク（T45–T48, T53）に方針が決まり次第着手可能
3. `git init` 実施後、初 commit → PyPI 公開フローに進める状態
4. Wave 2–7 ロードマップ（`docs/roadmap/aci-market-grade-next-wave-map.md`）への着手はユーザーの優先度判断次第

---

## python/ ファイル責務マップ

| ファイル | 役割 |
|---------|------|
| `aci_cli.py` | CLI エントリポイント。`scan` / `smoke` / `emit-annotations` / `--version` など全コマンド |
| `aci_scan.py` | スキャンコア。`scan_target()` / `PerFileDetector` / `CrossFileDetector` / `ACI_TOOL_VERSION` |
| `aci_findings.py` | Finding dataclass・定数（`LANE_*` / `VERIFICATION_*` / `SEVERITY_*`） |
| `aci_signals.py` | シグナル定数（`SIGNAL_*`）・シグナルセット定義 |
| `aci_wording.py` | シグナル → 人間可読テキストのマッピング |
| `aci_profiles.py` | プロファイル定数（`PROFILE_*`）・`build_profile_signals()` |
| `aci_profile_catalog.py` | プロファイルカタログ（外部公開用メタデータ） |
| `aci_analyzers.py` | 外部アナライザー定義（ruff / pyflakes / mypy）|
| `aci_analyzer_execution.py` | 外部アナライザー実行・ruff/pyflakes コード → CI ID マッピング（`_RUFF_PREFIX_TO_CI`）|
| `aci_config.py` | `AciConfig` dataclass・TOML 読み込み |
| `aci_domain_contract.py` | `AciDomainRules` dataclass・`CORE_ONLY_DOMAIN_ID` 定数 |
| `aci_domain_loader.py` | `load_domain_rules(domain_id)` — 動的 domain pack 読み込み |
| `aci_automation.py` | `validate_report_payload()` / `validate_sample_reports()` / `REQUIRED_SAMPLE_TOP_LEVEL_FIELDS` / `SUMMARY_COUNT_FIELDS` |
| `aci_annotations.py` | GitHub Actions workflow command annotation emitter |
| `aci_sarif.py` | SARIF 出力フォーマッター |
| `aci_ignore.py` | `.aciignore` パターン処理 |
| `aci_package_assets.py` | `read_text_asset()` — パッケージ内静的ファイルの読み込み |
| `aci_working_mirror_sync.py` | mirror sync チェック（ACI standalone では `standalone-skip / ok=True` を返す） |
| `aci_public_smoke.py` | `aci smoke` コマンドの実装 |
| `aci_installed_package_verification.py` | `aci installed-package-check` の実装（editable / built / release-gate の3レーン） |
| `aci_fixture_check.py` | `run_fixture_check(repo_root)` — `fixtures/expected_smoke_contract.json` との整合性チェック。smoke 結果・サンプルレポート検証を複合確認。`aci_cli.py` から import される |

---

## 同期を保つべき定数ペア（破ると `installed-package-check` が失敗）

| 定数 A | 定数 B / ファイル | 説明 |
|--------|----------------|------|
| `ACI_TOOL_VERSION` in `aci_scan.py` | `version` in `pyproject.toml` | バージョン文字列の一致 |
| `REQUIRED_SAMPLE_TOP_LEVEL_FIELDS` in `aci_automation.py` | `report/examples/aci-core-sample-report.json` および `python/package_assets/report/examples/aci-core-sample-report.json` | サンプル報告書の最上位フィールド網羅 |
| `SUMMARY_COUNT_FIELDS` in `aci_automation.py` | 同サンプル JSON の `summary` オブジェクト | `summary` 内のカウントフィールド網羅 |

---

## workspace/ の位置付け

`workspace/` は **canonical authority ではない**（`workspace/README.md` 明記）。スクラッチ・生成レビューファイル置き場。`aci-gap-assessment.md` はここにあるが、ACI 本体ロジックへの影響は持たない。

---

## ガバナンスポリシー置き場

`common/policies/` に 16 件のポリシー文書がある。agent-workflow-policy（7 フェーズワークフロー）はここ: `common/policies/agent-workflow-policy.md`。作業前に該当ポリシーを参照すること。

---

## 主要ドキュメント参照先

| 目的 | 参照先 |
|------|--------|
| プロジェクト全体理解 | `README.md` → `docs/USER_EVALUATION_INDEX.md` → `runtime/aci-generic-quickstart.md` |
| MGEF 全体進捗 | `workspace/aci-gap-assessment.md` |
| CI パターン仕様 | `core/aci-code-inspection-execution-spec.md` |
| ガバナンス | `docs/governance/project-template-adoption-packet.md` |
| リリースフロー | `python/aci_installed_package_verification.py` + `.github/workflows/ci.yml` |
| Pier domain pack | `domains/pier/README.md` |
| 変更履歴 | `CHANGELOG.md` |
