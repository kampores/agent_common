# agent_common (日本語)

**[📦 PyPI パッケージ](https://pypi.org/project/agent-common/) · [💻 GitHub ソースコードおよびマニュアル](https://github.com/kampores/agent_common)**

> [ 🇰🇷 한국어 (README_KR.md) ](README_KR.md) | [ 🇺🇸 English (README_EN.md) ](README_EN.md) | [ 🇨🇳 中文 (README_ZH.md) ](README_ZH.md) | [ 🇯🇵 日本語 (README_JP.md) ](README_JP.md)

---

## 🇯🇵 agent_common パッケージ概要

エンタープライズ AI エージェントサービスおよびデータ移行・生成パイプラインのための共通 Python コアライブラリです。統合ロギング、階層型設定ローダー、クラウドおよびデータベースインフラクライアント、動的ツールパーサー、集中エラー処理を提供します。

---

### 📌 主な機能

#### 1. 設定ローダーおよび不変設定オブジェクト (`agent_common.config_loader`)
- **1.1. [階層型 YAML 解析およびディープマージ (Deep Merge)](manual/jp/config_loader/01_hierarchical_yaml_merge_jp.md)**: パッケージ組み込みデフォルト設定 (`agent_common/config/*.yml`) とプロジェクト固有設定 (`config/*.yml`) を動的にマージ。
- **1.2. [不変ドット記法アクセス (`ReadOnlyConfig`)](manual/jp/config_loader/02_readonly_dot_notation_jp.md)**: `config.ecs.endpoint_url`, `config.transfer.max_workers_int` 形式の直感的な属性アクセスとランタイム改ざん防止。
- **1.3. [型サフィックス自動型変換および型保証](manual/jp/config_loader/03_type_coercion_and_guarantee_jp.md)**:
  - `_int`: 自動整数変換および型保証。
  - `_float`: 自動浮動小数点数変換および型保証。
  - `_bool`: 厳格なブール型変換および型保証（Python `bool` または大文字小文字不問の `"true"`, `"false"` をサポートし、`0`, `1` など非ブール値流入時は Fail-Fast 遮断）。
  - `_str`: 自動文字列変換および `.strip()` 空白トリミング。
  - `_list` / `_dict`: リスト / 不変辞書 (`ReadOnlyConfig`) ラッピング保証。
  - 汎用関数 `coerce_type_by_key_suffix` およびネスト辞書一括変換 `coerce_dict_by_key_suffix` により、外部設定ファイル (`rule.yml`, `mapping.yml`) やデータパイプラインを完全サポート。
  - 厳格な Fail-Fast 保証: 型不一致時は詳細な診断例外 (`ValueError`/`TypeError`) を即座に発生。
- **1.4. [Fail-Fast 必須設定検証 (`require_setting()`)](manual/jp/config_loader/04_fail_fast_require_setting_jp.md)**: プログラム起動時に必須設定値が欠落している場合、詳細原因を出力してプロセスを即座に終了。
- **1.5. [ネットワークプロキシ制御 (`_apply_no_proxy`)](manual/jp/config_loader/05_network_proxy_control_jp.md)**: `proxy.no_proxy` 設定を `NO_PROXY` 環境変数に自動反映し、内部通信プロキシをバイパス。
- **1.6. [全定数の設定ファイル外部化および自己修復テンプレート補正 (`ensure_config_file()`)](manual/jp/config_loader/06_ensure_config_self_healing_jp.md)**: コード内の全定数を設定ファイル化、`config.yml` の自動生成および欠落キーの強制補正。

#### 2. 単一行ログフォーマッターおよびロガー (`agent_common.logger`)
- **2.1. [単一行フラット化フォーマッターおよび例外発生源追跡 (`SingleLineFlattenFormatter`)](manual/jp/logger/01_single_line_flatten_formatter_jp.md)**: 全ログおよびトレースバックを1行にフラット化し、`[Origin: ...]` 発生源位置を抽出。集中ログ収集基盤（Logstash, Fluentd, CloudWatch）に最適化。
- **2.2. [一括ロギング構成およびハンドラー制御 (`ProjectLogger.configure`)](manual/jp/logger/02_project_logger_configure_jp.md)**: コンソールおよびファイルハンドラーを動的構成、日付別ディレクトリ分離、ログレベル別ディレクトリ自動振り分け。
- **2.3. [多言語メッセージカタログおよびコードベースロギング (`logging_messages_*.yml`)](manual/jp/logger/03_multilingual_message_catalog_jp.md)**: 設定に基づき日本語/英語/韓国語メッセージ辞書を自動連動、動的言語切り替えおよび安全なテンプレート変数置換。
- **2.4. [タスク進捗統計およびエラー/除外リアルタイム集計 (`record_result`)](manual/jp/logger/04_execution_result_and_error_tracking_jp.md)**: 成功、失敗、除外 (Skip) の3段階分類とマルチスレッド集計。
- **2.5. [タスク結果要約レポート自動生成 (`log_summary`)](manual/jp/logger/05_summary_report_generation_jp.md)**: 「全体 = 成功 + 失敗 + 除外」整合性保証、処理スループット、転送速度、エラー診断を含む標準 Markdown 表を出力。

#### 3. ストレージおよびデータベースクライアント (`agent_common.clients`)
- **3.1. [AWS S3 および Dell ECS オブジェクトストレージクライアント (`S3Client`)](manual/jp/clients/01_s3_ecs_storage_client_jp.md)**: AWS S3 および Dell ECS (S3互換) 接続、起動時 `head_bucket` 検証、ページネーション一覧取得 (`list_objects`)、メタデータ高速取得 (`get_object_size`)、ストリーミング読み込み (`get_object_stream`)、GCS リアルタイム転送と重複スキップ (`transfer_to_gcs`)。
- **3.2. [Google Cloud Storage ストリーミングクライアントおよび多層認証 (`GcsClient`)](manual/jp/clients/02_gcs_cloud_storage_client_jp.md)**: 4段階 GCP 認証階層 (`GOOGLE_APPLICATION_CREDENTIALS_JSON` メモリ JSON -> `GOOGLE_APPLICATION_CREDENTIALS` ファイル -> `credentials_path_str` -> Google ADC)、バケット疎通検証、チャンク単位ストリーム直接アップロード (`upload_stream`)。
- **3.3. [BigQuery バッチロードおよびストリーミング挿入クライアント (`BigQueryClient`)](manual/jp/clients/03_bigquery_batch_and_streaming_load_jp.md)**: テーブルメタデータキャッシュ (`get_table`)、JSON バッチロード Job (`load_table_from_json_data`)、リアルタイムストリーミング挿入 (`insert_rows_json_data`)、同期 SQL クエリ (`query`)、重複防止キー抽出 (`get_existing_keys`)。
- **3.4. [BigQuery 高性能インライン MERGE (Upsert) エンジン (`merge_table_from_json_data`)](manual/jp/clients/04_bigquery_inline_merge_upsert_jp.md)**: 一時テーブル不要で `UNNEST(JSON_QUERY_ARRAY(@json_payload))` によるインライン MERGE INTO 実行、主キー基準の自動 UPDATE/INSERT、作成日時等の初期値保護 (`preserve_columns_list`)、100件チャンク自動分割。
- **3.5. [BigQuery タイムゾーンオフセット変換およびテーブルタイムゾーンモード検証・同期 (`convert_to_bigquery_timestamp`)](manual/jp/clients/05_bigquery_timestamp_and_tz_sync_jp.md)**: 多様な日時文字列の BigQuery 標準タイムスタンプ正規化、タイムゾーンオフセット優先順位 (`timezone_offset_str`)、テーブルメタデータ自動同期および不一致遮断 (Fail-Fast)。

#### 4. 動的ツールローダーおよびテンプレート評価器 (`agent_common.tool_parser`) & 組み込みツール (`agent_common.tool`)
- **4.1. [二元化 Tool ディレクトリ階層探索および動的ロード (`ToolParser.load_tool_function`)](manual/jp/tool_parser/01_dual_tool_hierarchy_discovery_jp.md)**:
  - **優先度 1 (組み込みツール)**: `agent_common/tool/` 配下モジュール（標準組み込みツール）。
  - **優先度 2 (プロジェクトツール)**: `config.yml` 内の `transfer.tool_dir_str` 指定パス（例: `medallion/tool/`）。
- **4.2. [宣言的テンプレート置換および式評価 (`ToolParser.eval`)](manual/jp/tool_parser/02_declarative_template_eval_jp.md)**:
  - 名前空間バインディング: `{ecs.key}`, `{sys.today}`, `{json.title}`。
  - 動的ツール関数呼び出し: `"{code.date_check_to_code(contentInfo.enddate)}"`, `"{path.get_json_name(ecs.key)}"`.
  - パイプ (`|`) フォールバック連鎖とデフォルト値: `"{meta.title|json.title|'デフォルトタイトル'}"`.
- **4.3. [安全な名前空間探索 (`_SafeNamespace`)](manual/jp/tool_parser/03_safe_namespace_navigation_jp.md)**:
  - ドットおよびブラケットアクセス統合、大文字小文字不問探索、欠落キー `""` 返却、ネスト辞書/リストの安全ラッピング。
- **4.4. [組み込み共通日時ツール (`DateTimeUtils`)](manual/jp/tool_parser/04_builtin_datetime_utils_jp.md)**:
  - テーブルルールおよびテンプレート専用日時ツール。タイムゾーン中核計算は `TimeUtils` に委譲。

#### 5. 進捗トラッカー、テーブルフォーマッターおよび時間ユーティリティ (`agent_common.utils`)
- **5.1. [ホストシステムタイムゾーン検出、世界標準時解決および日時正規化 (`TimeUtils`)](manual/jp/utils/01_time_utils_and_timezone_resolution_jp.md)**: ホストシステムタイムゾーン自動検出、世界30以上の標準時解決、ISO 8601 オフセット計算、`parse_datetime` による正規化。
- **5.2. [マルチスレッドリアルタイム進捗追跡およびマイルストーン警告 (`ProgressTracker`)](manual/jp/utils/02_progress_tracker_and_milestones_jp.md)**: リアルタイム進捗率表示 (`[N/Total] (P%)`)、スループットおよび予測残り時間 (ETA) 計算、通常 `INFO` と10%単位マイルストーン `WARNING` 昇格ログ。
- **5.3. [Unicode 全角文字幅計算およびテーブル位置合わせフォーマッター (`TableFormatter`)](manual/jp/utils/03_unicode_table_formatter_jp.md)**: 東アジア文字幅 (`unicodedata.east_asian_width`) 計算による全角・半角混在時の Markdown / コンソール表縦罫線位置合わせ。

#### 6. 共通エラーおよび例外ハンドラー (`agent_common.error_handler`)
- ネットワーク障害、設定エラー、実行時例外の一貫したログ記録と標準処理を提供。

#### 7. 統合 LLM クライアントおよび推論エンジン (`agent_common.llm`)
- **7.1. [モデルプロファイル管理およびテキスト生成](manual/jp/llm/01_model_profiles_and_generation_jp.md)**
- **7.2. [外部チャット API および Fabrix 連携](manual/jp/llm/02_external_api_and_fabrix_jp.md)**
- **7.3. [ローカル GGUF 推論およびモデルキャッシュ](manual/jp/llm/03_local_gguf_inference_jp.md)**
- **7.4. [実行モードおよび条件付きローカル切り替え](manual/jp/llm/04_provider_and_local_fallback_jp.md)**
- **7.5. [推論結果および例外処理](manual/jp/llm/05_inference_results_and_errors_jp.md)**
- **7.6. [Groq 監督官 AI および Antigravity Stop フック](manual/jp/llm/06_groq_supervisor_and_stop_hook_jp.md)**

---

### 🛠️ 使用例 (Usage Examples)

#### 1. グローバル `config` ドットアクセスおよび型保証
```python
from agent_common.config_loader import config

# 1) 型サフィックスによる自動キャスト保証
max_workers: int = config.transfer.max_workers_int       # int 型保証
host: str = config.database.host_str                     # str 型および .strip() 保証
is_active: bool = config.transfer.is_active_bool         # bool 型保証

# 2) 階層的プロパティアクセス
api_url: str = config.services.api_endpoint_url
db_port: int = config.database.port_int
```

#### 2. ToolParser による動的ルール評価
```python
from agent_common.tool_parser import ToolParser

tool_parser = ToolParser()

context_dict = {
    "storage": {"key": "/data/incoming/20260804/sample_document.json"},
    "document": {"expiry_date": "2024-12-31"},
    "sys": tool_parser.build_sys_context(),
}

# 1) ツール関数呼び出しテンプレート評価
date_val = tool_parser.eval("{date.get_today_yyyymmdd()}", context_dict)

# 2) システム名前空間テンプレート評価
today_val = tool_parser.eval("{sys.today}", context_dict)
```

#### 3. ProgressTracker リアルタイム進捗追跡
```python
from agent_common.utils import ProgressTracker
from agent_common.logger import ProjectLogger

logger = ProjectLogger("MyTask")
tracker = ProgressTracker(total_items_int=1000, logger_obj=logger, item_name_str="ファイル")

for file_info in file_list:
    try:
        tracker.increment_success(bytes_int=len(data))
    except Exception as e:
        tracker.increment_failure(error_msg_str=str(e))

# 最終集計レポート出力
tracker.log_summary()
```

#### 4. LlmClient による統合テキスト/SQL生成
```python
from agent_common.llm import LlmClient

llm_client = LlmClient(purpose_str="sql_generator")
response_str = llm_client.generate(
    prompt_str="ユーザー要求: 2026年8月の日次新規加入者統計クエリを作成してください。",
    system_prompt_str="あなたは BigQuery SQL 専門の生成 AI です。"
)

print(f"生成結果 ({llm_client.last_generated_by_str}):\n{response_str}")
```

#### 5. ストレージおよび BigQuery クライアント使用例
```python
from agent_common.clients import S3Client, GcsClient, BigQueryClient

# S3 -> GCS スマート転送 (同一ファイルスキップ)
s3_client = S3Client(bucket_name_str="source-lake")
gcs_client = GcsClient(bucket_name_str="target-lake")

for obj in s3_client.list_objects(prefix_str="raw/events/"):
    s3_client.transfer_to_gcs(
        gcs_client_obj=gcs_client,
        s3_key_str=obj["Key"],
        gcs_blob_name_str=f"lake/{obj['Key'].lstrip('/')}",
        size_int=obj["Size"],
    )

# BigQuery インライン MERGE (Upsert)
bq_client = BigQueryClient(project_id_str="my-project", dataset_id_str="dw", table_id_str="tb_user")
bq_client.merge_table_from_json_data(
    json_data_any=[{"user_id": "U01", "name": "山田太郎", "created_at": "2026-01-01 00:00:00+09:00"}],
    pk_key_str="user_id",
    preserve_columns_list=["created_at"],
)
```

---

### 📖 詳細機能マニュアル (User Manuals)

| 番号 | モジュール / テーマ | マニュアルリンク | 主な内容要約 |
| :---: | :--- | :---: | :--- |
| **1.1** | **階層型 YAML 解析 & ディープマージ** | [01_hierarchical_yaml_merge_jp.md](manual/jp/config_loader/01_hierarchical_yaml_merge_jp.md) | 5段階マージ順序、再帰 `_deep_merge` アルゴリズム、ルート自動探索 |
| **1.2** | **不変ドット記法アクセス (`ReadOnlyConfig`)** | [02_readonly_dot_notation_jp.md](manual/jp/config_loader/02_readonly_dot_notation_jp.md) | ドット記法アクセス、ランタイム改ざん防止 (Read-Only)、不変オブジェクト設計 |
| **1.3** | **型サフィックス自動型変換 & 型保証** | [03_type_coercion_and_guarantee_jp.md](manual/jp/config_loader/03_type_coercion_and_guarantee_jp.md) | `_int`, `_float`, `_bool`, `_str`, `_list`, `_dict` 自動キャストおよび安全性保証 |
| **1.4** | **Fail-Fast 必須設定検証** | [04_fail_fast_require_setting_jp.md](manual/jp/config_loader/04_fail_fast_require_setting_jp.md) | 起動時必須設定の欠落検知、診断ログおよびプロセスの安全な早期終了 |
| **1.5** | **ネットワークプロキシ制御** | [05_network_proxy_control_jp.md](manual/jp/config_loader/05_network_proxy_control_jp.md) | `proxy.no_proxy` 設定の `NO_PROXY` 環境変数自動反映とプロキシバイパス |
| **1.6** | **全定数の設定ファイル外部化とテンプレート補正** | [06_ensure_config_self_healing_jp.md](manual/jp/config_loader/06_ensure_config_self_healing_jp.md) | コード内全定数の外部化、`config.yml` 自動生成および欠落設定の強制補正 |
| **2.1** | **単一行フラット化フォーマッター & 発生源追跡** | [01_single_line_flatten_formatter_jp.md](manual/jp/logger/01_single_line_flatten_formatter_jp.md) | `SingleLineFlattenFormatter`、`[Origin: ...]` 抽出、集中ログ収集最適化 |
| **2.2** | **一括ロギング構成 & ハンドラー制御** | [02_project_logger_configure_jp.md](manual/jp/logger/02_project_logger_configure_jp.md) | `ProjectLogger.configure()`、コンソール/ファイル振り分け、レベル別ディレクトリ分離 |
| **2.3** | **多言語メッセージカタログ & コードベースロギング** | [03_multilingual_message_catalog_jp.md](manual/jp/logger/03_multilingual_message_catalog_jp.md) | `logging_messages_*.yml`、ランタイム言語切り替え、安全な変数置換 |
| **2.4** | **タスク統計 & エラー/除外リアルタイム集計** | [04_execution_result_and_error_tracking_jp.md](manual/jp/logger/04_execution_result_and_error_tracking_jp.md) | 成功/失敗/除外の3段階分類、マルチスレッド環境での指標集計 |
| **2.5** | **タスク結果要約レポート自動生成** | [05_summary_report_generation_jp.md](manual/jp/logger/05_summary_report_generation_jp.md) | `ProjectLogger.log_summary()`、80列整形要約ブロック、スループットとエラー診断 |
| **3.1** | **AWS S3 & Dell ECS ストレージ連携** | [01_s3_ecs_storage_client_jp.md](manual/jp/clients/01_s3_ecs_storage_client_jp.md) | S3/ECS 接続検証、ページネーション一覧取得、GCS ストリーミング転送と重複スキップ |
| **3.2** | **GCS ストリーミングアップロード & 4段階認証** | [02_gcs_cloud_storage_client_jp.md](manual/jp/clients/02_gcs_cloud_storage_client_jp.md) | 4段階認証優先順位、バケット検証、メモリパイプラインによるゼロディスク転送 |
| **3.3** | **BigQuery バッチロード & ストリーミング挿入** | [03_bigquery_batch_and_streaming_load_jp.md](manual/jp/clients/03_bigquery_batch_and_streaming_load_jp.md) | JSON バッチロード vs ストリーミング API、ネストエラー展開、既存キー重複防止 |
| **3.4** | **BigQuery インライン MERGE (Upsert) エンジン** | [04_bigquery_inline_merge_upsert_jp.md](manual/jp/clients/04_bigquery_inline_merge_upsert_jp.md) | 一時テーブル不要のインライン MERGE、UNNEST パラメータバインディング、100件分割 |
| **3.5** | **BigQuery タイムゾーン変換 & モード同期** | [05_bigquery_timestamp_and_tz_sync_jp.md](manual/jp/clients/05_bigquery_timestamp_and_tz_sync_jp.md) | ISO/圧縮日時正規化、UTC/KST モード、テーブルメタデータ同期および Fail-Fast |
| **4.1** | **二元化 Tool ディレクトリ探索 & 動的ロード** | [01_dual_tool_hierarchy_discovery_jp.md](manual/jp/tool_parser/01_dual_tool_hierarchy_discovery_jp.md) | 組み込み(優先1) vs ローカル(優先2) 探索、3段階関数内省、キャッシュ機構 |
| **4.2** | **宣言的テンプレート置換 & 式評価** | [02_declarative_template_eval_jp.md](manual/jp/tool_parser/02_declarative_template_eval_jp.md) | `ToolParser.eval()`、関数直接呼び出し、名前空間バインド、パイプ (`\|`) フォールバック |
| **4.3** | **安全な名前空間探索 (`_SafeNamespace`)** | [03_safe_namespace_navigation_jp.md](manual/jp/tool_parser/03_safe_namespace_navigation_jp.md) | ドット/インデックス統一、大文字小文字不問、欠落時 `""` 返却、再帰ラッピング |
| **4.4** | **組み込み共通日時ツール (`DateTimeUtils`)** | [04_builtin_datetime_utils_jp.md](manual/jp/tool_parser/04_builtin_datetime_utils_jp.md) | ルール/テンプレート専用日時ツール、`TimeUtils` 連携、ISO タイムスタンプ生成 |
| **5.1** | **ホストタイムゾーン検出 & 世界標準時解決** | [01_time_utils_and_timezone_resolution_jp.md](manual/jp/utils/01_time_utils_and_timezone_resolution_jp.md) | `TimeUtils`、OS/コンテナタイムゾーン検出、30+標準時解析、datetime 正規化 |
| **5.2** | **マルチスレッド進捗追跡 & マイルストーン** | [02_progress_tracker_and_milestones_jp.md](manual/jp/utils/02_progress_tracker_and_milestones_jp.md) | `ProgressTracker`、進捗率 (`%`)、スループット、ETA 計算、`WARNING` 昇格ログ |
| **5.3** | **Unicode 全角幅計算 & テーブル縦線整列** | [03_unicode_table_formatter_jp.md](manual/jp/utils/03_unicode_table_formatter_jp.md) | `TableFormatter`、`east_asian_width` に基づく全角(2幅)・半角(1幅)整列 |
| **7.1** | **モデルプロファイル管理およびテキスト生成** | [01_model_profiles_and_generation_jp.md](manual/jp/llm/01_model_profiles_and_generation_jp.md) | `agent_common.llm` |
| **7.2** | **外部チャット API および Fabrix 連携** | [02_external_api_and_fabrix_jp.md](manual/jp/llm/02_external_api_and_fabrix_jp.md) | `agent_common.llm` |
| **7.3** | **ローカル GGUF 推論およびモデルキャッシュ** | [03_local_gguf_inference_jp.md](manual/jp/llm/03_local_gguf_inference_jp.md) | `agent_common.llm` |
| **7.4** | **実行モードおよび条件付きローカル切り替え** | [04_provider_and_local_fallback_jp.md](manual/jp/llm/04_provider_and_local_fallback_jp.md) | `agent_common.llm` |
| **7.5** | **推論結果および例外処理** | [05_inference_results_and_errors_jp.md](manual/jp/llm/05_inference_results_and_errors_jp.md) | `agent_common.llm` |
| **7.6** | **Groq 監督官 AI および Antigravity Stop フック** | [06_groq_supervisor_and_stop_hook_jp.md](manual/jp/llm/06_groq_supervisor_and_stop_hook_jp.md) | `agent_common.llm` |

---

### 🚀 インストールおよびビルドガイド (Installation and Build Guide)

#### 📦 Wheel パッケージビルド (.whl)
新バージョンとしてパッケージングして `.whl` ファイルをビルドする場合、`scripts/build_agent_common_whl.py` または `agent_common` ディレクトリ内で以下のコマンドを実行します。

##### 1. クローズドネットワーク環境（オフラインビルド）
外部 PyPI 接続を完全に遮断するため、`--no-index`, `--no-build-isolation`, `--no-deps` オプションを指定します。

```bash
# ルートディレクトリから自動ビルドスクリプトを実行（推奨）
python scripts/build_agent_common_whl.py

# または pip wheel を直接実行
pip wheel ./agent_common --no-index --no-build-isolation --no-deps -w whls/
```

##### 2. インターネット接続環境（オンラインビルド）

```bash
# pip wheel を利用
pip wheel ./agent_common --no-deps -w whls/

# または build モジュールを利用
python -m build agent_common --wheel -o whls/
```

#### Wheel パッケージのインストール
```bash
# 開発環境（Editable モード - 軽量コアインストール）
pip install -e agent_common

# 開発環境（クラウドクライアント extras 含む）
pip install -e "agent_common[clients]"

# 本番環境（Wheel パッケージのインストール）
pip install dist/agent_common-0.4.78-py3-none-any.whl
```

#### 🌐 公式 PyPI 配布（管理者専用）

```bash
# 1. ビルドツールの更新
pip install build twine

# 2. パッケージビルド（sdist および wheel 同時作成）
python -m build

# 3. 配布アーカイブの検証
python -m twine check dist/*

# 4. PyPI アップロード
python -m twine upload dist/agent_common-0.4.92*
```

---

### 📋 バージョン変更履歴 (Changelog)

詳細なバージョン変更履歴は [CHANGELOG_JP.md](CHANGELOG_JP.md) をご参照ください。
