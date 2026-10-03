# 7.1. モデルプロファイル管理およびテキスト生成

[LLM マニュアル一覧](01_unified_llm_client_jp.md)

## 1. 概要と推奨される実装手順

`LlmClient` は、外部チャット API とローカル GGUF モデルを同一の `generate()` インターフェースで透過的に呼び出します。テキスト要約、分類、SQL 文字列の生成などに活用できます。SQL の直接実行や対話履歴の永続化は行わず、各呼び出し時にシステムメッセージとユーザーメッセージを送信します。

初めは、**1つのモデルへプロンプトを送信して応答を受信する最小機能**から実装してください。正常に応答が得られることを確認した上で、用途別のモデル切り替え、ローカル実行、条件付きフォールバックなどを順次追加していきます。

## 2. 設定の準備と最小限の呼び出し

Python 3.10 以上および `agent-common` パッケージが必要です。外部 API 呼び出しには標準ライブラリ `urllib.request` を使用します。ローカル GGUF 推論には別途 `llama-cpp-python` とモデルファイルが必要です。

プロジェクトの `config/config.yml` と `config/llmpool.yml` を準備して実行します。

`config/config.yml`:

```yaml
llm:
  default_purpose_str: sql_generator
  sql_generator_model_str: text_generator
  router_model_str: text_generator
  system_prompt_str: 要求に対して日本語で簡潔に回答してください。

generation_request:
  prompt_str: データ移行作業の目的を一文で説明してください。
```

`config/llmpool.yml`:

```yaml
llm_pool:
  text_generator:
    provider_str: external
    enabled_bool: true
    api_format_str: standard
    api_key_env_str: EXTERNAL_LLM_API_KEY
    base_url_str: https://your-llm-endpoint.example/v1
    chat_completions_path_str: /chat/completions
    model_str: your-server-model-name
    timeout_seconds_int: 60
    max_tokens_int: 512
    temperature_float: 0.0
```

`base_url_str` と `model_str` を実際のエンドポイントとモデル名に設定し、環境変数 `EXTERNAL_LLM_API_KEY` を設定した後の最小呼び出し例は以下の通りです。

```python
from agent_common.config_loader import config
from agent_common.llm import LlmClient

llm_client_obj = LlmClient()
response_str = llm_client_obj.generate(
    prompt_str=config.generation_request.prompt_str,
)
```

`response_str` は生成された文字列、または `None` です。呼び出し元が結果の保存や表示を担当し、[7.5 戻り値および例外ルール](05_inference_results_and_errors_jp.md) に従ってエラーハンドリングを行います。設定自動生成やスキーマ登録については [1.6 設定ファイル自動生成](../config_loader/06_ensure_config_self_healing_jp.md) を参照してください。

## 3. モデル選択と公開 API

### `LlmClient(model_name_str=None, purpose_str=None, config_dir_path=None)`

| 引数 | 意味 |
| :--- | :--- |
| `model_name_str` | `llm_pool` 配下のプロファイルキー。指定時は用途別選択より優先されます。 |
| `purpose_str` | 未指定時はグローバル `config.llm.default_purpose_str`。`router` の場合は `router_model_str`、それ以外は `sql_generator_model_str` を使用。 |
| `config_dir_path` | インスタンスがプロファイルを読み込む設定ディレクトリ。 |

### `generate(prompt_str="", system_prompt_str=None)`

| 項目 | 動作 |
| :--- | :--- |
| `prompt_str` | ユーザープロンプト文字列 |
| `system_prompt_str` | `None` の場合、グローバル `config.llm.system_prompt_str` を使用。 |
| 戻り値 | 生成された文字列、または結果がない場合は `None` |
| `last_generated_by_str` | 呼び出しごとに初期化。成功時は `external_llm` または `local_llm` |
| `model_config` | 現在のモデルプロファイルを参照する読み取り専用プロパティ |

## 4. 環境変数の優先順位

| 範囲 | 環境変数 | 対応する設定または挙動 |
| :--- | :--- | :--- |
| 共通 | `LLM_PROVIDER` | `provider_str` をオーバーライド |
| 外部共通 | `EXTERNAL_LLM_ENABLED` | `enabled_bool` をオーバーライド (`1`, `true`, `yes`, `on`) |
| 外部共通 | プロファイルの `api_key_env_str` に指定した変数 | 最優先で参照し、未設定時は `EXTERNAL_LLM_API_KEY` を参照 |
| 標準 API | `EXTERNAL_LLM_BASE_URL`, `EXTERNAL_LLM_CHAT_COMPLETIONS_PATH`, `EXTERNAL_LLM_MODEL` | URL、パス、モデル名をオーバーライド |
| 標準 API | `EXTERNAL_LLM_MAX_TOKENS`, `EXTERNAL_LLM_TEMPERATURE`, `EXTERNAL_LLM_TIMEOUT_SECONDS` | 生成オプションおよびタイムアウトをオーバーライド |
| Fabrix | `FABRIX_LLM_ID`, `FABRIX_TIMEOUT_SECONDS` | モデル ID とタイムアウトをオーバーライド |
| ローカル | `LOCAL_LLM_MODEL_PATH` | GGUF ファイルパス |
| ローカル | `LOCAL_LLM_N_CTX`, `LOCAL_LLM_N_THREADS`, `LOCAL_LLM_N_BATCH`, `LOCAL_LLM_N_GPU_LAYERS` | モデル読み込みオプション |
| ローカル | `LOCAL_LLM_MAX_TOKENS`, `LOCAL_LLM_TEMPERATURE` | 生成オプション |
| ローカル | `LOCAL_LLM_VERBOSE` | 詳細ログの有効化フラグ |
