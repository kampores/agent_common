# バージョン変更履歴 (Changelog)

> [ KO 한국어 (CHANGELOG_KO.md) ](CHANGELOG_KO.md) | [ EN English (CHANGELOG_EN.md) ](CHANGELOG_EN.md) | [ ZH 中文 (CHANGELOG_ZH.md) ](CHANGELOG_ZH.md) | [ JA 日本語 (CHANGELOG_JA.md) ](CHANGELOG_JA.md)

### v0.4.97 (2026-10-05)

- **設定ファイルの自動生成・自動補正の書き込み対象をクラス単位で選択 (ルール 1.7.5、4.2 準拠、互換性変更)**:
  - 新規設定 `config_loader.config_file_auto_repair_dict`: `<クラス名>_bool` 形式のキー (例: `BigQueryClient_bool`) でクラスごとの有効・無効を指定する辞書。既定値はすべて `false` で、`ensure_config_file()` は値が `true` のクラスの既定設定のみを `config.yml` に書き込む。
  - 対象クラス: `ConfigLoader`, `ProjectLogger`, `S3Client`, `GcsClient`, `GcpCredentialResolver`, `BigQueryClient`, `ProgressTracker`, `TableFormatter`, `ToolParser`, `LlmClient`。各クラスに、書き込む既定設定を保持する `DEFAULT_SCHEMA_DICT` クラス属性を追加。
  - 呼び出し側プログラムのスキーマ (`register_schema()` の登録分、`default_schema` 引数) は従来どおり常に生成・補正。
  - 値は `_bool` 接尾辞の規則で解釈 (`true`/`false` および同義の文字列、それ以外は即時エラー)。有効にしたキーに対応するクラスが `agent_common` に見つからない場合は警告ログ `config_auto_repair_unknown_class` を出力してスキップ (4 言語のメッセージを追加)。
  - 互換性: 以前のバージョンは `LlmClient` を使わなくても `llm`、`llm_pool` を `config.yml` に自動追加していたが、今後は追加しない。必要な場合は `LlmClient_bool: true` を指定。
- **グローバルスキーマ登録メソッドを追加 (ルール 1.5.4 準拠)**:
  - `ConfigLoader.register_schema_globally(schema_dict)`: 渡されたスキーマをグローバルスキーマレジストリに登録。`ReadOnlyConfig.register_schema()` が 3 か所で呼び出していたが `agent_common` に定義がなく、その分岐に入ると `AttributeError` になっていた問題を解消。
  - `ConfigLoader.register_enabled_class_schemas_globally()`: `config_loader.config_file_auto_repair_dict` で `true` のクラスの `DEFAULT_SCHEMA_DICT` だけをグローバル登録。`ensure_config_file()` が最初に呼び出すため、有効にしたクラスの既定設定はファイルへの書き込みと実行時の既定値の両方に適用される。
  - 呼び出し側プログラムのスキーマで登録済みの値は、クラスの既定値で上書きしない。
- **LLM 既定設定をパッケージ既定設定ファイルへ移動**:
  - `llm.py` がインポート時および `LlmClient` 生成時に `register_schema()` でグローバル登録していた動作を削除し、同じ値 (`llm.router_model_str`、`llm.sql_generator_model_str`、`llm.system_prompt_str`、`llm.default_purpose_str`) を `default_agent_common.yml` に定義。実行時の設定値は同一。
- **`clients.py` のモジュールスキーマをクラス別に分割**:
  - モジュールレベルの `APP_DEFAULT_SCHEMA_DICT` を削除し、`S3Client`、`GcsClient`、`GcpCredentialResolver`、`BigQueryClient` の `DEFAULT_SCHEMA_DICT` に分割。共用キー `transfer.timeout_seconds_int` は 3 つのクライアントそれぞれに含める。
  - どのクラスも読み取っていなかった `transfer.chunk_size_int`、`bigquery.max_retries_int` をスキーマから削除。
- **`logger.py` 既定スキーマの `logging.log_file_str` を修正**:
  - パッケージ既定設定 (`default_agent_common.yml`) と異なっていたパステンプレートを同じ値に統一し、`ProjectLogger` を有効にしたときに実際に適用されている既定値と異なるパスが書き込まれないようにした。
