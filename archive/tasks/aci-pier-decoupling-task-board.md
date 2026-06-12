# ACI Pier Decoupling Task Board

Status: Complete

## Workstream

- 親workstream: ACI independence
- 親チェックポイント: CP6（コード結合除去）
- 設計: `design/aci-pier-decoupling-implementation-design.md`
- ゴール: `roadmap/aci-independence-goal.md`
- チェックポイント: `roadmap/aci-independence-checkpoints.md`

## Reference

- Design: `design/aci-pier-decoupling-implementation-design.md`
- Prior independence work: `roadmap/aci-independence-goal.md`

## Shared Defaults

以下は全タスク共通。個別タスクで明示した場合はそちらが優先する。

| 項目 | 値 |
|---|---|
| active bundle id | `aci-pier-decoupling` |
| active bundle type | `implementation` |
| 親テーマ | ACI independence |
| 親チェックポイント | CP6（コード結合除去） |
| 成功主語 | ACI |
| 完了報告主語 | ACI |
| 読んでよい場所 | `python/`, `tests/`, `DOMAIN_PACK_EXTENSION_GUIDE.md`, `domains/`, `core/` |
| 今回やらない範囲（全タスク共通） | `AciDomainRules` / `AciFinding` contract の変更、CI catalog（CI-01〜CI-27）の変更、`domains/pier/*.md` の変更、report/persistence/integrations 配下の変更、新しい domain pack の実装 |
| 触ってはいけない場所 | `archive/`, `.pytest_cache/`, `build/`, `aci.egg-info/`, `domains/pier/*.md`, `runtime/`, `report/`, `persistence/` |
| 差し戻し条件 | 既存の `scan_target()` または `load_domain_rules()` の公開インターフェースが壊れる変更 |
| 人判断へ上げる条件 | `AciDomainRules` dataclass の contract 変更、`AciFinding` contract の変更 |
| 証拠 | CLI 出力・pytest 出力をそのまま証跡とする |
| 結果の記録先 | 本ボードの Status 欄 |
| 最終判定者 | ACI maintainer |

## Tasks

### Step 1: domain loader を動的 discovery に変更

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-01 |
| 目的 | domain pack を open-ended にするためのコアとなる変更 |
| このタスクが必要な理由 | loader が pier を閉じた分岐で扱っているため第3ドメインを追加できない |
| 着手条件 | なし（先頭タスク） |
| 入力 | `python/aci_domain_loader.py`（現状） |
| 書いてよい場所 | `python/aci_domain_loader.py` のみ |
| やること | `PIER_DOMAIN_RULES` 定数・`_PIER_RULES_FILE` 定数を除去。`_discover_domain_file(domain_id)` を追加。`load_domain_rules(domain_id, domain_file=None)` に変更し閉じた pier 分岐を除去 |
| 期待する出力 | pier 分岐のない動的 discovery 関数 |
| 合格条件 | `load_domain_rules("pier")` が `domains/pier/python/pier_domain_rules.py` を自動発見して返す。`load_domain_rules("unknownxyz")` が ValueError を返す |
| 失敗条件 | import 時に `PIER_DOMAIN_RULES` を参照する既存コードが壊れる |
| 停止条件 | `aci.domains.pier.*` package import の副作用が予期しない場合 |
| Status | done |

### Step 2: scan_target に domain_file パラメータを追加

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-02 |
| 目的 | CLI から明示パスを loader に渡せるようにする |
| このタスクが必要な理由 | scan_target が domain_file を受け取らないと CLI の --domain-file が機能しない |
| 着手条件 | Step 1 完了 |
| 入力 | `python/aci_scan.py`（現状） |
| 書いてよい場所 | `python/aci_scan.py` のみ |
| やること | `scan_target(... , domain_file: Path \| None = None)` を追加し load_domain_rules に渡す |
| 期待する出力 | `domain_file` を受け付ける scan_target シグネチャ |
| 合格条件 | `scan_target()` が `domain_file` を load_domain_rules に渡す |
| 失敗条件 | 既存の `scan_target()` 呼び出し元が壊れる |
| 停止条件 | なし |
| Status | done |

