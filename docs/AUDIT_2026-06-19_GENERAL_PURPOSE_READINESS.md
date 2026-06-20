# ACI 監査記録 — 汎用コード監査ツールとしての完成度

- 監査日: 2026-06-19
- 対象バージョン: 0.1.8（`pyproject.toml`）/ ブランチ `claude/dreamy-brattain-c0180a`
- 監査方式: 証拠ベース（全ファイル精読 + 実環境PoC実行 + 外部標準照合）。推論のみの判断は不採用。
- 評価質問: 「ACIは**汎用的な**コード監査ツールとして完成しているか」

## 確定結論

**「汎用的なコード監査ツール」としては未完成（非該当）。**
ただし「Python-first 構造scanner（v0.1.8）」としては、限定スコープ内で動作し回帰固定された実働ツール。

理由は単なる未実装ではなく構造的:
1. 設計・自己定義・業界標準のいずれもが「汎用」を否定（native解析はPython専用、taint解析なし）。
2. Python範囲内ですら、最頻出のエイリアス書き換えでセキュリティ検出が全回避されるのに既知制約未記載。
3. 「完成」を支える証拠が自己採点の循環で、未知コードへの一般化が未測定。
4. 公開ドキュメントに虚偽（17検出器）と欠落（完成方針doc）がある。

## Step 1: 公式ドキュメント / 業界標準

ACI自身の自己定義（一貫して「Python-first」）:
- `README.md:31-34` — 「**Python-first** native audit tool ... **not** a language-general native structural auditor」
- `docs/NON_GOALS.md:13` — 「not a language-general native structural auditor across all languages」
- `shared/core/aci-product-boundary-and-coverage-policy.md:16` — 「ACI is a **Python-first** code audit tool」
- `README.md:87` — 「ACI **complements** ruff; it is **not a replacement**」

業界標準（汎用SAST/コード監査ツール）: 多言語対応 + クロスファイル/関数のデータフロー・taint解析（Semgrep 30言語超、SonarQube は OWASP/CWE/taint）。単一言語linterはこれを持たない。
- CWE-502: https://cwe.mitre.org/data/definitions/502
- SAST定義: https://appsecsanta.com/sast-tools/what-is-sast / https://dev.to/rahulxsingh/semgrep-vs-eslint-security-focused-sast-vs-javascript-linter-2026-hef

→ ACIの公式境界も業界標準も「汎用」を否定。

## Step 2: PoC結果（実行検証済み）

| 検証 | 結果 |
|---|---|
| `aci smoke` | ✅ 動作 |
| `pytest shared/tests` | ✅ 771 passed（exit 0） |
| 検証スイート planted | ✅ 期待25シグナル全25検出、gate fail（正） |
| 検証スイート clean | ✅ 0誤検出、gate pass（正） |
| 実世界 `requests` ライブラリ | ✅ findings 6件のみ・gate pass（低ノイズ。CI-23 `Session.send(**kwargs)` 等はFP気味だがlow confidence） |
| **エイリアス回避 4ケース** | ❌ **0/4検出**。`import pickle as p; p.loads()` / `import datetime as dt; dt.now()` / `datetime.datetime.now()` / `subprocess.run(f(), shell=True)`（ネスト括弧）が全てgate pass。非エイリアス同等形3件は全検出 |
| 欠落参照 | ❌ `docs/roadmap/ACI_COMPLETION_POLICY.md` がディレクトリごと不在（`aci-product-boundary-and-coverage-policy.md:11` が典拠参照） |
| 「17検出器」主張 | ❌ 実モジュール16、`ci_19.py` 不在。`README.md:65` は二重に誤り |
| 検証の循環性 | ⚠️ scorecardは同一リポジトリ内フィクスチャの自己採点 |

## Step 3: 第三者ソース

- 汎用SASTは多言語+クロスファイルtaint（Semgrep/SonarQube）。ACIは単一言語AST構文照合・taintなし → 定義上「汎用」非該当。
- CWE-502検出は成熟ツールではtaint+エイリアス解析で実施（FlowDroid等）。ACIの `import pickle as p` 盲点は業界が解決済みと位置づける既知弱点。

## 重大度別 所見（全てfile:line証拠付き・実行検証済み）

### Critical
- **C1 検証の循環性** — 「25/25・0FP」は検出器がチューニングされた同一リポ内フィクスチャの自己採点（`shared/tools/aci_validation_scorecard.py:39-71`）。未知コードでのprecision/recall試験が皆無。`shared/tools/aci_corpus_harness.py:11` 自身が「precision/recallを計算しない」と明記。
- **C2 エイリアスでセキュリティ検出が全回避（実行確定）** — 原因: `shared/python/detectors/ci_14.py:215-236`（`func.value.id` リテラル集合照合）、`ci_14.py:34`（`[^)]*` が内側 `)` で停止）、`shared/python/detectors/ci_25.py:27-37`（`=="datetime"` リテラル依存）。`shared/python/aci_known_limits.py` に未記載。

### High
- **H1 「17 native detectors / All parse AST」は虚偽** — 実モジュール16、`ci_19.py` 不在、CI-19はregexかつdomain-pack専用（`shared/python/aci_scan.py:621`）。`README.md:65` vs `shared/python/detectors/__init__.py`。CI_REFERENCE側は「22 active IDs」で正しく、誤りはREADME見出し。
- **H2 完成方針ドキュメント不在** — `docs/roadmap/ACI_COMPLETION_POLICY.md` 不在。「完成」を論じる中核docが欠落。
- **H3 recall_probeの自己充足** — 難ケースを `known-limit` で合否計算から除外（`shared/tools/aci_recall_probe.py:128`）、テストは `recall==1.0` のみ主張（構造上常に成立）。precision系テストは検出器を一切実行せず手書きdict集計。

### Medium
- **M1 ruff委譲がドキュメントより広い** — ruffインストール時、5シグナルをスキャン前に無効化（`shared/python/aci_scan.py:1130-1142`）。
- **M2 アナライザのparse-failureが既定で素通り** — JSON解析失敗が空findings=gate pass（`shared/python/aci_analyzer_execution.py:1184`）。
- **M3 テスト分布の極端な偏り** — CI-22が約480、他14検出器は各≤6。CI-14は約20、CI-25は2。
- **M4 「full native coverage」主張過大** — `shared/core/aci-autonomous-code-inspection-tool-contract.md:32` / `aci-product-boundary-and-coverage-policy.md:21` が「full coverage」と称すがC2が反証。

### Low
- **L1 CI-26がmere `global`存在でHIGH confidence** — lazy-init免除が緩い（`shared/python/detectors/ci_26.py:23-59`）。
- **L2 自己中心的なパス分類** — ACI固有レイアウトを汎用classifierにハードコード（`shared/python/aci_scan.py:427-430`）。
- **L3 非UTF-8テキストを `errors="ignore"` で黙って欠損** — skip記録なし（`shared/python/aci_scan.py:1082`）。

## 監査の限界（誠実な開示）
- 検出器は ci_02/03/04/07 を全行精読、ci_14 を詳細精読。他は登録+シグネチャ+対象節を確認。内部ロジックの全行監査は未実施の検出器あり。
- 実世界スキャンは `requests` 1パッケージのみ。広範な独立コーパス評価は本監査の範囲外（C1の指摘そのもの）。
