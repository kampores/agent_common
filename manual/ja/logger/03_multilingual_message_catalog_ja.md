# 2.3. 多言語ログメッセージテンプレート辞書およびコードベースロギング (`logging_messages_*.yml`, `log_msg`)

> **所属モジュール**: `agent_common.logger.ProjectLogger`  
> **関連関数/メソッド**: `ProjectLogger.get_log_msg()`, `ProjectLogger.log_msg()`, `ProjectLogger.get_log_id_description()`, `get_log_msg()`  
> **メッセージ辞書ファイル**: `agent_common/src/agent_common/localize/{ko,en,zh,ja}/logging_messages_{lang}.yml`

---

## 1. 概要およびエンタープライズにおける背景

エンタープライズサービスの開発において、ソースコード内部に直接ハードコードされたログメッセージは以下のような重大な問題を引き起こします:

1. **規律違反および保守コストの増大**: AGENTS.md 第1原則（ハードコーディング禁止）に反し、文言修正のたびにコードの再ビルド・再デプロイが必要となる非効率
2. **グローバル運用支援の限界**: 海外運用拠点（NOC）や多国籍エンジニアとの協業時に、特定言語ログによる障害初動の遅延
3. **ログ分析およびメトリクス標準化の欠如**: ログが非定型テキストで記述されるため、同一障害の集計やアラートルールの標準化が困難

`ProjectLogger` は、これらの問題を抜本的に解決するため、**メッセージコードに基づく外部テンプレート辞書連携システム**と**実行時の動的多言語切り替え (KO ⇄ EN ⇄ JA ⇄ ZH)** 機能を備えています。

---

## 2. 中核アーキテクチャおよびテンプレート解析パイプライン

```mermaid
flowchart TD
    A["logger.info('task_start', task_name='移行') の呼び出し"] --> B{"言語判定"}
    B -->|"KO / EN / ZH / JA"| C["localize/{lang}/logging_messages_{lang}.yml"]
    
    C --> E["_search_template_in_level(レベル, コード)"]
    E --> F{"該当レベルで発見？"}
    F -->|"はい"| G["テンプレート取得"]
    F -->|"いいえ"| H{"他レベルセクションの巡回探索"}
    H -->|"発見"| G
    H -->|"未発見"| I["default_str またはコード文字列自体をテンプレートとして使用"]
    
    G --> J["safe_kwargs_dict 処理 (波括弧のエスケープ保護)"]
    I --> J
    J --> K["template.format(**safe_kwargs) の実行"]
    K --> L["フォーマット完了メッセージ文字列の生成"]
    L --> M["stacklevel=2 を適用し呼び出し元行番号でログ記録"]
```

---

## 3. メッセージ辞書 YAML 構造

多言語メッセージファイルはコンポーネント別にモジュール化され、`agent_common/src/agent_common/localize/{lang}/` 配下に配置されます。
### 3.1. 韓国語辞書 (`agent_common/src/agent_common/localize/ko/logging_messages_ko.yml`)

```yaml
logging_messages:
  INFO:
    task_start: "🚀 [{task_name}] 작업이 시작되었습니다. (대상: {target_count:,}건)"
    task_completed: "✅ [{task_name}] 작업이 성공적으로 완료되었습니다."
    data_transfer_progress: "[{task_name}] 처리 진행 중: {processed_count:,}/{total_count:,}건 ({percent:.1f}%)"
  
  WARNING:
    record_skipped: "⚠️ [{task_name}] 제외 조건에 의해 데이터 처리를 건너뜁니다: {reason}"
    retry_attempt: "⚠️ 일시적 연결 실패로 재시도합니다. (시도 횟수: {attempt_count}/{max_retries})"
  
  ERROR:
    connection_failed: "❌ {service_name} 서비스 연결에 실패하였습니다. (사유: {error_msg})"
    schema_validation_failed: "❌ 필수 필드 누락 또는 스키마 검증 실패: {detail}"
```

### 3.2. 英語辞書 (`agent_common/src/agent_common/localize/en/logging_messages_en.yml`)

```yaml
logging_messages:
  INFO:
    task_start: "🚀 [{task_name}] task has started. (Targets: {target_count:,} items)"
    task_completed: "✅ [{task_name}] task has completed successfully."
    data_transfer_progress: "[{task_name}] Transfer progress: {processed_count:,}/{total_count:,} items ({percent:.1f}%)"
  
  WARNING:
    record_skipped: "⚠️ [{task_name}] Record skipped due to exclusion policy: {reason}"
    retry_attempt: "⚠️ Temporary connection failure. Retrying (Attempt: {attempt_count}/{max_retries})"
  
  ERROR:
    connection_failed: "❌ Failed to connect to {service_name}. (Reason: {error_msg})"
    schema_validation_failed: "❌ Required fields missing or schema validation failed: {detail}"
```

---

## 4. 主要機能および実装特徴