### Step 3: CLI を open-ended domain に変更

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-03 |
| 目的 | CLI が pier を列挙しないようにする |
| このタスクが必要な理由 | `choices=["core-only", "pier"]` が第3ドメインを受け付けない |
| 着手条件 | Step 1・Step 2 完了 |
| 入力 | `python/aci_cli.py`（現状） |
| 書いてよい場所 | `python/aci_cli.py` のみ |
| やること | `--domain` から `choices=` を除去。`--domain-file` 引数（Path）を追加。scan コマンドが `domain_file` を渡す |
| 期待する出力 | 任意の domain 文字列と --domain-file を受け付ける CLI |
| 合格条件 | `aci scan --domain pier` が動作する。`aci scan --domain custom --domain-file /path/rules.py` が動作する |
| 失敗条件 | `--domain` choices 除去で既存の argparse help が壊れる |
| 停止条件 | なし |
| Status | done |

### Step 4: smoke check を Pier optional に変更 + detect_repo_root standalone 対応

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-04 |
| 目的 | Pier domain pack なしで smoke が通るようにする。かつ detect_repo_root() のモノレポ前提を除去する |
| このタスクが必要な理由 | `load_domain_rules("pier")` が smoke を Pier 必須にしている。`detect_repo_root()` がモノレポ構造前提のため standalone 環境で誤検出する |
| 着手条件 | Step 1 完了 |
| 入力 | `python/aci_public_smoke.py`（現状） |
| 書いてよい場所 | `python/aci_public_smoke.py` のみ |
| やること | (1) `load_domain_rules("pier")` を try/except で囲む。失敗時は `pier_domain` キーを省略。core-only で `ok=True` を返せるようにする。(2) `detect_repo_root()` のモノレポ前提判定（`ancestor.parent.name == "common"`）を除去し、`Path(__file__).resolve().parent.parent` を ACI root として使用する（`python/aci_domain_contract.py` の存在で確認） |
| 期待する出力 | core-only でも `ok=true` を返す smoke。standalone 環境で正しく ACI root を返す detect_repo_root() |
| 合格条件 | Pier なし環境で `aci smoke` が `ok=true` を返す。detect_repo_root() がモノレポ構造なしでも ACI root を返す |
| 失敗条件 | smoke が core-only で `ok=false` を返す。detect_repo_root() が None を返す |
| 停止条件 | detect_repo_root() の呼び出し元が複数あり変更範囲が `aci_public_smoke.py` を超える場合は人判断へ上げる |
| Status | done |

### Step 5: config の sample_mode から pier を除去

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-05 |
| 目的 | config validation から pier 固有の enum を除去する |
| このタスクが必要な理由 | `VALID_SAMPLE_MODES = {"core", "pier"}` が pier を必須列挙している |
| 着手条件 | なし（独立） |
| 入力 | `python/aci_config.py`（現状） |
| 書いてよい場所 | `python/aci_config.py` のみ |
| やること | `VALID_SAMPLE_MODES = {"core"}` のみに変更 |
| 期待する出力 | `{"core"}` のみの VALID_SAMPLE_MODES |
| 合格条件 | `VALID_SAMPLE_MODES` に "pier" が含まれない |
| 失敗条件 | なし |
| 停止条件 | `aci.example.toml` に `sample_mode = "pier"` が残っている場合は scope 内で同時修正する |
| Status | done |

### Step 6: LOW_INFO_SCATTERED_LITERALS を空に

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-06 |
| 目的 | aci_signals.py から Pier 固有の noise filter 値を除去する |
| このタスクが必要な理由 | DB 名・CLI フラグ等の Pier 固有値が generic core に混入している |
| 着手条件 | なし（独立） |
| 入力 | `python/aci_signals.py`（現状） |
| 書いてよい場所 | `python/aci_signals.py` のみ |
| やること | `LOW_INFO_SCATTERED_LITERALS = frozenset()` に変更 |
| 期待する出力 | 空 frozenset |
| 合格条件 | `LOW_INFO_SCATTERED_LITERALS` が空 frozenset |
| 失敗条件 | `aci_scan.py` がこの定数を参照していて scan 結果が変わる（事前確認済み：参照なし） |
| 停止条件 | なし |
| Status | done |

### Step 7: mirror sync の monorepo 判定を修正

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-07 |
| 目的 | `aci_working_mirror_sync.py` の typo を修正し判定を正しくする |
| このタスクが必要な理由 | `root / "epo root"` は存在しないディレクトリ名のため常に standalone-skip に落ちる |
| 着手条件 | なし（独立） |
| 入力 | `python/aci_working_mirror_sync.py`（現状） |
| 書いてよい場所 | `python/aci_working_mirror_sync.py` のみ |
| やること | `root / "epo root"` の判定を `(root / "common" / "aci").exists()` に変更 |
| 期待する出力 | monorepo/standalone を正しく判定する条件式 |
| 合格条件 | standalone repo で mirror sync が正しく skip する |
| 失敗条件 | monorepo 環境（`common/aci/` あり）で skip になる |
| 停止条件 | 他の monorepo 判定箇所に予期しない連鎖がある場合 |
| Status | done |

