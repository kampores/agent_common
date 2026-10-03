# 7. 统一 LLM 客户端与推理引擎 (`LlmClient`)

> **所属模块**: `agent_common.llm`  
> **公开 API**: `LlmClient`, `LlmInferenceError`  
> **配置文件**: `config/config.yml`, `config/llmpool.yml`  
> **实现源码**: 仓库中的 `src/agent_common/llm.py`

请根据所需的功能章节查阅对应手册。建议首先了解 7.1 的基础调用，然后再逐步扩展到外部 API、本地模型和异常处理等高阶功能。Groq 监督者 AI 案例参见 7.6。

- **[7.1. 模型配置管理与文本生成](01_model_profiles_and_generation_zh.md)**
- **[7.2. 外部聊天 API 与 Fabrix 平台集成](02_external_api_and_fabrix_zh.md)**
- **[7.3. 本地 GGUF 模型推理与模型缓存](03_local_gguf_inference_zh.md)**
- **[7.4. 执行模式与条件触发本地切换](04_provider_and_local_fallback_zh.md)**
- **[7.5. 推理返回值与异常处理规范](05_inference_results_and_errors_zh.md)**
- **[7.6. Groq 监督者 AI 与 Antigravity Stop 钩子](06_groq_supervisor_and_stop_hook_zh.md)**
