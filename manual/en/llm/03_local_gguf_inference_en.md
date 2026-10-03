# 7.3. Local GGUF Inference and Model Caching

[All LLM manuals](01_unified_llm_client_en.md)

> Start with [7.1 Model Profiles and Text Generation](01_model_profiles_and_generation_en.md) for configuration and the minimal call.

## 1. Local GGUF inference

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

Select this profile through `llm.sql_generator_model_str` or an explicit model argument. Relative model paths resolve from the project root determined by `ConfigLoader`, not the configuration directory. A missing file returns `None`. An existing file with no `llama-cpp-python` installation raises `LlmInferenceError`.

`n_ctx_int`, `n_threads_int`, and `n_batch_int` control context size, CPU threads, and prompt processing batch size. Zero GPU layers selects CPU execution; GPU support depends on the installed inference engine and environment.

Models load lazily and are cached by model path within the process. Changing loading options for an already cached path does not reload it. Restart the process to verify changed loading settings.