### Step 8: テスト import パスを standalone 対応に

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-08 |
| 目的 | テストを standalone 環境で動作させる |
| このタスクが必要な理由 | `from common.aci.python.*` は monorepo パス固定で standalone では動作しない |
| 着手条件 | なし（独立） |
| 入力 | `tests/test_aci_runtime_scan.py`, `tests/test_aci_analyzer_execution.py`（現状） |
| 書いてよい場所 | `tests/test_aci_runtime_scan.py`, `tests/test_aci_analyzer_execution.py` のみ |
| やること | `from common.aci.python.*` → pyproject.toml の package-dir 定義に従った standalone パスに修正 |
| 期待する出力 | standalone 環境で動作する import 文 |
| 合格条件 | `pytest tests/` が standalone import で全て通過する |
| 失敗条件 | import が解決できない |
| 停止条件 | pyproject.toml の package-dir 設定と矛盾する場合は設定を確認して人判断へ上げる |
| Status | done |

### Step 9: DOMAIN_PACK_EXTENSION_GUIDE を更新

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-09 |
| 目的 | extension guide が discovery 方式を正しく説明するようにする |
| このタスクが必要な理由 | Step 4「add a bounded loader branch」は閉じた分岐追加を前提としており新方式と矛盾する |
| 着手条件 | Step 1 完了（loader 設計確定後） |
| 入力 | `DOMAIN_PACK_EXTENSION_GUIDE.md`（現状） |
| 書いてよい場所 | `DOMAIN_PACK_EXTENSION_GUIDE.md` のみ |
| やること | Step 4 の記述を「discovery パスにファイルを配置する」方式の説明に更新 |
| 期待する出力 | 新 discovery 方式と一致した Step 4 説明 |
| 合格条件 | Step 4 が `domains/<id>/python/<id>_domain_rules.py` の配置を説明している |
| 失敗条件 | なし |
| 停止条件 | なし |
| Status | done |

### Step 10: 全検証

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-10 |
| 目的 | Step 1〜9 の acceptance criteria を一括確認する |
| このタスクが必要な理由 | 個別 step の合格確認では回帰を見落とす可能性がある |
| 着手条件 | Step 1〜9 全完了 |
| 入力 | 実装後の全ファイル |
| 書いてよい場所 | なし（read-only 確認） |
| やること | `design/aci-pier-decoupling-implementation-design.md §5` の A1〜A10 を一括確認 |
| 期待する出力 | A1〜A10 全 PASS の確認記録 |
| 合格条件 | A1〜A10 全通過 |
| 失敗条件 | いずれかの acceptance criterion が未達 |
| 停止条件 | A1〜A10 以外の regression が見つかった場合は人判断へ上げる |
| Status | done |

### Step 11: aci_installed_package_verification.py の pier 結合を全て除去

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-11 |
| 目的 | pier なし環境で `installed-package-check` がクラッシュ・失敗しないようにする（Amendment 2 で scope 拡張） |
| このタスクが必要な理由 | (1) `load_domain_rules("pier")` が try/except なし（:58）。(2) `built_artifact_contract_checks` が pier レポートを必須とする（:142-144）。(3) monorepo パスが stale code として残存（:15-16, :87-88） |
| 着手条件 | Step 1 完了（load_domain_rules の新仕様確定済み）|
| 入力 | `python/aci_installed_package_verification.py`（現状） |
| 書いてよい場所 | `python/aci_installed_package_verification.py` のみ |
| やること | (1) `:58` — `load_domain_rules("pier")` を try/except (ValueError, ImportError) で囲む。pier 利用可能時: 既存 ok 判定維持。pier 利用不可時: `ok=True`, `actual="not-installed (optional)"` で記録。(2) `:142-144` — `has_pier_report_json`・`has_pier_report_md` 変数を削除し `ok` 判定を `has_core_report_json and has_core_report_md` のみとする。(3) `:15-16` — `_detect_package_root()` の `monorepo_package_root` パスを削除。(4) `:87-88` — `pyproject_candidates` の monorepo パスを削除 |
| 期待する出力 | pier なし・monorepo 前提なしで動作する installed-package-check |
| 合格条件 | pier あり環境で `ok=True` かつ `actual == "pier"` (A15)。pier なし環境で ValueError が発生しない (A15)。`built_contract.report_asset_rule` が pier なし環境で `ok=True` (A18) |
| 失敗条件 | pier あり環境で `ok` が False になる |
| 停止条件 | `_editable_install_checks` の構造変更が必要になる場合は人判断へ上げる |
| Status | done |

