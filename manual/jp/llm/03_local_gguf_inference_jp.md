# 7.3. ローカル GGUF 推論およびモデルキャッシュ

[LLM マニュアル一覧](01_unified_llm_client_jp.md)

> 設定の準備と最小限の呼び出しについては、まず [7.1 モデルプロファイル管理およびテキスト生成](01_model_profiles_and_generation_jp.md) を参照してください。

## 1. ローカル GGUF モデル

```yaml
llm_pool:
  local_text_generator:
    provider_str: local
    model_path_str: llm_models/your-model.gguf
    n_ctx_int: 4096
    n_threads_int: 4
    n_batch_int: 512
    n_gpu_layers_int: 0
    max_tokens_int: 512
    temperature_float: 0.0
    verbose_bool: false
```

このプロファイルを使用するには、`config.yml` の `llm.sql_generator_model_str` を `local_text_generator` に変更します。

`model_path_str` には用意した GGUF ファイルのパスを指定します。相対パスは `ConfigLoader` が決定したプロジェクトルート基準で解決されます。ファイルが存在しない場合、`generate()` は `None` を返します。ファイルが存在するが `llama-cpp-python` がインストールされていない場合は `LlmInferenceError` が送出されます。

モデルは初回の呼び出し時にロードされ、同一モデルパスのインスタンスがプロセス内でキャッシュ・再利用されます。
