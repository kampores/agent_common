# 7.4. 执行模式与条件触发本地切换

[LLM 手册总览](01_unified_llm_client_zh.md)

> 配置准备与基础调用请首先参阅 [7.1 模型配置管理与文本生成](01_model_profiles_and_generation_zh.md)。

## 1. 执行模式与条件回退

通过环境变量 `LLM_PROVIDER` 可强行覆盖配置中的 `provider_str`：

| 模式 | 运行行为 |
| :--- | :--- |
| `external` | 仅执行外部 API 调用。若服务被禁用或未提供 API Key，则安全返回 `None`。 |
| `local` | 仅执行本地 GGUF 模型推理。 |
| `auto` | 外部调用结果若为 `None` 时，自动利用同配置节点下的本地参数尝试回退推理。 |

> ⚠️ **关于 `auto` 模式的重要边界说明**:
> `auto` 并不等同于捕获并吞没一切外部网络故障。若外部 API 抛出底层的 `HTTPError`、`URLError` 或响应结构校验异常，此类异常将如实抛出给上层调用方（Fail-Fast）。只有当外部调用因配置未激活或正常返回空时，才会降级执行本地模型。若需启用 `auto`，必须在**同一个模型配置块**中同时声明外部参数（`base_url_str` 等）与本地参数（`model_path_str`, `n_ctx_int` 等）。