### Step 12: expected_smoke_contract.json から pier_domain を除去

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-12 |
| 目的 | `fixture-check` が pier なし環境でも `ok=true` を返すようにする |
| このタスクが必要な理由 | `pier_domain` が必須コントラクトに含まれており、pier なし環境で `fixture-check` が失敗する |
| 着手条件 | なし（独立） |
| 入力 | `python/package_assets/fixtures/expected_smoke_contract.json`（現状） |
| 書いてよい場所 | `python/package_assets/fixtures/expected_smoke_contract.json` のみ |
| やること | `"pier_domain": "pier"` エントリを `mode_checks` から削除する |
| 期待する出力 | `core_only_domain` のみを含む `mode_checks` コントラクト |
| 合格条件 | `aci fixture-check` が pier あり・なし両環境で `ok=true` を返す |
| 失敗条件 | `core_only_domain` チェックが消える |
| 停止条件 | なし |
| Status | done |

### Step 13: aci_automation.py の pier サンプル依存を除去

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-13 |
| 目的 | pier なし環境で `validate_sample_reports()` が `FileNotFoundError` を出さないようにする |
| このタスクが必要な理由 | `_sample_paths()` が pier サンプルパスを常に返しており、pier なし環境でクラッシュする |
| 着手条件 | なし（独立） |
| 入力 | `python/aci_automation.py`（現状） |
| 書いてよい場所 | `python/aci_automation.py` のみ |
| やること | `_sample_paths()` の戻り値を core サンプルパス 1 件のみに変更。戻り値型を `tuple[Path, ...]` に変更。pier サンプルパスの行を削除 |
| 期待する出力 | core サンプルのみを返す `_sample_paths()` |
| 合格条件 | pier なし環境で `validate_sample_reports()` が `FileNotFoundError` を出さない (A17) |
| 失敗条件 | core サンプル検証が消える |
| 停止条件 | なし |
| Status | done |

### Step 14: pyproject.toml から pier パッケージエントリを除去

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-14 |
| 目的 | ACI コアパッケージから pier を物理的に切り離す |
| このタスクが必要な理由 | `packages = ["aci", "aci.domains", "aci.domains.pier"]` により pier が ACI パッケージに同梱されており「完全汎用」方針に違反する |
| 着手条件 | なし（独立） |
| 入力 | `pyproject.toml`（現状） |
| 書いてよい場所 | `pyproject.toml` のみ |
| やること | `[tool.setuptools]` の `packages` を `["aci"]` のみに変更。`[tool.setuptools.package-dir]` から `"aci.domains"` と `"aci.domains.pier"` のエントリを削除 |
| 期待する出力 | `packages = ["aci"]` のみ、`package-dir` に `aci = "python"` のみ含む pyproject.toml |
| 合格条件 | `pyproject.toml` に pier 関連パッケージエントリが含まれない (A19)。pier domain pack の動的探索（`domains/pier/python/pier_domain_rules.py`）は引き続き機能する |
| 失敗条件 | `aci` パッケージ自体が機能しなくなる |
| 停止条件 | パッケージビルドに影響する他の依存が見つかった場合は人判断へ上げる |
| Status | pending |

### Step 15: aci_cli.py のモノレポチェック・dead code・automation-smoke KeyError を除去

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-15 |
| 目的 | `_resolve_repo_root()` のモノレポ前提コードと `_sample_asset_relative_path()` の dead code を除去し、`automation-smoke` コマンドの KeyError クラッシュを修正する |
| このタスクが必要な理由 | (1) `cwd.parent.name == "common"` チェック（:57）が stale dead code。(2) `else "aci-pier-sample-report"`（:82）が到達不能 dead code。(3) `automation-smoke` コマンド（:343）が `result["mirror_sync"]` を直接アクセスしており、standalone mode（`build_public_smoke_result()` が `"mirror_sync"` ではなく `"layout_note"` を返す）で `KeyError` クラッシュ |
| 着手条件 | Step 3 完了（`choices=["core"]` 確定済み） |
| 入力 | `python/aci_cli.py`（現状） |
| 書いてよい場所 | `python/aci_cli.py` のみ |
| やること | (1) `:57` — `if cwd.name == "aci" and cwd.parent.name == "common": return cwd.parent.parent` ブランチを削除し `return cwd` のみ残す。(2) `:82` — `else "aci-pier-sample-report"` 条件式を削除し `name = "aci-core-sample-report"` の単純代入に変更。(3) `:343` — `"mirror_sync": result["mirror_sync"]` を `"mirror_sync": result.get("mirror_sync", result.get("layout_note"))` に変更 |
| 期待する出力 | モノレポ前提コードのない `_resolve_repo_root()`。pier dead code のない `_sample_asset_relative_path()`。standalone mode でクラッシュしない `automation-smoke` |
| 合格条件 | `_resolve_repo_root()` にモノレポチェックが残らない (A20)。`_sample_asset_relative_path()` が dead code を持たない (A21)。`aci automation-smoke` が standalone mode で `KeyError` を出さない (A25) |
| 失敗条件 | `_resolve_repo_root()` が None を返す。`automation-smoke` が monorepo 環境で mirror_sync を返さなくなる |
| 停止条件 | なし |
| Status | done |

