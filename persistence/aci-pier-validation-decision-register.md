# task_aci001 Validation Decision Register

Last updated: 2026-05-26

Purpose:

- accumulate reviewed `ACI` validation decisions for the `Pier` integration
  surface
- make detector-tuning and human-confirm policy changes traceable without
  relying on operator memory
- keep `Pier`-specific residual classification out of the generic `ACI`
  design shelf

Scope:

- only reviewed residuals from `Pier` validation runs belong here
- root-cause fix items do not belong here once they are routed to direct
  remediation
- generic `ACI` tool rules stay at the repo root
- generic template authority stays in `templates/`

Human-confirm rendering rule:

- when an item is presented to a human reviewer, it must be renderable with the
  following fixed headings:
  - `コード全体の目的`
  - `ツール名`
  - `エラー種別`
  - `参照先`
  - `エラー内容`
  - `詳細解説`
  - `推奨`
  - `確認事項`
- the table below is the storage form; human-facing review output must project
  into those eight headings without adding ad hoc wording

Dirty-tree discipline actor rule:

- `ACI-detected`
  - only when a project-local companion lane emits a dirty-tree finding from path/rule evidence
- `manual refinement of ACI output`
  - when owner maps that finding to a closure board, theme, or reopen rule
- `manual-only gap`
  - when a human/Codex notices a dirty-tree discipline issue that the companion lane did not emit

Do not record a dirty-tree owner judgment as if the generic `ACI` core had detected it.

## Residuals Requiring Detector Decomposition Before Bucketing