- **`logging.level_dict` の参照から接尾辞なしキーへのフォールバックを削除 (ルール 1.5.3 準拠、互換性変更)**:
  - `ProjectLogger.configure` がログレベルを探す順序を、`<プログラム名>_str` キー、`default` キーの 2 段階に整理。接尾辞のない `<プログラム名>` キーは認識しなくなるため、`<プログラム名>_str` に変更する必要がある。
- **マニュアル `1.6` の補足 (ルール 4.2 準拠)**:
  - 4 言語のマニュアルに `2.1` 節を追加し、クラス単位の選択設定、クラスごとの書き込み項目、初回実行時の適用方法を説明。

### v0.4.96 (2026-10-04)

- **言語識別子を ISO 639-1 言語コードに統一 (ルール 1.1.3, 4.2 準拠、互換性変更)**:
  - 国コード形式だった `KR`、`JP` を言語コード `KO`、`JA` に変更。`EN`、`ZH` はそのままで、対応言語は `KO`、`EN`、`ZH`、`JA`。
  - デフォルト言語および `logging.language_str` のデフォルト値を `KR` から `KO` に変更。
  - `Localizer` から国コードの別名 (`KR`, `JP`, `CN`, `US`) とファイル接尾辞の相互探索 (`kr`↔`ko`, `jp`↔`ja`, `zh`↔`cn`) を削除。認識できない値は従来どおりデフォルト言語 `KO` として扱われるため、設定で `JP` を使用していた場合は `JA` への変更が必要。
  - ファイル名変更: `logging_messages_kr.yml` → `logging_messages_ko.yml`、`logging_messages_jp.yml` → `logging_messages_ja.yml`。
  - 文書パス変更: `manual/kr` → `manual/ko`、`manual/jp` → `manual/ja`（ファイル接尾辞 `_kr.md` → `_ko.md`、`_jp.md` → `_ja.md`）、`CHANGELOG_KR.md` → `CHANGELOG_KO.md`、`CHANGELOG_JP.md` → `CHANGELOG_JA.md`、`AGENTS_KR.md` → `AGENTS_KO.md`、`AGENTS_DOCS_ENV_KR.md` → `AGENTS_DOCS_ENV_KO.md`。README と `pyproject.toml` のリンクもあわせて更新。
- **`Localizer` マニュアルの新設と多言語ドキュメントの補完 (ルール 4.2 準拠)**:
  - マニュアル `8.1 言語コードの正規化と言語別リソースファイル探索` (`manual/*/localizer/01_language_codes_and_resource_lookup_*.md`) を 4 カ国語で新設し、README 主要機能に `8. 言語ローカライザー` セクションとマニュアル一覧の項目を追加。
  - マニュアル `2.3 多言語ログメッセージテンプレート辞書` に、4 言語の辞書ファイルとログ言語決定の優先順位を反映。
- **ドキュメント内の `agent_common.utils` 表記を実際のモジュールパスに修正 (ルール 4.2 準拠)**:
  - 存在しない `agent_common.utils` モジュールを指していた README とマニュアルの表記を、`agent_common.time_utils`、`agent_common.progress_tracker`、`agent_common.table_formatter` に修正。
  - 実行すると `ModuleNotFoundError` になっていたサンプルコードの `from agent_common.utils import ...` を `from agent_common import ...` に修正。
- **言語移動リンクの国旗絵文字を言語コードに置き換え (ルール 4.2 準拠)**:
  - README と CHANGELOG 冒頭の言語移動リンクにある国旗絵文字（一部の環境では国コード `KR`、`US`、`CN`、`JP` として表示される）を、言語コード `KO`、`EN`、`ZH`、`JA` に置き換え。
  - README の言語別セクション見出しから国旗絵文字を削除し、移動リンクのアンカーを新しい見出し（`#agent_common-パッケージ-日本語` など）に合わせて更新。

### v0.4.95 (2026-10-04)

- **`ProjectLogger.get_log_id_description` のローカル変数名を修正 (ルール 1.6.1, 1.6.2, 4.2 準拠)**:
  - 型サフィックスがなく省略形を使っていた `template_val` を、`get_log_msg` と同じ `template_str` に変更。
  - 動作の変更なし。