### 4.1. 安全な引数置換 (`safe_kwargs_dict`)
ログパラメータとして渡された文字列に波括弧（`{`, `}`）が含まれていても（例: JSON 文字列、正規表現等）、`format()` パース時に `KeyError` や `ValueError` が発生しないようエスケープ処理（`{{`, `}}`）を自動適用します。

```python
safe_kwargs_dict = {
    k: str(v).replace("{", "{{").replace("}", "}}") if isinstance(v, str) else v
    for k, v in kwargs.items()
}
```

### 4.2. 正確な呼び出し元追跡 (`stacklevel=2`)
`logger.info()`, `logger.error()` などのラッパーメソッドを経由しても、ラッパー内部ではなく**実際にこのメソッドを呼び出したビジネスコードのファイル名と行番号**がログヘッダーに正確に記録されるよう `stacklevel=2` を適用しています。

### 4.3. 実行時の動的言語切り替え
プロセスを再起動することなく、グローバル設定または `ConfigLoader` を介して即座に出力言語を変更できます:

- グローバル設定: `Localizer.set_global_language("EN")`
- 設定ローダープロパティ (Setter): `config_loader.language_str = "EN"`
- 現在の言語確認 (Getter): `config_loader.language_str` (➔ `"EN"`, `"KO"`, `"JA"`, `"ZH"`)

対応する言語コードは `KO`、`EN`、`ZH`、`JA` で、ログ言語は次の優先順位で決定されます:

1. `ConfigLoader.language_str` または `Localizer.set_global_language()` で指定した値
2. 環境変数 `AGENT_LOG_LANGUAGE`、`LOGGING_LANGUAGE`、`AGENT_LANGUAGE`、`APP_LANGUAGE`、`LANG` のうち先頭から最初に値があるもの (BCP 47 標準ハイフンロケール自動正規化)
3. `config.yml` の `logging.language_str`
4. デフォルト言語 `KO`

言語コードの正規化ルールと言語別ファイルの探索方法は、[8.1. 言語コードの正規化と言語別リソースファイル探索 (`Localizer`)](../localizer/01_language_codes_and_resource_lookup_ja.md) を参照してください。

### 4.4. `service_name_str` バインドによるサービス文脈自動注入
`ProjectLogger(name_str, service_name_str="")` インスタンス生成時に任意の `service_name_str` パラメータを渡すと、ロガーインスタンスに永続的にバインドされます。
以降の `get_log_msg()` や `get_log_id_description()` の呼び出し時に毎回 `service_name="BigQuery"` を渡す必要がなく、テンプレートの `{service_name}` および `{service_name_str}` 変数に自動注入されます:

```python
logger = ProjectLogger("BqPipeline", service_name_str="BigQuery")
logger.error("connection_failed", error_msg="Timeout")
# ➔ "❌ BigQuery 服务连接失败。(原因: Timeout)"
```

---

## 5. 実践使用コード

### 5.1. コードベースのメッセージロギング

```python
from agent_common.logger import ProjectLogger

logger = ProjectLogger("MigrationService", service_name_str="Cloud_Storage")

# 1. メッセージコードとキーワード引数を用いたロギング
logger.info("task_start", task_name="Cloud_Data_Sync", target_count=50000)

# 2. 進捗ロギング
logger.info(
    "data_transfer_progress",
    task_name="Cloud_Data_Sync",
    processed_count=25000,
    total_count=50000,
    percent=50.0,
)

# 3. エラー発生時のコードベースロギング (service_name 自動置換)
try:
    raise ConnectionTimeoutError("Connection timed out after 30s")
except Exception as e:
    logger.exception("connection_failed", error_msg=str(e))
```

### 5.2. 実行時多言語動的切り替えの例

```python
from agent_common.logger import ProjectLogger
from agent_common import Localizer

logger = ProjectLogger("InternationalBatch")

# デフォルト言語 (KO) での出力
logger.info("task_start", task_name="SyncJob", target_count=100)
# ➔ [INFO] 🚀 [SyncJob] 작업이 시작되었습니다. (대상: 100건)

# 英語モードへの切り替え
Localizer.set_global_language("EN")

logger.info("task_start", task_name="SyncJob", target_count=100)
# ➔ [INFO] 🚀 [SyncJob] task has started. (Targets: 100 items)
```

### 5.3. 文字列テンプレートフォーマット専用関数 (`get_log_msg`)

直接ログを出力せず、フォーマットされたメッセージ文字列のみを取得して外部通知（Slack, Email 等）に利用したい場合は `get_log_msg()` を活用します:

```python
from agent_common.logger import get_log_msg

alert_text = get_log_msg("ERROR", "connection_failed", service_name="Kafka", error_msg="Broker unreachable")
print(alert_text)
# ➔ "❌ Kafka 서비스 연결에 실패하였습니다. (사유: Broker unreachable)"
```

---

## 6. 運用ベストプラクティス

### 6.1. プロジェクト固有メッセージ辞書の拡張例

