# 7. 統合 LLM クライアントおよび推論エンジン (`LlmClient`)

> **所属モジュール**: `agent_common.llm`  
> **公開 API**: `LlmClient`, `LlmInferenceError`  
> **設定ファイル**: `config/config.yml`, `config/llmpool.yml`  
> **実装基準**: リポジトリの `src/agent_common/llm.py`

必要な機能番号のマニュアルから参照してください。まず 7.1 の最小呼び出しを確認した上で、外部 API、ローカルモデル、例外処理などを段階的に適用してください。Groq 監督官 AI の事例は 7.6 に記載されています。

- **[7.1. モデルプロファイル管理およびテキスト生成](01_model_profiles_and_generation_jp.md)**
- **[7.2. 外部チャット API および Fabrix 連携](02_external_api_and_fabrix_jp.md)**
- **[7.3. ローカル GGUF 推論およびモデルキャッシュ](03_local_gguf_inference_jp.md)**
- **[7.4. 実行モードおよび条件付きローカル切り替え](04_provider_and_local_fallback_jp.md)**
- **[7.5. 推論結果および例外処理](05_inference_results_and_errors_jp.md)**
- **[7.6. Groq 監督官 AI および Antigravity Stop フック](06_groq_supervisor_and_stop_hook_jp.md)**
