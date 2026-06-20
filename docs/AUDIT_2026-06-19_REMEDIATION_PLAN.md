# ACI 是正ロードマップ — 汎用コード監査ツール化

- 起票日: 2026-06-19
- 改訂: 2026-06-19（Phase 4 の framing を修正。下記「改訂記録」参照）
- 紐付く監査記録: `docs/AUDIT_2026-06-19_GENERAL_PURPOSE_READINESS.md`
- 前提認識: 「汎用 native 多言語解析」の自前実装は Semgrep/CodeQL/SonarQube と正面競合する数年規模事業。現実的な「完成」は **堅牢な Python-native コア + 多言語は一流外部アナライザのオーケストレーション + 独立評価**。

## 改訂記録（2026-06-19）

初版は Phase 4 を「①多言語を自前native実装 vs ②外部アナライザのオーケストレーション」の**戦略分岐**として記述したが、これは誤り。実コード確認（`shared/python/aci_analyzer_execution.py:83-93`）で以下が確定:

- ACIは**最初から非Pythonを外部ツールへ委譲しており、オーケストレーションは既に現行アーキテクチャ**。
- 実行可能(execution-ready)な9ツールが既に稼働: `semgrep`(30言語超), `eslint`/`tsc`(JS/TS), `shellcheck`(Shell), `sqlfluff`(SQL), `ruff`/`pyflakes`/`mypy`/`pytest`(Python)。
- 「自前native多言語実装(①)」は誰も提案しておらずACIも未実施＝**実体のないストローマン**。

したがって Phase 4 は「戦略分岐」ではなく、**「既存オーケストレーションの正式化＋カタログ止まり4ツールの実行化」という小さな差分**に縮小する（下記 Phase 4 を改訂）。
**含意: 「汎用・完成」の本丸は Phase 4 ではなく Phase 0 → 1 → 2。**

## 進捗ログ

- **Phase 0 完了（2026-06-19）**: README「17」是正、`docs/roadmap/ACI_COMPLETION_POLICY.md` 作成＋`.gitignore` 再包含で追跡化、known-limit に alias 追加、契約doc「full coverage」格下げ。worktreeコードで全771テスト緑。
- **Phase 1 完了（2026-06-19）**: `_helpers.ImportResolver` 名前解決層を新設し CI-14（subprocess を AST化／deserialization／yaml）・CI-25 を接続。エイリアス回避 **0/4 → 4/4**。recall_probe に alias 4件を必須追加（21/21）。scorecard 25/25・0FP 維持。known-limit を残存範囲に更新。
- **Phase 2 完了（2026-06-19）**: `shared/tools/aci_independent_eval.py` 新設 — Python標準ライブラリ（ACI未tune）を host にした mutation で**独立recall算出（100%）**＋未改変stdlibの**ノイズ/FP候補率算出（1.71 findings/kloc, signal別内訳）**。`recall_probe` を known-limit「除外」→「併記レポート」に修正（H3）。`test_aci_independent_eval.py` で固定。
- **Phase 3 完了（2026-06-19）**: `shared/python/detectors/ci_14_taint.py` 新設 — ACI初の**データフロー検出**。intra-procedural な source→sink taint（source: `input()`/`os.environ`/`os.getenv`/`sys.argv`/`request.*`、sink: `eval`/`exec`/`os.system`/`os.popen`/`subprocess(shell=True)`/`cursor.execute`、伝播: 代入・f-string・連結・文字列メソッド）。新signal `CI14_TAINTED_FLOW` を `_NATIVE_HYGIENE_SIGNALS` とレジストリに配線。**精度優先設計で recall 6/6・誤検出 0**（clean fixture・ACI自身・stdlib いずれも0 FP）。`test_aci_taint.py`（12件）で固定、known-limit `KL-ACI-CI14-TAINT-INTRAPROCEDURAL` で inter-procedural 非対応を明記。
- **Phase 5 実質完了（2026-06-19）**: `ci_22.py` を列挙ベース（1349行・~40レコグナイザ）から**原理的解析へ全面書換**（**499行＝63%削減**）。中核は「*この式を呼ぶとハンドルが閉じるか？*」を assignments/`functools.partial`/lambda/local def/registrar alias 越しに解決する**1つの再帰述語**。ExitStack callback/partial/lambda/helper の全綴りがこの述語の事例として一括分類される（＝「判定して振り分け、チェックを減らす」）。**480 CI-22テスト全通過・scorecard recall不変・ruffクリーン**。`CI_REFERENCE.md` の CI-22 列挙も 372→163行に縮小。**注**: ≤400行の数値目標は構造床（定数＋~38原理ヘルパー＋ruff強制空行）のため499行で未達。これ以上は密化で可読性（リファクタ本来の目的）を損なうため見送り。
- **Phase 4 一部完了（2026-06-19）**: `osv-scanner`・`trivy` に execution-ready アダプタ（command builder＋JSONパーサ→CI-14正規化）を実装し `_EXECUTION_READY_ANALYZERS` に追加。`show-analyzer-availability` で両者が `availability-check-only`→`execution-ready` へ遷移。パーサをサンプルJSONで単体テスト（`test_aci_analyzer_execution.py`）。**`gitleaks`（ファイルレポート出力）・`codeql`（DB構築必須）は実行モデルが bounded single-invocation 契約に合わないため availability-only 維持＋理由を boundary doc に明記**（過剰主張回避）。ライブ実行検証は当該ツール導入時のみ可能（全opt-inアナライザ共通の制約）。

