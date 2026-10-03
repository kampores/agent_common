# バージョン変更履歴 (Changelog)

> [ 🇰🇷 한국어 (CHANGELOG_KR.md) ](CHANGELOG_KR.md) | [ 🇺🇸 English (CHANGELOG_EN.md) ](CHANGELOG_EN.md) | [ 🇨🇳 中文 (CHANGELOG_ZH.md) ](CHANGELOG_ZH.md) | [ 🇯🇵 日本語 (CHANGELOG_JP.md) ](CHANGELOG_JP.md)

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
