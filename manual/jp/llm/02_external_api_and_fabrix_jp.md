# 7.2. 外部チャット API および Fabrix 連携

[LLM マニュアル一覧](01_unified_llm_client_jp.md)

> 設定の準備と最小限の呼び出しについては、まず [7.1 モデルプロファイル管理およびテキスト生成](01_model_profiles_and_generation_jp.md) を参照してください。

## 1. 外部 API: 標準形式と Fabrix

### 標準チャット API

`api_format_str: standard` では、`base_url_str` と `chat_completions_path_str` を結合した URL に対して POST リクエストを送信します。Bearer 認証を使用し、リクエストには `model`, `messages`, `max_tokens`, `temperature` が含まれます。レスポンスは `choices[0].message.content` から抽出します。

### Fabrix 形式

Fabrix を使用する場合は、以下の構造でプロファイルを定義します。URL とモデル ID は利用環境の値に置き換えてください。

```yaml
llm_pool:
  fabrix_text_generator:
    provider_str: external
    enabled_bool: true
    api_format_str: fabrix_api
    api_key_env_str: X_OPENAPI_TOKEN
    base_url_str: https://your-fabrix-endpoint.example/v1/messages
    llm_id_int: 159
    client_env_str: X_GENERATIVE_AI_CLIENT
    user_env_str: X_CLIENT_USER
    timeout_seconds_int: 120
```

`base_url_str` 自体をリクエスト URL として使用します。認証キーは `x-openapi-token` ヘッダーに設定され、`client_env_str` および `user_env_str` で指定された環境変数の値が存在する場合、それぞれ `x-generative-ai-client`, `x-client-user` ヘッダーが付与されます。

リクエストボディには `llmId`, `contents`, `isStream: "False"` を送信し、レスポンスのルート `content` から結果を抽出します。