- **構造化（2026-06-19）**: **責務（パイプライン段階）駆動**でモジュール分割（行数駆動ではない）。`aci_analyzer_execution.py`（1346→951）から**出力パーサ**概念を `_analyzer_parsers.py`(432)へ。`aci_scan.py`（1338）から**レポート/ゲート構築**を `_scan_report.py`(306)へ、**finding後処理(dedup/scope-noise/operations適用)** を `_scan_postprocess.py`(88)へ分離（当初reportに混在していた3概念を単一責務へ是正）。公開API・テスト参照名は元モジュールから再エクスポートして互換維持。両import経路疎通・ruff/mypyクリーン・全789テスト緑。**責務分離 完遂（2026-06-19）**: 行数ではなく**分析パイプラインの段階＝責務**で分割。
- **analyzer**: `aci_analyzer_execution.py`(757, readiness+実行統括) / `_analyzer_commands.py`(195, コマンド構築) / `_analyzer_parsers.py`(514, 出力パース＋CI-IDマッパー, **自己完結＝循環解消**)
- **scan**: `aci_scan.py`(674, config+検出器統括+scan_target) / `_scan_scope.py`(398, スコープ解決+走査, scope語彙定数を所有) / `_scan_report.py`(304, レポート/ゲート構築) / `_scan_postprocess.py`(88, finding後処理)
- 各モジュールは単一責務。公開名は元モジュールから再エクスポートして互換維持。**1000行超ファイル：ゼロ**。全789テスト緑・ruff/mypyクリーン。

## フェーズ別 Goal とその検証可否（実測ベースライン付き）

各 Goal は「ベースライン（今日の実測値）→ 目標値 → 測定コマンド → 今すぐ自動測定できるか」で定義。

### Phase 0 — 是正（嘘と欠落を消す）｜紐付: H1, H2, C2, M4
| 項目 | 内容 |
|---|---|
| Goal | 公開ドキュメントの虚偽・欠落をゼロにする |
| 受け入れ基準 | (a) README の「17 detectors/all AST」表現=0、(b) `docs/roadmap/ACI_COMPLETION_POLICY.md` 存在 or 参照削除、(c) `aci_known_limits.py` に alias 盲点記載≥1、(d) 契約docの「full coverage」表現を是正 |
| ベースライン(実測) | (a) **2箇所**、(b) **不在(NO)**、(c) **0件**、(d) 未是正 |
| 測定コマンド | `grep -c "All 17\|17 .*detectors" README.md` / `test -f docs/roadmap/ACI_COMPLETION_POLICY.md` / `grep -ci alias shared/python/aci_known_limits.py` |
| **Goal検証可否** | ✅ **今すぐ完全自動検証可能**。受け入れ基準がそのままCI gate化できる |

### Phase 1 — Python範囲の堅牢化（名前解決層）｜紐付: C2
| 項目 | 内容 |
|---|---|
| Goal | エイリアス/属性/`from x import`束縛/ネスト括弧でセキュリティ検出が回避されない |
| 受け入れ基準 | alias-fixture pack（`import pickle as p`, `import datetime as dt`, `datetime.datetime.now()`, `subprocess.run(f(),shell=True)` 等）で recall=1.0、既存 clean の FP 不変 |
| ベースライン(実測) | 同等 alias 4ケース = **0/4 検出（gate pass）**、非alias同等形 = 3/3 検出 |
| 測定コマンド | alias pack を validation-suite に追加 → `aci_validation_scorecard.py` |
| **Goal検証可否** | ✅ **自動測定可能**。測定器は既存（scan+manifest+scorecard）。fixture追加のみで baseline 0/4 → 目標 4/4 を機械判定 |

### Phase 2 — 循環性の打破（独立評価）｜紐付: C1, H3, M3
| 項目 | 内容 |
|---|---|
| Goal | precision/recall を、検出器が未見の独立コーパスで測定・公開する |
| 受け入れ基準 | チューニング用と分離した独立ラベル付きコーパスで precision/recall を算出（閾値は測定後に設定）。recall_probe は known-limit を合否除外せず併記 |
| ベースライン(実測) | 独立コーパス測定 = **存在しない**。`aci_corpus_harness.py:11` 自身が「precision/recallを計算しない」と明記。recall_probe は known-limit を除外（`:128`） |
| 測定コマンド | 新規: ラベル付きコーパスランナー（要構築）+ 改修した recall_probe |
| **Goal検証可否** | ⚠️ **Goal設定は可能だが測定器が未存在**。独立ラベルコーパス＋precision/recall計算ロジックの構築が本フェーズの成果物。構築後は自動測定可 |