- **SDK 遅延読み込み関数をクライアントクラス内部へ移動 (ルール 1.4.1, 4.2 準拠)**:
  - モジュールレベル関数 `_get_boto3`, `_get_gcs`, `_get_bigquery` を、それぞれ `S3Client`, `GcsClient`, `BigQueryClient` の `@classmethod` に移動。
  - モジュールレベルのキャッシュ変数 (`_boto3_module`, `_boto_config_cls`, `_storage_module`, `_bigquery_module`, `_service_account_module`) を各クラス変数に移動し、`global` 宣言を削除。
  - 動作の変更なし。
- **GCP 認証解決専用クラス `GcpCredentialResolver` の新設と公開 (ルール 1.4.1, 1.4.7, 1.6.2, 4.2 準拠)**:
  - モジュールレベル関数 `_resolve_gcp_credentials` を削除し、`GcpCredentialResolver.resolve()` へ移行。4 段階の認証優先順位は従来どおり。
  - `GcsClient`, `BigQueryClient` は継承ではなくコンポジションで `self.credential_resolver` を保持し、どちらか一方のクライアントだけを切り出しても他方に依存しない構成に変更。
  - `google.oauth2.service_account` の遅延読み込みを `GcpCredentialResolver` に一元化。`GcsClient._get_gcs()`, `BigQueryClient._get_bigquery()` はタプルではなく自身のモジュールのみを返却。
  - 公開 API (`from agent_common import GcpCredentialResolver`) として登録し、GCS・BigQuery 以外の GCP サービスでも再利用可能。
  - 省略形の変数名を整理: `val_str`, `cred_path`, `cred_err` → `env_credentials_path_str`, `credentials_file_path`, `credentials_error`。
  - `google-auth` 未インストール時、`ImportError` はクライアントの `_connect` で `ConnectionError` にラップされて送出。
  - マニュアル `3.6 GCP サービスアカウント認証リゾルバー` (`06_gcp_credential_resolver_*.md`) を 4 カ国語で新設し、README の主要機能・使用例・マニュアル一覧に反映。
- **KST-as-UTC タイムスタンプモードの削除 (ルール 4.2 準拠、互換性変更)**:
  - 現地時刻の数字を `+00:00` として保存していた KST-as-UTC モードを削除。現地時刻をそのまま表示したい場合は、`DATETIME` 列と `convert_to_bigquery_datetime` を使用。
  - 削除項目: 設定 `bigquery.kst_as_utc_timestamp_bool`、属性 `BigQueryClient.kst_as_utc_timestamp_bool`、メソッド `BigQueryClient.validate_and_sync_table_timestamp_mode()`。
  - 削除されたログメッセージキー: `table_timestamp_mode_legacy_warning`, `table_timestamp_mode_mismatch`, `table_get_failed`, `table_metadata_update_failed`。
  - `convert_to_bigquery_timestamp` は、決定されたタイムゾーンオフセット（元データの明記値 → `default_tz_offset_str` → `timezone_offset_str` → システムタイムゾーン）を常に付与して返却。
- **マニュアル `3.5` の全面改訂と文書番号の整理 (ルール 4.2 準拠)**:
  - マニュアルのファイル名を `05_bigquery_timestamp_and_tz_sync_*.md` から `05_bigquery_timestamp_and_datetime_conversion_*.md` に変更し、`TIMESTAMP`・`DATETIME` の 2 つの変換メソッドを中心に 4 カ国語で書き直し。これまで欠けていた `convert_to_bigquery_datetime` の仕様と使用例を追加。
  - README 主要機能の `3.6 BigQuery 標準 DATETIME 変換` 項目を `3.5` に統合し、機能番号とマニュアルファイル (01〜06) が 1:1 で対応するよう整理。

### v0.4.94 (2026-10-04)

- **PyPI README 言語移動アンカーリンクの修正 (ルール 4.2 準拠)**:
  - PyPI レンダラーが HTML `<a id="...">` タグの `id` 属性を除去するため、v0.4.93 の `#kr`, `#en`, `#zh`, `#jp` リンクが機能しなかった問題を修正。
  - 従来 KR/EN で正常動作していた方式と同様に、Markdown 見出しの自動スラッグ (`#-agent_common-패키지-한국어`, `#-agent_common-package-english`, `#-agent_common-软件包-中文`, `#-agent_common-パッケージ-日本語`) で 4 カ国語リンクを統一。
  - 不要になった `<a id>` タグを削除。