| date | target file | line | signal | current bucket | recommended bucket | code excerpt | runtime role | failure behavior | judgment question | reason | source report | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-26 | taskiq/receiver/receiver.py | 399,425 | CI26_RACE_HAZARD | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `asyncio.create_task(iterator.__anext__())` | async iterator advancement (次メッセージ取得) | 誤検知。共有可変状態なし。iterator.__anext__() 呼び出しにすぎない | — | `__anext__` パターンは単一行・複数行両形式あり。suppressor 追加済み（単行 + next_line check 両形式） | 20260526_aci_github_corpus_audit_summary.md | resolved |
| 2026-05-26 | arq/worker.py | 781 | CI25_ENVIRONMENT_DRIFT | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `f'{datetime.now():%Y-%m-%d}'` | ログファイル名のフォーマット指定子（TZ非依存文字列生成） | 誤検知。`:%fmt` はフォーマット指定子であり、TZ依存の計算を行わない | — | `datetime.now():%fmt` 形式は出力フォーマット指定にすぎない。FSTRING_DATETIME_FORMAT_SPEC_PATTERN suppressor 追加済み | 20260526_aci_github_corpus_audit_summary.md | resolved |
| 2026-05-26 | celery/worker/consumer/consumer.py | 293 | CI21_BROAD_EXCEPTION_SWALLOW | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `while queue: try: queue.pop()() except Exception as exc: logger.exception(...)` | pending operation drain loop（1件失敗でも残り処理を継続） | 誤検知。ループ内 logging-only handler は標準パターン | — | for/while ループ内でのロギングのみ例外ハンドラは drain loop の定番パターン。`_is_logging_only_in_loop_handler` suppressor 追加済み | celery corpus audit 2026-05-26 | resolved |
| 2026-05-26 | celery/worker/consumer/consumer.py | 428 | CI21_BROAD_EXCEPTION_SWALLOW | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `try: conn.collect(socket_timeout=T) except Exception: pass` | broken connection teardown（既に壊れたリソースのクリーンアップ） | 誤検知。teardown パスの bare pass は適切 | — | `.collect/.release/.disconnect` 等の teardown 呼び出し直後の `except Exception: pass` は best-effort cleanup の標準パターン。`_is_generic_teardown_pass_handler` suppressor 追加済み | celery corpus audit 2026-05-26 | resolved |
| 2026-05-26 | celery/worker/consumer/consumer.py | 738 | CI21_BROAD_EXCEPTION_SWALLOW | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `except Exception as exc: return self.on_decode_error(message, exc)` | message decode error routing（専用 error handler へ委譲） | 誤検知。return でエラーを明示委譲しており swallow ではない | — | `return self.on_*_error(msg, exc)` パターンは例外を error handler へ明示 routing するため swallow に非ず。`_is_error_routing_return_handler` suppressor 追加済み | celery corpus audit 2026-05-26 | resolved |
| 2026-05-26 | celery/app/base.py | 123 | CI21_BROAD_EXCEPTION_SWALLOW | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `try: app._after_fork() except Exception as exc: logger.info(...)` | register_after_fork callback（fork 後 child process 内実行） | 誤検知。fork callback でのロギング swallow は適切 | — | `._after_fork()` 呼び出し後の logging-only handler は fork callback の標準パターン。`_is_fork_callback_logging_handler` suppressor 追加済み | celery corpus audit 2026-05-26 | resolved |
| 2026-05-26 | celery/worker/consumer/consumer.py | 334 | CI21_UNBOUNDED_RETRY | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `while True: try: item=bucket.pop() except IndexError: break` | rate limit bucket drain（IndexError で必ず break する有界ループ） | 誤検知。narrow except + break のパターンは unbounded ではない | — | `while True` + `except IndexError: break` は EAFP ドレインパターン。broad handler を持つ場合のみ UNBOUNDED_RETRY を発火するよう修正済み | celery corpus audit 2026-05-26 | resolved |
| 2026-05-26 | sqlalchemy/dialects/postgresql/base.py, mysql/base.py, sqlite/base.py | 複数 | CI05_DUPLICATE_BLOCK | ツール側で消せる誤検知 | ツール側で消せる誤検知 | モジュール docstring 内の共有説明文（server-side cursor 等） | 複数方言ファイルの共有ドキュメント | 誤検知。docstring 内テキストはコード重複でなく説明文 | — | 多行文字列リテラル（docstring 含む）の行は CI05 の重複判定から除外すべき。`_multiline_string_line_set` で AST ベースのスキップを実装済み | sqlalchemy corpus audit 2026-05-26 | resolved |
| 2026-05-26 | httpx/_client.py | 941, 970, 1656, 1685 | CI21_UNBOUNDED_RETRY | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `while True: try: ... return response except BaseException as exc: response.close(); raise exc` | auth flow / redirect loop（例外時は必ずリソースを close して re-raise） | 誤検知。broad handler の最終文が `raise exc` であるため、ループは例外で必ず終了する | — | `while True` + `except BaseException: cleanup; raise exc` は有界ループ。`_all_broad_handlers_reraise` suppressor 追加済み（handler 最終文が `ast.Raise` の場合に抑制） | httpx corpus audit 2026-05-26 | resolved |
| 2026-05-26 | httpx/_config.py | 35, 37 | CI25_ENVIRONMENT_DRIFT | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `if os.environ.get("SSL_CERT_FILE"): ctx = ssl.create_default_context(cafile=os.environ["SSL_CERT_FILE"])` | SSL 設定（trust_env フラグ付き条件分岐） | 誤検知。`os.environ["KEY"]` は直前の `os.environ.get("KEY")` が truthy の場合のみ実行されるため KeyError リスクなし | — | if 条件に `os.environ.get("KEY")` を含む場合、同一 key の `os.environ["KEY"]` subscript は guard 済み。`_is_environ_subscript_guarded_by_get` suppressor 追加済み（AST 親チェーンで If ノードを遡り test に get() を確認） | httpx corpus audit 2026-05-26 | resolved |
| 2026-05-26 | uvicorn/config.py | 340 | CI25_ENVIRONMENT_DRIFT | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `if "WEB_CONCURRENCY" in os.environ: self.workers = int(os.environ["WEB_CONCURRENCY"])` | ワーカー数設定（環境変数存在確認後のアクセス） | 誤検知。`"KEY" in os.environ` は key の存在を確認するため、後続の `os.environ["KEY"]` は KeyError リスクなし | — | `"KEY" in os.environ` ガードパターンも `os.environ.get()` と同等。`_test_has_environ_guard` に `ast.In` 演算子判定を追加し suppressor を拡張済み | uvicorn corpus audit 2026-05-26 | resolved |
| 2026-05-26 | django/conf/global_settings.py | 全体 | CI08_CONFIG_HELL | ツール側で消せる誤検知 | 誤検知なし | `SECRET_KEY = ""` など空文字列プレースホルダー | Django デフォルト設定ファイル（ドキュメント的役割） | 真陰性。空文字列・None は `_is_credential_placeholder_value` で抑制される | — | placeholder suppressor が `""` / `None` をカバー。CI08 findings=0 で正しく動作 | django corpus audit CI08 2026-05-26 | resolved |
| 2026-05-26 | django/tests/test_sqlite.py | 24 | CI08_CONFIG_HELL | 根本解決で潰すべきもの | 根本解決で潰すべきもの | `SECRET_KEY = "django_tests_secret_key"` | テスト用設定ファイル（本番では使用不可の文字列） | 真陽性。テストファイルのため severity=WARN が正しいが corpus 配置の都合で HIGH 表示（path に tests/ prefix なし） | corpus artifact であり tool 動作は正しい | 本番 repo では `tests/test_sqlite.py` として WARN になる。corpus では flat 配置のため TEST_PATH_PATTERN が不一致 | django corpus audit CI08 2026-05-26 | resolved |
| 2026-05-26 | pallets/flask/tests/conftest.py | 全体 | CI08_CONFIG_HELL | 誤検知なし | 誤検知なし | Flask テスト conftest（`SECRET_KEY` なし or 設定なし） | Flask テストフィクスチャ | 真陰性。findings=0。Flask conftest は SECRET_KEY を直接設定せず | — | false positive 0 件確認 | flask corpus audit CI08 2026-05-26 | resolved |
| 2026-05-26 | shared/tools/update_task_state_auth.py | 20 | CI08_CONFIG_HELL | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `_GATE_SECRET_ENV = "PIER_GATE_SECRET"` | env var キー名格納定数（認証情報ではなく env var 名） | 誤検知。値 `"PIER_GATE_SECRET"` は `^[A-Z][A-Z0-9_]*$` 形式の env var キー名であり認証情報ではない | — | 全大文字・アンダースコアのみの文字列は env var key name。`ENV_VAR_KEY_NAME_PATTERN` suppressor 追加済み | pier internal CI08 audit 2026-05-26 | resolved |
| 2026-05-26 | shared/tools/archive/migrate_to_postgresql.py | 36 | CI08_CONFIG_HELL | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `print("postgresql://postgres.xxx:[PASSWORD]@aws-1...")` | 環境変数設定例を示す print 文（`[PASSWORD]` はブラケットプレースホルダー） | 誤検知。接続文字列のパスワード部分 `[PASSWORD]` はブラケット形式プレースホルダー | — | `[...]` 形式プレースホルダーを `CREDENTIAL_PLACEHOLDER_PATTERN` に追加済み。接続文字列検出でもパスワード部分を抽出して placeholder チェックを適用 | pier internal CI08 audit 2026-05-26 | resolved |
| 2026-05-26 | (generic corpus) | — | CI14_SECURITY_NEGLECT | 新実装 | 新実装 | SQL f-string 補間 / 動的コード実行関数呼び出し / subprocess shell=True | SQL クエリ文字列生成・動的コード実行・subprocess shell 呼び出し | 真陽性。SQL f-string 補間・動的コード実行関数・shell=True を native-static で検出。テストファイルは WARN に severity downgrade | SQL に `%s`・`?`・`$n` placeholder が含まれる場合は suppress。動的実行関数名は `DYNAMIC_CODE_EXEC_NAMES` frozenset で管理 | native-static secondary lane 実装完了。SE-251 §3.2 に secondary エントリ追加。external-analyzer primary (bandit/ruff) は別 lane | CI14 implementation 2026-05-26 | resolved |
| 2026-05-26 | (generic corpus) | — | CI15_DOCUMENTATION_ROT | 新実装 | 新実装 | docstring の引数名と関数シグネチャの不一致 | 関数ドキュメント保守 | 真陽性。Google / NumPy / Sphinx RST の 3 スタイルに対応。実シグネチャに存在しない引数名を WARN | `self`・`cls`・`*args`・`**kwargs`・1 文字以下の引数名は suppress | native-static secondary lane 実装完了（Item 1 のみ。Items 2・3 は human-judgment）。SE-251 §3.2 に secondary エントリ追加。external-analyzer primary (mypy/pydocstyle) は別 lane | CI15 implementation 2026-05-26 | resolved |
| 2026-05-26 | arq / dramatiq (stdlib shadow) | — | CI13_DEPENDENCY_ROT | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `dramatiq/logging.py` が `import logging` → `logging → logging` self-loop / `arq/typing.py` が `if TYPE_CHECKING: from .worker import Function` | モジュール名が stdlib と衝突（module shadowing）/ 型チェッカー専用 import | 誤検知。self-loop は `(imports & module_names) - {stem}` で除外。TYPE_CHECKING ガード内 import は `_visit` で skip | stdlib shadow self-loop suppressor + TYPE_CHECKING suppressor 追加済み | arq 循環 4→0, dramatiq 誤循環 6→0 | CI13 corpus audit arq/dramatiq 2026-05-26 | resolved |
| 2026-05-26 | taskiq/taskiq/funcs.py | 10 | CI15_DOCUMENTATION_ROT | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `def gather(*tasks)` / docstring `:param tasks:` | `*vararg` 名を docstring に明示的に文書化 | 誤検知。`*tasks` は vararg であり docstring に記載することは正当 | `*vararg` 名を `sig_params` に追加（`add` に変更）して suppress | taskiq CI15: 7→2（残り 2 件は真陽性：パラメータ名変更後 docstring 未更新） | CI15 corpus audit taskiq 2026-05-26 | resolved |
| 2026-05-26 | alembic/alembic/ddl/postgresql.py | 681 | CI15_DOCUMENTATION_ROT | ツール側で消せる誤検知 | 誤検知なし | `def create_exclude_constraint(cls, ..., **kw)` / docstring `:param name: ... :param deferrable:` | `**kw` 経由で受け取る引数を docstring に文書化（alembic DSL パターン） | 誤検知。`**kw` がある関数は全 docstring param を suppress | `**kwarg` suppressor（関数が `**kw` を受ける場合は skip）追加済み | alembic CI15: 49→1（残り 1 件は真陽性）| CI15 corpus audit alembic 2026-05-26 | resolved |
| 2026-05-26 | aiohttp (site-packages) | 複数 | CI07_LAVA_FLOW | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `# not already removed by _release_waiter` / `# got removed from headers parsing` / `# can be removed someday` | 実行時動作・データ変換・将来 cleanup 候補の説明コメント | 誤検知。`removed` 単体は「削除済み API / deprecated 定義」以外の文脈でも広く使用される | `LAVA_FLOW_COMMENT_PATTERN` から `removed` を除去。`deprecated` / `legacy` / `todo: remove` で代替 | aiohttp CI07: 8→1（残り 1 件は `# Deprecated: RFC 9112` で TP） | CI07 corpus audit aiohttp site-packages 2026-05-26 | resolved |
| 2026-05-26 | django/template/smartif.py | 複数 | CI14_SECURITY_NEGLECT | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `lambda ctx, x, y: x.eval(ctx) or y.eval(ctx)` — `.eval()` はカスタム演算子クラスのメソッド呼び出し | テンプレートエンジン演算子評価（builtin `eval()` とは無関係） | 誤検知。`ast.Attribute` 経由の `.eval()` 呼び出しは Python builtin `eval()` でない | `DYNAMIC_CODE_EXEC_NAMES` 検出を `ast.Name`（bare call）のみに限定。`ast.Attribute` 経由のメソッド呼び出しは除外 | django CI14: 35→6（残り 6 件は TP：questioner.py eval / shell.py exec / postgresql bulk_insert_sql / version.py shell=True） | django corpus audit CI14 2026-05-26 | resolved |
| 2026-05-26 | django/tasks/base.py ほか | 複数 | CI13_DEPENDENCY_ROT | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `from django.db.models... import ...` → `django` が `module_names` に含まれる（`template/backends/django.py` が存在するため） | パッケージ名と同名のファイルによる import graph 汚染 | 誤検知。パッケージ root 名と同名ファイルが存在する場合、外部 import がパッケージ内循環と誤判定される | `_pkg_name = root.name` を `_excluded` に追加し import graph から除外 | django CI13 circ: 1→0 | django corpus audit CI13 2026-05-26 | resolved |
| 2026-05-26 | trio/_socket.py, trio/_abc.py | — | CI13_DEPENDENCY_ROT | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `import socket as _stdlib_socket` — trio が `socket.py` / `abc.py` を持つため stdlib import がパッケージ内依存と誤判定 | Python stdlib の `socket` / `abc` モジュールを absolute import（level=0） | 誤検知。`sys.stdlib_module_names` で既知 stdlib 名を除外することで解決 | `_stdlib = sys.stdlib_module_names` を import graph の intersection から除外 | trio CI13 circ: 10→8（残り 8 件は `_run ↔ _io_windows/epoll/kqueue/_generated_*` の真陽性循環） | trio corpus audit CI13 2026-05-26 | resolved |
| 2026-05-26 | celery/utils/functional.py, django/utils/functional.py | — | CI07_LAVA_FLOW | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `# class attributes __module__...` / `# class we are pickling` — `# class \w+` パターンが英語散文にマッチ | コードコメント（コメントアウト定義でなく説明文） | 誤検知。`# class` / `# def` の後に `(` または `:` が続かない場合は定義でなく説明文 | `LAVA_FLOW_COMMENTED_DEF_PATTERN` に `[\(:]` 要件を追加 (`r"^\s*#\s*(def \|class )\s*\w+\s*[\(:]"`) | celery CI07: 14→13 / django CI07: 13→12（それぞれ 1 FP 除去） | celery/django corpus audit CI07 2026-05-26 | resolved |
| 2026-05-26 | django/migrations/operations/models.py, contrib/postgres/operations.py | — | CI14_SECURITY_NEGLECT | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `f"Alter {self.name} table comment"` / `f"Create collation {self.name}"` — `describe()` メソッド内の人間可読ラベル | migration 操作の説明文（SQL クエリ文字列でない） | 誤検知。`describe()` / `__repr__` 等の display メソッド内 f-string は SQL コンテキストでない | `SQL_DISPLAY_METHOD_NAMES` frozenset を追加し `display_lines` でスキップ | django CI14: 9→6（残り 6 件は TP） | django corpus audit CI14 2026-05-26 | resolved |
| 2026-05-26 | trio/_core/_run.py ほか | — | CI15_DOCUMENTATION_ROT | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `to :func:run`, `delayed:`, `see` — Google style docstring の continuation line 内の語が param として誤認識 | trio は Google style docstring を 2-space indent で記述（標準 4-space でない） | 誤検知。2-space indent の param は検出されず、その continuation line（4-space 相当）が誤マッチ | `_extract_docstring_param_names` を section-aware かつ adaptive-indent 化。`param_indent` を Args ヘッダ後の最初の非空行から動的検出。`indent < param_indent` で section exit | trio CI15: 4→1（残り 1 件は `WaitForSingleObject` の `handle→obj` rename で TP） | trio corpus audit CI15 2026-05-26 | resolved |
| 2026-05-26 | trio/_threads.py | 257 | CI15_DOCUMENTATION_ROT | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `  example: :func:getaddrinfo` — `**Cancellation handling**:` セクション後の continuation line（`example:` が 2-space indent でパラメータと同一レベル） | Cancellation handling 説明文の一部 | 誤検知。`**Bold header**: text` 形式のセクションは Args section exit 条件（行末 `:`）にマッチしないため section が継続し `example:` が誤検出される | `indent < param_indent` 条件で exit（`**Cancellation handling**:` が 0-space indent であるため自動退出） | trio CI15: 2→1（残り 1 件は `WaitForSingleObject` の TP） | trio CI15 inline-section-exit audit 2026-05-26 | resolved |

