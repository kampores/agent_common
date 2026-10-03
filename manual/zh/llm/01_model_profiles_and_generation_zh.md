# 7.1. 模型配置管理与文本生成

[LLM 手册总览](01_unified_llm_client_zh.md)

## 1. 概述与推荐实现顺序

`LlmClient` 对外部 Chat API 与本地 GGUF 模型提供了统一抽象的 `generate()` 方法调用界面。常用于文本摘要、信息抽取、分类以及 SQL 语句生成等场景。该客户端本身不维护复杂的长多轮对话上下文数据库，也不直接执行生成的 SQL，而是专注于单次交互中系统提示词（System Prompt）与用户提示词（User Prompt）的快速下发与生成。

推荐的接入步骤是：**首先通过单一外部模型跑通提示词输入与文本输出的基础流程**。确认输出格式与业务期望匹配后，再逐步按需引入多模型路由、本地 GGUF 推理以及主备故障自动转移等进阶机制。

---

## 2. 配置准备与最小调用示例

运行环境需具备 Python 3.10+ 及 `agent-common`。调用外部标准 API 采用 Python 原生标准库 `urllib.request`（零第三方网络库依赖，杜绝 CVE 漏洞）。若使用本地 GGUF 推理，需额外安装 `llama-cpp-python` 并准备对应权重的 `.gguf` 物理文件。

首先配置项目的 `config/config.yml` 与 `config/llmpool.yml`。启动时将由 `ConfigLoader` 自动完成多层级 YAML 深度合并。敏感 API 密钥不应直接硬编码在 YAML 文件内，而是通过环境变量注入：

`config/config.yml`:

```yaml
llm:
  default_purpose_str: sql_generator
  sql_generator_model_str: text_generator
  router_model_str: text_generator
  system_prompt_str: 请用清晰简练的中文回答用户请求。

generation_request:
  prompt_str: 请用一句话总结企业数据迁移的核心目标。
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

将 `base_url_str` 与 `model_str` 替换为实际服务地址与模型标识，并在环境变量中配置 `EXTERNAL_LLM_API_KEY`。随后执行最小调用代码：

```python
from agent_common.config_loader import config
from agent_common.llm import LlmClient

llm_client_obj = LlmClient()
response_str = llm_client_obj.generate(
    prompt_str=config.generation_request.prompt_str,
)
print(f"LLM 响应: {response_str}")
```

返回值 `response_str` 为生成的文本字符串（若触发非阻塞过滤时可能为 `None`）。关于配置自愈及 Schema 默认值声明，请查阅 [1.6 全部常量的配置文件化](../config_loader/06_ensure_config_self_healing_zh.md)。

---

## 3. 模型选择与公共 API 规范

### `LlmClient(model_name_str=None, purpose_str=None, config_dir_path=None)`

| 参数项 | 说明与行为 |
| :--- | :--- |
| `model_name_str` | `llm_pool` 中的具体模型配置键名。若显式指定，将覆盖任何业务用途路由规则。请与实际向远端 API 传递的模型名 `model_str` 区分开。 |
| `purpose_str` | 缺省时读取全局 `config.llm.default_purpose_str`。若为 `router` 则使用 `router_model_str`，其余情况默认映射至 `sql_generator_model_str`。 |
| `config_dir_path` | 指定模型配置文件的目录路径，未指定时默认使用项目根目录下的 `config` 文件夹。 |

### `generate(prompt_str="", system_prompt_str=None)`

| 属性/参数 | 行为逻辑 |
| :--- | :--- |
| `prompt_str` | 用户提示词输入字符串。 |
| `system_prompt_str` | 为 `None` 时缺省读取全局 `config.llm.system_prompt_str`。若传空字符串 `""` 则如实下发空系统提示。 |
| 返回值 | 生成的有效响应字符串；在特定跳过或受控降级场景下返回 `None`。 |
| `last_generated_by_str` | 实例属性，记录单次请求的实际处理后端（如 `external_llm` 或 `local_llm`）。 |
| `model_config` | 获取当前生效模型配置的只读字典属性 (`ReadOnlyConfig`)。 |

---

## 4. 环境变量覆盖优先级

| 作用域 | 环境变量 | 生效目标与规则 |
| :--- | :--- | :--- |
| 通用 | `LLM_PROVIDER` | 强制重写当前配置的 `provider_str`（如 `external`, `local`, `auto`）。 |
| 外部通用 | `EXTERNAL_LLM_ENABLED` | 动态覆盖 `enabled_bool`。`1`, `true`, `yes`, `on` 均判定为启用。 |
| 外部通用 | 在配置项 `api_key_env_str` 中声明的自定义变量名 | 优先读取自定义名称；若为空则兜底读取 `EXTERNAL_LLM_API_KEY`。 |
| 标准 API | `EXTERNAL_LLM_BASE_URL`, `EXTERNAL_LLM_CHAT_COMPLETIONS_PATH`, `EXTERNAL_LLM_MODEL` | 动态覆盖服务 Base URL、路径与服务侧模型标识。 |
| 标准 API | `EXTERNAL_LLM_MAX_TOKENS`, `EXTERNAL_LLM_TEMPERATURE`, `EXTERNAL_LLM_TIMEOUT_SECONDS` | 覆盖单次推理生成的最大 Token、采样温度及超时时长。 |
| Fabrix | `FABRIX_LLM_ID`, `FABRIX_TIMEOUT_SECONDS` | 覆盖 Fabrix 专有模型 ID 与网络超时。 |
| 本地推理 | `LOCAL_LLM_MODEL_PATH` | 本地 `.gguf` 权重的相对或绝对物理路径。 |
| 本地推理 | `LOCAL_LLM_N_CTX`, `LOCAL_LLM_N_THREADS`, `LOCAL_LLM_N_BATCH`, `LOCAL_LLM_N_GPU_LAYERS` | 内存上下文大小、CPU 线程并发数、Batch 尺寸及 GPU 显存卸载层数。 |