### Phase 3 — taint/dataflow 導入｜紐付: 業界SAST定義要件
| 項目 | 内容 |
|---|---|
| Goal | source→sink のデータフローでセキュリティIDを検出（手続き内→手続き間） |
| 受け入れ基準 | taint fixture（汚染源→危険sink、間接代入経由）で検出、無害な定数フローで FP なし |
| ベースライン(実測) | taint 解析・taint fixture = **ゼロ**（現状は単発AST/regex） |
| 測定コマンド | 新規: taint fixture スイート（要構築） |
| **Goal検証可否** | ⚠️ **Goal設定は可能だが基準コーパスが未存在**。推奨は自前実装より CodeQL/Semgrep Pro を外部レーンに組込み、その検出を測定対象にする |

### Phase 4 — 既存オーケストレーションの正式化 + 残4ツール実行化｜紐付: 「汎用」看板
> 注: オーケストレーションは新規方針ではなく**既に現行アーキテクチャ**（execution-ready 9ツール稼働中）。本フェーズは「分岐の決断」ではなく、(a) 看板の正式化と (b) カタログ止まり4ツールの実行化という小さな差分。

| 項目 | 内容 |
|---|---|
| Goal | (a) ACIの立ち位置を「Python-native コア + 多言語は外部アナライザのオーケストレータ」と正式定義、(b) catalog-only の deep analyzer を実行可能化 |
| 受け入れ基準 | (a) README/契約docが「自前網羅」でなく「統合網羅」を明記、(b) `codeql`/`gitleaks`/`osv-scanner`/`trivy` の support_level が `opt-in` → `execution-ready` へ遷移し、実 invocation が正規化findingsを返す |
| ベースライン(実測) | execution-ready=**9ツール稼働**（semgrep/eslint/tsc/shellcheck/sqlfluff/ruff/pyflakes/mypy/pytest）。残り `codeql`/`gitleaks`/`osv-scanner`/`trivy`=**`opt-in`（実行せず導入チェックのみ）**。定義は `aci_analyzer_execution.py:83-93` |
| 測定コマンド | `aci scan --target <polyglot-fixture>` で当該アナライザの runtime_state を確認 / `show-analyzer-catalog` で support_level 遷移を確認 |
| **Goal検証可否** | ✅ **自動測定可能**。既存CLI(`show-analyzer-catalog`/`scan`)が状態を構造化出力。実行アダプタ実装後に `opt-in`→`execution-ready` 遷移を機械判定 |
| 規模感 | **小**。多言語検出ロジックの自作は不要（外部ツール任せ）。実体は4アダプタ追加＋positioning修正 |

### Phase 5 — 保守負債の解消｜紐付: CI-22肥大, L1, L2, L3
| 項目 | 内容 |
|---|---|
| Goal | CI-22 を原理的 escape/ownership 解析に置換し、列挙肥大を解消（recall維持） |
| 受け入れ基準 | `ci_22.py` LOC を大幅削減（例: ≤400）かつ validation scorecard の CI-22 recall=1.0 不変、`CI_REFERENCE.md` CI-22節も連動縮小 |
| ベースライン(実測) | `ci_22.py` = **1349 LOC**（次点 ci_14=679, ci_20=285, ci_02=207） |
| 測定コマンド | `wc -l shared/python/detectors/ci_22.py` + `aci_validation_scorecard.py` |
| **Goal検証可否** | ✅ **自動測定可能**。LOC閾値＋recall不変の二条件を既存ツールで機械判定 |

## 検証総括: フェーズごとの Goal 設定は可能か

**結論: 6フェーズ全てで SMART な Goal（具体的・測定可能な受け入れ基準）を設定できる。**

| 区分 | フェーズ | 測定の現況 |
|---|---|---|
| ✅ 既存ツールで今すぐ自動測定可 | Phase 0, 1, 4, 5 | grep/`test -f`/scorecard/`wc -l`/`show-analyzer-availability` がそのまま受け入れテスト |
| ⚠️ Goal可・測定器はフェーズ内成果物 | Phase 2, 3 | 独立ラベルコーパス / taint fixture の新規構築が前提（構築後は自動測定可） |

到達定義:
- **Phase 0+1+2 完了 = 誠実で堅牢な Python-first ツール**（嘘ゼロ・エイリアス耐性・独立評価あり）
- **+ Phase 3+4 = 汎用コード監査ツール（オーケストレーション型）** として正当に名乗れる

優先順位（改訂後）: 本丸は **Phase 0 → 1 → 2**。Phase 4 はオーケストレーションが既に稼働済みのため小ぶり（4ツール昇格＋看板正式化）。Phase 3(taint) と Phase 4 のうち多言語の深い解析は外部ツール（CodeQL/Semgrep）に委ねる方針で、自前再実装は非ゴール。