### v0.4.93 (2026-10-04)

- **PyPI ページでの全閲覧に対応する 4 カ国語統合 README の構築 (ルール 4.2 準拠)**:
  - 単一 README のみをレンダリングする PyPI のプラットフォーム特性に対応し、韓国語 (KR)、英語 (EN)、中国語 (ZH)、日本語 (JP) の 4 カ国語ドキュメントを `README.md` 1 ファイルへ完全統合 (順序: `kr` -> `en` -> `zh` -> `jp`)。
  - 上部にダイレクトアンカーナビゲーション (`#kr`, `#en`, `#zh`, `#jp`) を配置し、GitHub / PyPI の双方で完全動作する絶対 URL マニュアルリンク体系を構築。
  - 重複していた `README_*.md` 分割ファイルを完全整理・削除。
- **`pyproject.toml` 多言語プロジェクトリンク (`project.urls`) の 4 カ国語への拡充**:
  - PyPI サイドバーリンクに韓国語・英語に加え、中国語 (ZH) および日本語 (JP) の変更履歴 (`Changelog`) と詳細マニュアル (`Manual`) リンクを公式登録。

### v0.4.92 (2026-10-04)

- **言語ローカライズモジュール (`Localizer`) の導入および単一責任原則 (SRP) に基づく言語・ログ設定の分離 (ルール 1.4.1, 1.5.1, 4.2 準拠)**:
  - `Localizer`: 多言語コード正規化、グローバル言語状態管理、および汎用多言語リソースファイルパス探索 (`resolve_localized_file`, `resolve_localized_path_from_list`) を担当する専用モジュールを新設。
  - `Localizer` から `logging` 設定ディクショナリ、ログ専用環境変数 (`AGENT_LOG_LANGUAGE`)、ハードコードされた `logging_messages` ファイル名、およびログレベル構造への依存性を完全分離・排除。
  - `ConfigLoader`: ログ専用環境変数 (`AGENT_LOG_LANGUAGE`, `LOGGING_LANGUAGE`) および `logging.language_str` 設定を解析する専用メソッド (`_resolve_logging_language`) を分離し、言語コード正規化を `Localizer` に委譲。
  - `ProjectLogger`: `APP_DEFAULT_SCHEMA_DICT` のデフォルトログ言語を `KR` に確定し、ログフォーマット、ログレベル別テンプレート検索、およびサマリーレポートのエラー説明生成を担当。
- **国・言語コード標準規格の統一 (`KR`, `JP`, `EN`, `ZH`)**:
  - マニュアルディレクトリ (`manual/kr/`, `manual/jp/`)、ファイル名 (`*_kr.md`, `*_jp.md`)、および README (`README_KR.md`, `README_JP.md`) と完全一致させ、デフォルト言語コードを `KO` から `KR` へ変更。
  - `default_agent_common.yml` および `config.yml` の `logging.language_str` デフォルト値を `KR` に設定。
  - `logging_messages_kr.yml`、`logging_messages_zh.yml`、および `logging_messages_jp.yml` を新規追加し、4カ国語 (KR, EN, ZH, JP) 標準ログメッセージテンプレートを完備。
  - `CHANGELOG_KR.md` を作成し全ドキュメントの多言語ナビゲーションバーを更新、`KO` 重複ファイルを完全整理。
- **スタンドアロン配布モジュール (`load_util.py`, `ig_gcs_bigquery_insert.py`) の言語設定を `KR` に固定**:
  - 配布実行環境においてログ言語を厳格に `KR` に固定し、不要な多言語分岐およびヒューリスティックコードを削除。

### v0.4.91 (2026-10-03)

