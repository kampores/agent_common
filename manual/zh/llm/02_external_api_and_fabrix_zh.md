# 7.2. 外部聊天 API 与 Fabrix 平台集成

[LLM 手册总览](01_unified_llm_client_zh.md)

> 配置准备与基础调用请首先参阅 [7.1 模型配置管理与文本生成](01_model_profiles_and_generation_zh.md)。

## 1. 外部 API：标准格式与 Fabrix 格式

### 标准 Chat API

当配置 `api_format_str: standard` 时，底层通过拼接 `base_url_str` 与 `chat_completions_path_str` 发起标准的 HTTP POST 请求。遵循标准 Bearer 鉴权协议，请求体由 `model`、`messages`、`max_tokens`、`temperature` 构成，从返回的 JSON 结构 `choices[0].message.content` 中提取生成的最终文本。

### Fabrix 专有 API 格式

在接入企业内网 Fabrix AI 服务时，按如下格式组织 `config/llmpool.yml` 中的模型配置节点：

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

- **请求路径**: 直接以 `base_url_str` 作为完整的请求目标地址。
- **专有鉴权请求头**: 鉴权 Token 挂载在 `x-openapi-token` 请求头中。若声明了 `client_env_str` 与 `user_env_str`，其环境变量内容将分别装配至 `x-generative-ai-client` 与 `x-client-user` 头字段。
- **请求体与响应解析**: 请求体发送 `llmId`、`contents` 与 `isStream: "False"`，从顶层返回结构中的 `content` 字段提取应答。
