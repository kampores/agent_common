# 7.2. External Chat APIs and Fabrix

[All LLM manuals](01_unified_llm_client.md)

> Start with [7.1 Model Profiles and Text Generation](01_model_profiles_and_generation.md) for configuration and the minimal call.

## 1. External API formats

The standard format joins `base_url_str` and `chat_completions_path_str`, uses Bearer authentication, and sends `model`, `messages`, `max_tokens`, and `temperature`. It reads `choices[0].message.content` from the response.

For Fabrix, define a profile such as the following, replacing the endpoint and model ID with values verified for your environment:

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

Fabrix uses `base_url_str` directly and the `x-openapi-token` header. Values from the optional client/user environment variables become `x-generative-ai-client` and `x-client-user` headers. The request contains `llmId`, `contents`, and `isStream: "False"`; the response text comes from top-level `content`.

The current Fabrix implementation does not send token or temperature settings. It prepends the system prompt only when it is nonempty and differs from the global default system prompt.