### Step 16: aci_public_smoke.py の main() からモノレポチェックを除去

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-16 |
| 目的 | `main()` のモノレポ前提コードを除去する |
| このタスクが必要な理由 | `if cwd.name == "aci" and cwd.parent.name == "common":` ブランチ（:79）が stale dead code として残存している |
| 着手条件 | Step 4 完了（detect_repo_root standalone 対応済み） |
| 入力 | `python/aci_public_smoke.py`（現状） |
| 書いてよい場所 | `python/aci_public_smoke.py` のみ |
| やること | `main()` 内の `if cwd.name == "aci" and cwd.parent.name == "common": repo_root = cwd.parent.parent else: repo_root = cwd` を `repo_root = cwd` に簡略化する |
| 期待する出力 | モノレポ前提コードのない `main()` |
| 合格条件 | `main()` にモノレポチェックが残らない (A22) |
| 失敗条件 | `main()` が repo root を誤認する |
| 停止条件 | なし |
| Status | done |

### Step 17: README.md の smoke check 説明を pier optional 表記に修正

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-17 |
| 目的 | smoke check の説明から pier 必須前提を除去する |
| このタスクが必要な理由 | `README.md:91-95` が smoke check の確認項目として `aci + pier domain` を必須のように並記している |
| 着手条件 | なし（独立） |
| 入力 | `README.md`（現状） |
| 書いてよい場所 | `README.md` の該当箇所のみ |
| やること | `aci + pier domain` の行を削除または "pier domain（installed 時のみ）" の旨に修正する |
| 期待する出力 | pier を optional として説明する README |
| 合格条件 | `README.md` の smoke check 説明が pier を必須前提として記載しない (A23) |
| 失敗条件 | なし |
| 停止条件 | なし |
| Status | done |

### Step 18: domains/pier/python/pier_domain_rules.py の dead 相対インポートを除去

| 項目 | 内容 |
|---|---|
| Task ID | aci-pier-dec-18 |
| 目的 | 常に失敗する dead 相対インポートを除去してコードを明確にする |
| このタスクが必要な理由 | `from ....python.aci_domain_contract import AciDomainRules`（:13）は4段相対インポートで常に `ImportError` になり except へフォールバックする。misleading な dead code |
| 着手条件 | なし（独立） |
| 入力 | `domains/pier/python/pier_domain_rules.py`（現状） |
| 書いてよい場所 | `domains/pier/python/pier_domain_rules.py` のみ |
| やること | `try: from ....python.aci_domain_contract import AciDomainRules` の try ブランチを削除し `from aci_domain_contract import AciDomainRules` の単独インポートのみとする |
| 期待する出力 | dead 相対インポートのない pier_domain_rules.py |
| 合格条件 | `from ....python.aci_domain_contract` が残らない (A24) |
| 失敗条件 | `PIER_DOMAIN_RULES` の生成が失敗する |
| 停止条件 | なし |
| Status | done |

## Current Status

- remaining task count: 0
- steps 1-10: 完了（2026-06-08）
- steps 11-18: 完了（2026-06-09）
- amendment 1: Steps 11-12（pier-optional フォローアップ、2026-06-08 発見）→ 完了
- amendment 2: Steps 13-18（全ファイル調査による追加発見、2026-06-09）→ 完了。C-6（automation-smoke KeyError）Step 15 で修正済み。L-2・L-3 は設計書 §11.3a の判断通り変更なし
- 全 18 step 完了。ACI は pier への依存なしで standalone 動作可能