- **ロギング標準規格の整理、ラッパー関数の排除およびモジュール同期 (ルール 1.3.1, 1.4.6, 1.5.3, 1.6.1, 4.2 準拠)**:
  - `logging.format_str`: Python 標準 `LogRecord` 組み込み属性 (`%(asctime)s`, `%(levelname)s`, `%(name)s`, `%(filename)s:%(lineno)d`, `%(message)s`) および唯一のカスタム注入属性 `%(caller_str)s` 体系へ統一。
  - `SingleLineFlattenFormatter`: 不要に Python 標準属性を多重複製していた形式的メソッド `formatMessage` を完全削除 (ルール 1.4.6 準拠)。
  - `logging.log_file_str`: パステンプレート引数を標準型サフィックス `{app_name_str}`, `{log_level_str}` に統一し、不要な大文字小文字防御パラメータ (`APP_NAME`, `LOG_LEVEL`, `app_name`, `log_level`) および一時変数を全廃。
  - `_safe_log_record_factory` およびログレコード属性から非標準・レガシー別名 (`record.className`, `record.caller`, `fallback_class_name`) を全面削除し、`record.class_name_str`, `record.caller_str`, `fallback_class_name_str` に単一化。
  - `ProjectLogger.configure`: 初期レガシーサードパーティロガー (`metricflow`, `metricflow_semantics`, `urllib3`, `httpx`) のログレベル強制抑制ハードコードを完全削除。
  - `load_util.py` を `agent_common/logger.py` と 100% 同期させ、ハードコードされたフォールバック定数 (Fail-Fast ルール 1.3.1 違反) を根絶。

### v0.4.90 (2026-10-01)

- **`BigQueryClient.get_existing_records_metadata` メソッドの新規実装 (ルール 1.4, 1.5, 4.2 準拠)**:
  - BigQuery テーブルから指定された PK リストに対応するレコードのメタデータ（状態コード `asstStusCd`、更新日時 `orignAmndHms` 等）を高速一括取得し、`{pk_str: {カラム名: 値}}` 辞書で返却するメソッドを新設。
  - BigQuery API リクエストサイズ上限 (HTTP 413) 回避のため、`UNNEST(@pk_list)` に基づく 5,000件チャンク分割クエリ実行構造を適用。
  - 事前定義された標準ログテンプレート (`db_existing_records_loaded`, `existing_records_metadata_fetch_failed`) と連携。

### v0.4.89 (2026-10-01)

- **設定ローダーおよびラッパー再帰関数のリソース過剰消費 (CWE-674) 防御措置 (ルール 1.3, 1.4, 4.2 準拠)**:
  - `ReadOnlyConfig.register_schema`, `ReadOnlyConfig.apply_cli_overrides` に最大深度制限 (`max_depth_int=10`) および明示的な基底条件脱出文 (Early Return) を完備。
  - `ConfigLoader._deep_merge` および `ConfigLoader._interpolate_env_vars` 内部再帰ロジックに最大探索深度制限 (`max_depth_int=20`) を適用し、スタックオーバーフローおよび無限ループのリスクを遮断。

### v0.4.88 (2026-10-01)

- **`BigQueryClient.convert_to_bigquery_datetime` メソッドの新規実装 (ルール 1.4, 4.2 準拠)**:
  - BigQuery の `DATETIME` 型仕様に適合させ、多様な形式の元日時文字列（ISO 8601、空白区切り、14桁/8桁数値等）を標準日時 (`YYYY-MM-DD HH:MM:SS`) へ変換するメソッドを新設。
  - パースエラーを引き起こすタイムゾーンオフセットを除外し、タイムゾーン付きデータは韓国標準時 (KST) へ正規化変換して返却。

### v0.4.87 (2026-10-01)

- **`_SafeNamespace` 無限再帰 (`RecursionError`) 欠陥の解消 (ルール 1.3, 1.4, 4.2 準拠)**:
  - `_SafeNamespace.__getattr__` での `hasattr(self, "_data")` 呼び出し時に属性未存在で再帰的に `__getattr__` が呼ばれる不具合を遮断。
  - `self.__dict__.get("_data")` 直接アクセス方式へ転換し、インスタンス初期化時に `self._data = None` 基本属性を明示的に保証。

### v0.4.86 (2026-10-01)

- **`SingleLineFlattenFormatter` およびロガー階層の単一責任原則 (SRP) 分離 (ルール 1.4.1, 4.2 準拠)**:
  - `SingleLineFlattenFormatter` 内部に混在していたコールスタック検査および `caller` / `className` 抽出ルーチンをロガー階層 (`_safe_log_record_factory`) へ完全移管。
  - `LogRecord` 生成時に常に `caller` と `className` が設定されるよう保証し、フォーマッターの種類に関わらず `KeyError` を防止。
  - `SingleLineFlattenFormatter` は改行のフラット化 (`\n` -> 空白) と最終文字列フォーマットのみを純粋に担当。

