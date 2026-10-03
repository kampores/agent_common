# 7.1. Model Profiles and Text Generation

[All LLM manuals](01_unified_llm_client_en.md)

## 1. Start with a single model

`LlmClient` provides one `generate()` interface for external chat APIs and local GGUF inference. It returns text; it does not execute generated SQL or maintain conversation history. Each request contains a system message and a user message.

First implement one prompt and one response with a single model. Verify that behavior before adding purpose-based routing, local inference, or conditional fallback. Apply application-wide type guarantees (README 1.3) and configuration dot notation (1.2) in separate steps as needed.

Python 3.10 or later and `agent-common` are required. External requests use the standard library's `urllib.request`. Local inference additionally requires `llama-cpp-python` and a GGUF file; the package's `all` extra does not install that inference library.

## 2. Minimal configuration and call

Prepare the configuration files before starting the application. `ConfigLoader` merges packaged defaults with project settings. Replace the example endpoint and server model name with your deployment values, and supply the API key through `EXTERNAL_LLM_API_KEY`.

`config/config.yml`:

```yaml
llm:
  default_purpose_str: sql_generator
  sql_generator_model_str: text_generator
  router_model_str: text_generator
  system_prompt_str: Answer briefly.

generation_request:
  prompt_str: Explain the purpose of data migration in one sentence.
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

```python
from agent_common.config_loader import config
from agent_common.llm import LlmClient

llm_client_obj = LlmClient()
response_str = llm_client_obj.generate(
    prompt_str=config.generation_request.prompt_str,
)
```

The caller handles displaying or storing the result, `None`, and exceptions. For entry-point schema registration and automatic configuration creation, see [1.6 Configuration self-healing](../config_loader/06_ensure_config_self_healing_en.md).

## 3. Public API and profile selection

| API | Behavior |
| :--- | :--- |
| `LlmClient(model_name_str=None, purpose_str=None, config_dir_path=None)` | Selects and checks a model profile. Does not connect to the server or load a model at construction time. |
| `model_name_str` | Explicit `llm_pool` profile key; takes precedence over purpose-based selection. Distinct from the server's `model_str`. |
| `purpose_str` | Defaults to global `config.llm.default_purpose_str`. `router` selects `router_model_str`; every other purpose selects `sql_generator_model_str`. |
| `config_dir_path` | Instance profile configuration directory; defaults to the project's `config` directory. |
| `generate(prompt_str="", system_prompt_str=None)` | Returns generated text or `None`. A `None` system prompt uses global `config.llm.system_prompt_str`; an empty string is passed through. |
| `last_generated_by_str` | Reset to `None` on each call; becomes `external_llm` or `local_llm` on success. |
| `model_config` | Read-only view of the selected profile. |

Custom purposes do not automatically resolve new configuration keys. Use an explicit profile for additional purposes. `config_dir_path` changes instance profile lookup, but default purpose, purpose-to-model mapping, and default system prompt still come from global `config.llm`. Pass an explicit model and system prompt when necessary.

## 4. Environment overrides

| Scope | Environment variables |
| :--- | :--- |
| Common | `LLM_PROVIDER` |
| External | `EXTERNAL_LLM_ENABLED`; the variable named by `api_key_env_str`, followed by `EXTERNAL_LLM_API_KEY` if empty/missing |
| Standard API | `EXTERNAL_LLM_BASE_URL`, `EXTERNAL_LLM_CHAT_COMPLETIONS_PATH`, `EXTERNAL_LLM_MODEL`, `EXTERNAL_LLM_MAX_TOKENS`, `EXTERNAL_LLM_TEMPERATURE`, `EXTERNAL_LLM_TIMEOUT_SECONDS` |
| Fabrix | `FABRIX_LLM_ID`, `FABRIX_TIMEOUT_SECONDS`, and variables named by `client_env_str` and `user_env_str` |
| Local | `LOCAL_LLM_MODEL_PATH`, `LOCAL_LLM_N_CTX`, `LOCAL_LLM_N_THREADS`, `LOCAL_LLM_N_BATCH`, `LOCAL_LLM_N_GPU_LAYERS`, `LOCAL_LLM_MAX_TOKENS`, `LOCAL_LLM_TEMPERATURE`, `LOCAL_LLM_VERBOSE` |

External enablement accepts `1`, `true`, `yes`, or `on`, ignoring case. Local verbose mode accepts `true`, ignoring case. Numeric overrides require valid numbers. Standard API URL and generation overrides do not configure the Fabrix request.