## Human-Confirm Residuals Confirmed As Tool-Side Suppressible Pending Detector Work

| date | target file | line | signal | current bucket | recommended bucket | code excerpt | runtime role | failure behavior | judgment question | reason | source report | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-26 | aiohttp/client_proto.py | 326 | CI21_BROAD_EXCEPTION_SWALLOW | ツール側で消せる誤検知 | ツール側で消せる誤検知 | `except Exception as underlying_exc: ... self.set_exception(exc, underlying_exc); return` | HTTP パーサ data_received（asyncio.Protocol 例外ルーティング） | 誤検知。`self.set_exception(exc)` は例外を asyncio Protocol/Future メカニズムで伝播するため swallow ではない | — | `self.set_exception(exc) ... return` は asyncio.Protocol 標準の例外伝播パターン。corpus 全体で 1 件のみ確認。suppressor 実装は evidence 蓄積後に判断 | aiohttp corpus audit 2026-05-26 | pending-suppressor |

## Human-Confirm Residuals That Still Require Human Confirmation

| date | target file | line | signal | current bucket | recommended bucket | code excerpt | runtime role | failure behavior | judgment question | reason | source report | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-26 | aiohttp/client_proto.py | 150 | CI21_BROAD_EXCEPTION_SWALLOW | 人間確認 | 人間確認 | `try: uncompleted = self._parser.feed_eof() except Exception as underlying_exc: if self._payload is not None: set_exception(self._payload, ...)` | HTTP パーサ EOF 処理（ペイロードが存在する場合のみ例外を伝播） | `_payload is None` の場合、`_parser.feed_eof()` の例外がサイレントに消える。意図的な設計か確認必要 | `_payload is None` の場合のパーサエラー消失は仕様か？ | 条件付き伝播パターン。`self._payload is not None` の場合のみ `set_exception` → payload が None の場合は例外が drop される | aiohttp corpus audit 2026-05-26 | pending |
| 2026-05-26 | aiohttp/connector.py | 451 | CI26_RACE_HAZARD | 人間確認 | 人間確認 | `results = await asyncio.gather(*waiters, return_exceptions=True)` | コネクタ close 処理（全 waitable を並列実行してログのみ記録） | `return_exceptions=True` は例外収集パターン。`_close_immediately()` が返す awaitable 間の共有状態アクセスの有無を確認必要 | gather される waitable が共有 `self._conns` 等の可変状態を並列書き込みするか？ | `return_exceptions=True` 単独では race hazard 不在を保証しない。await 対象の処理内容を確認すべき | aiohttp corpus audit 2026-05-26 | pending |