### v0.4.85 (2026-10-01)

- **`TimeUtils.format_elapsed_time` 所要時間フォーマットユーティリティメソッド新設 (ルール 1.4, 4.2 準拠)**:
  - パイプライン各段階および全体作業の所要秒数を可読性の高い時間文字列（例: `1h 23m 45.67s`, `2m 15.30s`, `4.25s`）へ変換するクラスメソッドを追加。

### v0.4.84 (2026-09-30)

- **`_SafeNamespace(dict)` 統合および Fail-Fast の実現 (ルール 1.5.3, 1.4.6, 4.2 準拠)**:
  - 大文字小文字無視探索および空文字列 (`""`) 暗黙返却の防御コードを全面撤廃し、フィールド欠落時に `AttributeError` / `KeyError` を発生させて Fail-Fast を実現。
  - `dict` 継承マッピングクラスとして構造化し、`eval()` のローカル変数辞書とドット属性アクセスを単一クラスで統合。
  - `agent_common` トップレベルパッケージで正式公開 (`__all__`)。

### v0.4.83 (2026-09-29)

- **`utils.py` 循環インポート欠陥の解消および単一責任原則 (SRP) に基づくモジュール分離 (`time_utils.py`, `progress_tracker.py`, `table_formatter.py`)**:
  - `TimeUtils`: ホストシステムローカルタイムゾーン自動検出、世界標準時解決および日時正規化専任インフラモジュール。
  - `ProgressTracker`: バッチ処理リアルタイム進捗追跡、スループットおよび残り時間 (ETA) 計算、マイルストーン警告専任モジュール。
  - `TableFormatter`: Markdown およびコンソール表縦罫線位置合わせ・東アジア文字幅計算専任モジュール。

### v0.4.82 (2026-09-28)

- **入力パラメータおよび日付検証標準ログテンプレート新設 (`validation` セクション)**:
  - `invalid_date_format`: 日付フォーマットエラー通知 (`key_str`, `val_str`, `message_str`)。
  - `invalid_date_range`: 日付範囲エラー通知 (`start_date_str`, `end_date_str`, `message_str`)。
- **設定ファイル自動生成/自己修復および BigQuery テーブルメタデータログテンプレート正式登録**:
  - `config_auto_create_failed`, `config_auto_repair_failed`: 設定自己修復失敗テンプレート。
  - `table_get_failed`, `table_metadata_update_failed`, `table_timestamp_mode_mismatch`: テーブルメタデータログテンプレート。
  - `storage_clean_failed`: `storage_type_str` ベースの汎用キーへ一元化。
- **全ログプレースホルダーおよび引数の型サフィックス (`_str`, `_int` 等) 標準化**。

### v0.4.81 (2026-09-28)

- **テーブル WRITE_TRUNCATE カウントダウンおよび分割バッチロード汎用ログテンプレート追加**:
  - `table_truncate_countdown`, `table_truncate_tick`, `table_truncate_countdown_completed`: データ消失防止カウントダウンテンプレート。
  - `db_bulk_load_batch_started`, `db_bulk_load_batch_completed`: 大量レコード分割バッチロード追跡テンプレート。

### v0.4.80 (2026-09-23)

- **BigQueryClient に WHERE 条件に基づく安全削除 (DELETE DML) メソッドを追加 (`delete_rows`)**:
  - 指定された条件式に合致する行を一括削除し、削除件数 (`affected_rows_int`) を返却。
  - **全件削除防止フェイルセーフ**: 条件が空または恒真 (`1=1`, `TRUE`, `''=''`) の場合は即座に `ValueError` を発生。

### v0.4.78 (2026-09-21)

- **AI 開発要求ガイドおよび統合 LLM マニュアルの追加**:
  - AI に対する要件・PyPI/GitHub リンク・機能番号の伝達例と段階的拡張ガイドを追加。
  - 統合 LLM クライアントマニュアルを追加し、設定・外部 API・ローカル GGUF・環境変数・例外処理を解説。
  - Groq 監督官 AI および Antigravity Stop フックの検査仕様を明文化。

---

初期の過去バージョン履歴については [CHANGELOG_KR.md](CHANGELOG_KR.md) または [CHANGELOG_EN.md](CHANGELOG_EN.md) をご参照ください。
