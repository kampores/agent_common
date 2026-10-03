# 7.3. 本地 GGUF 模型推理与模型缓存

[LLM 手册总览](01_unified_llm_client_zh.md)

> 配置准备与基础调用请首先参阅 [7.1 模型配置管理与文本生成](01_model_profiles_and_generation_zh.md)。

## 1. 本地 GGUF 模型运行配置

在断网或敏感数据无法出境的环境中，可配置直接加载本地权重运行：

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

- **生效启用**: 在 `config.yml` 中将对应用途的模型名指定为 `local_text_generator`。
- **路径解析**: `model_path_str` 指向本地 GGUF 权重文件。若填相对路径，则始终自动锚定至当前项目的根目录（依据 `ConfigLoader` 的项目根定位策略），杜绝因工作目录变动导致找不到文件。
- **环境依赖**: 若目标 GGUF 文件不存在，`generate()` 返回 `None`；若文件物理存在但未安装 `llama-cpp-python` 引擎，将抛出 `LlmInferenceError`。
- **单例缓存**: 进程内按文件物理路径自动缓存已加载的模型实例，后续相同路径的请求直接复用内存常驻模型，消除昂贵的模型加载损耗。若调整了 GPU 卸载层数等加载期参数，需重启服务进程生效。