## Residuals Confirmed As Implementation-Side Follow-Up

| date | target file | line | signal | current bucket | recommended bucket | code excerpt | runtime role | failure behavior | judgment question | reason | source report | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-26 | pj-sample002/backend/tests/test_e4~8.py, test_e456_performance.py ほか | 10–15 | CI05_DUPLICATE_BLOCK | 根本解決で潰すべきもの | 根本解決で潰すべきもの | `@pytest.fixture def session(): engine=create_engine("sqlite:///:memory:"); Base.metadata.create_all(engine); ...` | テスト DB セットアップフィクスチャ（6+ ファイルに完全重複） | 真陽性。`conftest.py` に集約すれば重複解消。現状はファイルが増えるたびにコピーされている | — | テスト規模が大きくなると fixture の挙動変更が全ファイルに波及しリグレッションリスクが増大する。conftest.py に抽出すべき | pj-sample002 dogfooding scan 2026-05-26 | open |
| 2026-05-26 | pj-sample002/backend/rules/e5_duplicate_order.py | 18 | CI25_ENVIRONMENT_DRIFT | 根本解決で潰すべきもの | 根本解決で潰すべきもの | `past_24h = datetime.now() - timedelta(hours=24)` | 重複注文判定の時刻比較（ローカル時刻依存） | 真陽性。TZ 未設定環境ではローカル時刻が使用され、デプロイ先の TZ によって挙動が変化する。`datetime.now(tz=timezone.utc)` へ修正すべき | — | CI25 検出の既知アンカー（earlier wave で確認済み）。本番環境 TZ≠UTC の場合、24h 窓の計算がずれる | pj-sample002 dogfooding scan 2026-05-26 | open |

## Human-Confirm Residuals Likely Removable Later

| date | target file | line | signal | current bucket | recommended bucket | code excerpt | runtime role | failure behavior | judgment question | reason | source report | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Notes

- `current bucket` is the bucket used in the latest validation report.
- `recommended bucket` is the reviewed next-state if detector or mechanism work
  is later applied.
- items stay here until the detector or human-confirm mechanism is updated and a
  rerun proves the decision.
- 2026-05-25 rerun:
  - `shared/tools/session_start.py` の `CI21_BROAD_EXCEPTION_SWALLOW` residual は、fail-soft helper の exception narrowing と fail-close `sys.exit` recognition の反映後に rerun し、current register から除去した。
  - `shared/tools/session_start.py` の `CI18_PARAMETER_CLUSTER` residual は、lessons matcher を parameter object 化した後の rerun で除去した。
  - `shared/tools/session_start.py` の `RESPONSIBILITY_SPROUT` residual は、Operator View rendering を helper module へ分離した後の rerun で除去した。