パッケージ標準辞書に加え、個別プロジェクト独自のビジネスメッセージが必要な場合は、プロジェクトルートの `config/logging_messages_ko.yml` に記述します。  
`ConfigLoader` は **5段階階層マージ (Deep Merge)** により、パッケージ標準辞書を維持したままプロジェクト固有の辞書をスマートにマージします。

```yaml
# <プロジェクトルート>/config/logging_messages_ko.yml
logging_messages:
  INFO:
    task_start: "🔥 [パイプライン開始] {task_name} バッチ起動 (対象予定: {target_count:,}件)"
    medallion_step_completed: "🏅 [{stage_name}] 処理完了: 成功 {success_count:,}件, 除外 {excluded_count:,}件"

  ERROR:
    auth_token_expired: "🚫 認証トークンの失効または更新失敗 ({auth_url}, HTTPステータス: {status_code})"
```

### 6.2. エラーコード命名規約
メッセージコードはスネークケース（`snake_case`）で一貫して記述し、目的と対象を明確に命名してください（例: `db_query_failed`, `file_not_found`, `invalid_payload`）。

---

### 6.3. 例外発生時のメッセージ処理ベストプラクティス：多言語化（Localization）と二重ログ（Double Logging）防止

下位レイヤー（バリデータ、コンテキストビルダー、ドメイン変換クラスなど）で入力値やデータが不正であり、例外（`ValueError`、`TypeError` など）を送出する必要がある場合、コード内に直接エラー文字列をハードコードしたり、安易にロガーを出力すると深刻な不具合が発生します：

#### 1) 潜在的な問題点
* **ハードコーディング問題**: `raise ValueError(f"エラー発生: {key_str}")` のようにソース内に文字列を直接記述すると、**AGENTS.md 第1原則（ハードコーディング禁止）**違反となり、多言語化（Localization）にも対応できません。
* **二重ログ（Double Logging）問題**: 下位関数で `logger.error(...)` を直接呼び出してから `raise ValueError(...)` を送出すると、上位の実行ランナー（例: `PipelineThreadRunner` のワーカースレッドプール）が `except Exception:` で捕捉して再度 `logger.exception(...)` を出力するため、**同一エラー1件に対してログが2回重複出力**され、監視やエラー集計が歪められます。

#### 2) 推奨される設計パターン: "Log or Throw, Never Both" & `get_log_msg()` の活用
下位関数では**一切のログ出力を行わず**、`logger.get_log_msg()` を通じて多言語メッセージ辞書からフォーマット済みテキストのみを生成して例外オブジェクトに渡します。実際のログ出力、スタックトレース記録、エラーカウント集計は、例外を最終的に捕捉する最上位の実行ランナー（Runner）が一元管理します。

```python
# 1. メッセージ辞書の定義 (config/logging_messages_ja.yml または logging_messages.yml)
logging_messages:
  ERROR:
    extract_job_base_date_failed_error: "ECSオブジェクトキーから8桁の作業基準日(YYYYMMDD)を抽出できません: [ECS_Key={ecs_key_str}]"

# 2. 下位ドメイン/ビルダーでの例外送出（画面/ファイル出力は行わず文字列のみ取得）
class RuleContextBuilder:
    def __init__(self):
        self.logger = ProjectLogger(self.__class__.__name__)

    def build_context(self, ecs_key_str: str) -> dict[str, Any]:
        extracted_date_str = StoragePathBuilder.extract_date_from_key(ecs_key_str)
        if not extracted_date_str:
            # get_log_msg() はコンソール/ファイルに出力せず、多言語テンプレートからフォーマット済み文字列のみを返します。
            error_msg_str: str = self.logger.get_log_msg(
                "ERROR",
                "extract_job_base_date_failed_error",
                ecs_key_str=ecs_key_str,
            )
            raise ValueError(error_msg_str)
        ...

# 3. 上位実行ランナー（Runner）での一元ロギングと例外隔離
try:
    context_dict = context_builder.build_context(ecs_key_str)
except Exception as err_obj:
    # 上位でスタックトレースとともに正確に1回のみ記録（二重ログ防止 + 多言語メッセージ保持）
    self.logger.exception(
        "pipeline_worker_exception",
        target_item_str=ecs_key_str,
        error_str=f"[{type(err_obj).__name__}] {err_obj}",
    )
```

#### 3) 3大コアメリット
1. **二重ログ 0%（重複出力の完全防止）**: `get_log_msg()` はハンドラーへのログ出力を一切行わないため、下位層で無駄なログが残りません。
2. **多言語化 100%（ローカライズ完全対応）**: ソースコードに一切の文字列を埋め込まず、グローバル言語設定（`KO`、`EN`、`ZH`、`JA`）に応じて YAML 辞書から動的に適切な文言が適用されます。
3. **正確なメトリクス集計とトレース保持**: 上位ランナーが `logger.exception()` を1回だけ記録するため、スタックトレースが確実に残ると同時にエラー集計カウンターが狂いません。
